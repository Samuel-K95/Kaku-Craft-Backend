from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model

from products.permissions import ADMIN_ROLES, IsAdminOrSuperAdmin, IsExpertOrAdmin

from .models import (
	CartItem,
	CustomOrder,
	CustomOrderPaymentProof,
	Order,
	PaymentProof,
)
from .serializers import (
	AddToCartSerializer,
	AdminOrderStatusSerializer,
	AssignExpertSerializer,
	CartItemSerializer,
	CartSerializer,
	CreateOrderSerializer,
	CustomOrderCreateSerializer,
	CustomOrderDecisionSerializer,
	CustomOrderPaymentProofCreateSerializer,
	CustomOrderQuoteSerializer,
	CustomOrderSerializer,
	ExpertStartSerializer,
	OrderSerializer,
	PaymentProofCreateSerializer,
	PaymentProofReviewSerializer,
	PaymentProofSerializer,
	UpdateCartItemSerializer,
)

User = get_user_model()
from .services import (
	apply_payment_proof_decision,
	assert_order_transition,
	complete_order_if_paid,
	get_or_create_cart,
	mark_order_delivered,
)


def _notify_safe(event, **payload):
	try:
		from notifications.services import dispatch_event

		dispatch_event(event, **payload)
	except Exception:
		# Notifications are best-effort; commerce APIs must not fail if missing.
		pass


class CartDetailView(APIView):
	@extend_schema(responses=CartSerializer)
	def get(self, request):
		cart = get_or_create_cart(request.user)
		return Response(CartSerializer(cart).data)


class CartAddItemView(APIView):
	@extend_schema(request=AddToCartSerializer, responses=CartSerializer)
	def post(self, request):
		serializer = AddToCartSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		item = serializer.save()
		cart = get_or_create_cart(request.user)
		return Response(
			{
				"item": CartItemSerializer(item).data,
				"cart": CartSerializer(cart).data,
			},
			status=status.HTTP_201_CREATED,
		)


class CartItemDetailView(APIView):
	@extend_schema(request=UpdateCartItemSerializer, responses=CartSerializer)
	def patch(self, request, item_id):
		cart = get_or_create_cart(request.user)
		item = get_object_or_404(CartItem, pk=item_id, cart=cart)
		serializer = UpdateCartItemSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		item.quantity = serializer.validated_data["quantity"]
		item.save(update_fields=["quantity", "updated_at"])
		return Response(
			{
				"item": CartItemSerializer(item).data,
				"cart": CartSerializer(cart).data,
			}
		)

	@extend_schema(responses=CartSerializer)
	def delete(self, request, item_id):
		cart = get_or_create_cart(request.user)
		item = get_object_or_404(CartItem, pk=item_id, cart=cart)
		item.delete()
		return Response(CartSerializer(cart).data)


class OrderListCreateView(generics.ListCreateAPIView):
	def get_serializer_class(self):
		if self.request.method == "POST":
			return CreateOrderSerializer
		return OrderSerializer

	def get_queryset(self):
		user = self.request.user
		qs = Order.objects.prefetch_related("items", "payment_proofs")
		if getattr(user, "role", None) in ADMIN_ROLES:
			status_filter = self.request.query_params.get("status")
			if status_filter:
				qs = qs.filter(status=status_filter)
			return qs
		return qs.filter(user=user)

	def create(self, request, *args, **kwargs):
		serializer = CreateOrderSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		order = serializer.save()
		_notify_safe("order_placed", user=request.user, order=order)
		return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
	serializer_class = OrderSerializer

	def get_queryset(self):
		user = self.request.user
		qs = Order.objects.prefetch_related("items", "payment_proofs")
		if getattr(user, "role", None) in ADMIN_ROLES:
			return qs
		if getattr(user, "role", None) == "expert":
			return qs.filter(assigned_expert=user)
		return qs.filter(user=user)


class ExpertJobListView(generics.ListAPIView):
	serializer_class = OrderSerializer
	permission_classes = [IsExpertOrAdmin]

	def get_queryset(self):
		user = self.request.user
		qs = Order.objects.prefetch_related("items", "payment_proofs").select_related(
			"assigned_expert"
		)
		if getattr(user, "role", None) in ADMIN_ROLES:
			expert_id = self.request.query_params.get("expert_id")
			if expert_id:
				qs = qs.filter(assigned_expert_id=expert_id)
			return qs.exclude(assigned_expert__isnull=True)
		return qs.filter(assigned_expert=user)


