from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import CustomOrder, Order
from products.permissions import IsAdminOrSuperAdmin

from .models import Conversation, Message
from .serializers import (
	ConversationCreateSerializer,
	ConversationSerializer,
	MessageCreateSerializer,
	MessageSerializer,
)
from .services import ensure_conversation_for_custom_order, ensure_conversation_for_order


def _user_can_access(user, conversation: Conversation) -> bool:
	if getattr(user, "role", None) in {"admin", "super_admin"}:
		return True
	return conversation.customer_id == user.id


class ConversationListCreateView(APIView):
	def get(self, request):
		qs = Conversation.objects.prefetch_related("messages").select_related(
			"customer", "order", "custom_order"
		)
		if getattr(request.user, "role", None) not in {"admin", "super_admin"}:
			qs = qs.filter(customer=request.user)
		return Response(
			ConversationSerializer(qs, many=True, context={"request": request}).data
		)

	def post(self, request):
		serializer = ConversationCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		user = request.user

		if data.get("order_id"):
			order = get_object_or_404(Order, pk=data["order_id"])
			if order.user_id != user.id and getattr(user, "role", None) not in {
				"admin",
				"super_admin",
			}:
				raise PermissionDenied()
			conversation = ensure_conversation_for_order(order)
		elif data.get("custom_order_id"):
			custom_order = get_object_or_404(CustomOrder, pk=data["custom_order_id"])
			if custom_order.customer_id != user.id and getattr(user, "role", None) not in {
				"admin",
				"super_admin",
			}:
				raise PermissionDenied()
			conversation = ensure_conversation_for_custom_order(custom_order)
		else:
			conversation = Conversation.objects.create(
				customer=user,
				subject=data.get("subject") or "Support",
			)

		body = data.get("body")
		if body:
			Message.objects.create(conversation=conversation, sender=user, body=body)
			conversation.updated_at = timezone.now()
			conversation.save(update_fields=["updated_at"])

		conversation = Conversation.objects.prefetch_related("messages").get(pk=conversation.pk)
		return Response(
			ConversationSerializer(conversation, context={"request": request}).data,
			status=status.HTTP_201_CREATED,
		)


class ConversationDetailView(APIView):
	def get(self, request, pk):
		conversation = get_object_or_404(
			Conversation.objects.prefetch_related("messages"),
			pk=pk,
		)
		if not _user_can_access(request.user, conversation):
			raise PermissionDenied()
		return Response(
			ConversationSerializer(conversation, context={"request": request}).data
		)


class ConversationMessagesView(APIView):
	def get(self, request, pk):
		conversation = get_object_or_404(Conversation, pk=pk)
		if not _user_can_access(request.user, conversation):
			raise PermissionDenied()
		messages = conversation.messages.select_related("sender")
		return Response(MessageSerializer(messages, many=True).data)

	def post(self, request, pk):
		conversation = get_object_or_404(Conversation, pk=pk)
		if not _user_can_access(request.user, conversation):
			raise PermissionDenied()
		if conversation.is_closed:
			raise ValidationError({"conversation": "This conversation is closed."})

		serializer = MessageCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		message = Message.objects.create(
			conversation=conversation,
			sender=request.user,
			body=serializer.validated_data["body"],
		)
		conversation.updated_at = timezone.now()
		conversation.save(update_fields=["updated_at"])

		try:
			from notifications.services import dispatch_event

			recipient = conversation.customer
			if request.user.id == conversation.customer_id:
				# Notify admins via broadcast event; customer already knows.
				recipient = None
			dispatch_event(
				"new_message",
				user=recipient or conversation.customer,
				conversation=conversation,
				message=message,
			)
		except Exception:
			pass

		return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class ConversationMarkReadView(APIView):
	def post(self, request, pk):
		conversation = get_object_or_404(Conversation, pk=pk)
		if not _user_can_access(request.user, conversation):
			raise PermissionDenied()
		updated = (
			conversation.messages.exclude(sender=request.user)
			.filter(is_read=False)
			.update(is_read=True)
		)
		return Response({"marked_read": updated})


class ConversationCloseView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, pk):
		conversation = get_object_or_404(Conversation, pk=pk)
		conversation.is_closed = True
		conversation.save(update_fields=["is_closed", "updated_at"])
		return Response(
			ConversationSerializer(conversation, context={"request": request}).data
		)