class AssignExpertView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, order_id):
		order = get_object_or_404(Order, pk=order_id)
		serializer = AssignExpertSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		expert = get_object_or_404(User, pk=serializer.validated_data["expert_id"], role="expert")
		order.assigned_expert = expert
		order.save(update_fields=["assigned_expert", "updated_at"])
		return Response(OrderSerializer(order).data)


class ExpertStartView(APIView):
	permission_classes = [IsExpertOrAdmin]

	def post(self, request, order_id):
		order = get_object_or_404(Order, pk=order_id)
		user = request.user
		if getattr(user, "role", None) == "expert" and order.assigned_expert_id != user.id:
			raise PermissionDenied("This job is not assigned to you.")
		serializer = ExpertStartSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		days = serializer.validated_data["days"]
		order.estimated_completion_days = days
		order.expert_started_at = timezone.now()
		order.expert_completed_at = None
		update_fields = [
			"estimated_completion_days",
			"expert_started_at",
			"expert_completed_at",
			"updated_at",
		]
		if order.status in {
			Order.Status.PAYMENT_VERIFIED,
			Order.Status.IN_PROGRESS,
		} or order.has_minimum_deposit:
			if order.status == Order.Status.PAYMENT_VERIFIED:
				assert_order_transition(order, Order.Status.IN_PROGRESS)
				order.status = Order.Status.IN_PROGRESS
				update_fields.append("status")
		order.save(update_fields=list(dict.fromkeys(update_fields)))
		return Response(OrderSerializer(order).data)


class ExpertCompleteView(APIView):
	permission_classes = [IsExpertOrAdmin]

	def post(self, request, order_id):
		order = get_object_or_404(Order, pk=order_id)
		user = request.user
		if getattr(user, "role", None) == "expert" and order.assigned_expert_id != user.id:
			raise PermissionDenied("This job is not assigned to you.")
		if not order.expert_started_at:
			raise ValidationError({"detail": "Start the job before completing it."})
		order.expert_completed_at = timezone.now()
		update_fields = ["expert_completed_at", "updated_at"]
		if order.status == Order.Status.IN_PROGRESS:
			assert_order_transition(order, Order.Status.DELIVERED)
			order.status = Order.Status.DELIVERED
			update_fields.append("status")
			order.save(update_fields=list(dict.fromkeys(update_fields)))
			if order.is_fully_paid:
				complete_order_if_paid(order)
		else:
			order.save(update_fields=update_fields)
		order.refresh_from_db()
		return Response(OrderSerializer(order).data)


class OrderPaymentProofUploadView(APIView):
	parser_classes = [MultiPartParser, FormParser]

	def post(self, request, order_id):
		order = get_object_or_404(Order, pk=order_id)
		if order.user_id != request.user.id and getattr(request.user, "role", None) not in {
			"admin",
			"super_admin",
		}:
			raise PermissionDenied("You can only upload proof for your own orders.")

		if order.status not in {
			Order.Status.PENDING_PAYMENT,
			Order.Status.PAYMENT_SUBMITTED,
			Order.Status.PAYMENT_VERIFIED,
			Order.Status.IN_PROGRESS,
			Order.Status.DELIVERED,
		}:
			raise ValidationError(
				{"status": "Payment proof cannot be uploaded in the current order status."}
			)

		serializer = PaymentProofCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		proof = PaymentProof.objects.create(
			order=order,
			uploaded_by=request.user,
			**serializer.validated_data,
		)

		if order.status == Order.Status.PENDING_PAYMENT:
			assert_order_transition(order, Order.Status.PAYMENT_SUBMITTED)
			order.status = Order.Status.PAYMENT_SUBMITTED
			order.save(update_fields=["status", "updated_at"])

		_notify_safe("payment_proof_uploaded", user=order.user, order=order, proof=proof)
		return Response(PaymentProofSerializer(proof).data, status=status.HTTP_201_CREATED)


class OrderPaymentProofReviewView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, proof_id):
		proof = get_object_or_404(PaymentProof.objects.select_related("order"), pk=proof_id)
		serializer = PaymentProofReviewSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		proof = apply_payment_proof_decision(
			proof,
			approved=serializer.validated_data["approve"],
			reviewer=request.user,
			admin_note=serializer.validated_data.get("admin_note", ""),
		)
		_notify_safe(
			"payment_verified" if serializer.validated_data["approve"] else "payment_rejected",
			user=proof.order.user,
			order=proof.order,
			proof=proof,
		)
		return Response(PaymentProofSerializer(proof).data)


class AdminOrderStatusUpdateView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, order_id):
		order = get_object_or_404(Order, pk=order_id)
		serializer = AdminOrderStatusSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		new_status = serializer.validated_data["status"]

		if new_status == Order.Status.DELIVERED:
			order = mark_order_delivered(order)
		elif new_status == Order.Status.COMPLETED:
			order = complete_order_if_paid(order)
		elif new_status == Order.Status.IN_PROGRESS:
			if not order.has_minimum_deposit:
				raise ValidationError(
					{"amount_paid": "At least 50% deposit must be paid before production."}
				)
			assert_order_transition(order, new_status)
			order.status = new_status
			order.save(update_fields=["status", "updated_at"])
		else:
			assert_order_transition(order, new_status)
			order.status = new_status
			order.save(update_fields=["status", "updated_at"])

		_notify_safe("order_status_updated", user=order.user, order=order)
		return Response(OrderSerializer(order).data)


class CustomOrderListCreateView(generics.ListCreateAPIView):
	parser_classes = [MultiPartParser, FormParser, JSONParser]

	def get_serializer_class(self):
		if self.request.method == "POST":
			return CustomOrderCreateSerializer
		return CustomOrderSerializer

	def get_queryset(self):
		user = self.request.user
		qs = CustomOrder.objects.prefetch_related("payment_proofs")
		if getattr(user, "role", None) in {"admin", "super_admin"}:
			status_filter = self.request.query_params.get("status")
			if status_filter:
				qs = qs.filter(status=status_filter)
			return qs
		return qs.filter(customer=user)

	def perform_create(self, serializer):
		custom_order = serializer.save(customer=self.request.user)
		_notify_safe("custom_order_created", user=self.request.user, custom_order=custom_order)
		try:
			from messaging.services import ensure_conversation_for_custom_order

			ensure_conversation_for_custom_order(custom_order)
		except Exception:
			pass


class CustomOrderDetailView(generics.RetrieveAPIView):
	serializer_class = CustomOrderSerializer

	def get_queryset(self):
		user = self.request.user
		qs = CustomOrder.objects.prefetch_related("payment_proofs")
		if getattr(user, "role", None) in {"admin", "super_admin"}:
			return qs
		return qs.filter(customer=user)


class CustomOrderDecisionView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, pk):
		custom_order = get_object_or_404(CustomOrder, pk=pk)
		if custom_order.status != CustomOrder.Status.PENDING_REVIEW:
			raise ValidationError({"status": "Only pending requests can be approved or rejected."})

		serializer = CustomOrderDecisionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		approve = serializer.validated_data["approve"]
		custom_order.admin_note = serializer.validated_data.get("admin_note", "")

		if approve:
			quoted = serializer.validated_data.get("quoted_price")
			if quoted is None:
				raise ValidationError({"quoted_price": "Quoted price is required when approving."})
			custom_order.quoted_price = quoted
			custom_order.status = CustomOrder.Status.APPROVED
			event = "custom_order_approved"
		else:
			custom_order.status = CustomOrder.Status.REJECTED
			event = "custom_order_rejected"

		custom_order.save()
		_notify_safe(event, user=custom_order.customer, custom_order=custom_order)
		return Response(CustomOrderSerializer(custom_order).data)


class CustomOrderQuoteView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, pk):
		custom_order = get_object_or_404(CustomOrder, pk=pk)
		if custom_order.status not in {
			CustomOrder.Status.PENDING_REVIEW,
			CustomOrder.Status.APPROVED,
		}:
			raise ValidationError({"status": "Cannot set quote in current status."})

		serializer = CustomOrderQuoteSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		custom_order.quoted_price = serializer.validated_data["quoted_price"]
		custom_order.admin_note = serializer.validated_data.get("admin_note", custom_order.admin_note)
		if custom_order.status == CustomOrder.Status.PENDING_REVIEW:
			custom_order.status = CustomOrder.Status.APPROVED
		custom_order.save()
		_notify_safe("custom_order_approved", user=custom_order.customer, custom_order=custom_order)
		return Response(CustomOrderSerializer(custom_order).data)


class CustomOrderConfirmView(APIView):
	def post(self, request, pk):
		custom_order = get_object_or_404(CustomOrder, pk=pk, customer=request.user)
		if custom_order.status != CustomOrder.Status.APPROVED:
			raise ValidationError({"status": "Only approved quotes can be confirmed."})
		if custom_order.quoted_price is None:
			raise ValidationError({"quoted_price": "No quote has been set yet."})

		custom_order.customer_confirmed = True
		custom_order.status = CustomOrder.Status.AWAITING_PAYMENT
		custom_order.save(update_fields=["customer_confirmed", "status", "updated_at"])
		return Response(CustomOrderSerializer(custom_order).data)


class CustomOrderPaymentUploadView(APIView):
	parser_classes = [MultiPartParser, FormParser]

	def post(self, request, pk):
		custom_order = get_object_or_404(CustomOrder, pk=pk, customer=request.user)
		if custom_order.status not in {
			CustomOrder.Status.AWAITING_PAYMENT,
			CustomOrder.Status.PAYMENT_SUBMITTED,
		}:
			raise ValidationError({"status": "Payment cannot be uploaded in the current status."})

		serializer = CustomOrderPaymentProofCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		proof = CustomOrderPaymentProof.objects.create(
			custom_order=custom_order,
			uploaded_by=request.user,
			**serializer.validated_data,
		)
		custom_order.status = CustomOrder.Status.PAYMENT_SUBMITTED
		custom_order.save(update_fields=["status", "updated_at"])
		_notify_safe(
			"custom_payment_proof_uploaded",
			user=request.user,
			custom_order=custom_order,
			proof=proof,
		)
		return Response(CustomOrderSerializer(custom_order).data, status=status.HTTP_201_CREATED)


class CustomOrderPaymentReviewView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, proof_id):
		proof = get_object_or_404(
			CustomOrderPaymentProof.objects.select_related("custom_order"),
			pk=proof_id,
		)
		serializer = PaymentProofReviewSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		if proof.status != CustomOrderPaymentProof.VerificationStatus.PENDING:
			raise ValidationError({"status": "This payment proof was already reviewed."})

		proof.reviewed_by = request.user
		proof.reviewed_at = timezone.now()
		proof.admin_note = serializer.validated_data.get("admin_note", "")
		custom_order = proof.custom_order

		if serializer.validated_data["approve"]:
			proof.status = CustomOrderPaymentProof.VerificationStatus.APPROVED
			custom_order.amount_paid = (custom_order.amount_paid + proof.amount).quantize(
				Decimal("0.01")
			)
			if custom_order.has_minimum_deposit:
				custom_order.status = CustomOrder.Status.IN_PROGRESS
			proof.save()
			custom_order.save()
			_notify_safe(
				"custom_payment_verified",
				user=custom_order.customer,
				custom_order=custom_order,
			)
		else:
			proof.status = CustomOrderPaymentProof.VerificationStatus.REJECTED
			proof.save()
			custom_order.status = CustomOrder.Status.AWAITING_PAYMENT
			custom_order.save(update_fields=["status", "updated_at"])

		return Response(CustomOrderSerializer(custom_order).data)


class CustomOrderStatusUpdateView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, pk):
		custom_order = get_object_or_404(CustomOrder, pk=pk)
		new_status = request.data.get("status")
		allowed = {
			CustomOrder.Status.IN_PROGRESS,
			CustomOrder.Status.COMPLETED,
		}
		if new_status not in allowed:
			raise ValidationError({"status": f"Allowed statuses: {sorted(allowed)}"})
		if new_status == CustomOrder.Status.IN_PROGRESS and not custom_order.has_minimum_deposit:
			raise ValidationError({"amount_paid": "Minimum 50% deposit required."})
		custom_order.status = new_status
		custom_order.save(update_fields=["status", "updated_at"])
		_notify_safe("custom_order_status_updated", user=custom_order.customer, custom_order=custom_order)
		return Response(CustomOrderSerializer(custom_order).data)
