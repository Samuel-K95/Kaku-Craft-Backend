from decimal import Decimal

from rest_framework import serializers

from .models import (
	Cart,
	CartItem,
	CustomOrder,
	CustomOrderPaymentProof,
	Order,
	OrderItem,
	PaymentProof,
)
from .services import add_to_cart, create_order_from_cart


class CartItemSerializer(serializers.ModelSerializer):
	product_name = serializers.CharField(source="product.name", read_only=True)
	product_slug = serializers.CharField(source="product.slug", read_only=True)
	unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
	subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

	class Meta:
		model = CartItem
		fields = [
			"id",
			"product",
			"product_name",
			"product_slug",
			"quantity",
			"unit_price",
			"subtotal",
			"created_at",
			"updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
	items = CartItemSerializer(many=True, read_only=True)
	total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
	item_count = serializers.IntegerField(read_only=True)

	class Meta:
		model = Cart
		fields = ["id", "items", "total_price", "item_count", "updated_at"]
		read_only_fields = fields


class AddToCartSerializer(serializers.Serializer):
	product_id = serializers.IntegerField()
	quantity = serializers.IntegerField(min_value=1, default=1)

	def create(self, validated_data):
		user = self.context["request"].user
		return add_to_cart(
			user,
			validated_data["product_id"],
			validated_data.get("quantity", 1),
		)


class UpdateCartItemSerializer(serializers.Serializer):
	quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
	class Meta:
		model = OrderItem
		fields = [
			"id",
			"product",
			"product_name",
			"unit_price",
			"quantity",
			"line_total",
		]
		read_only_fields = fields


class PaymentProofSerializer(serializers.ModelSerializer):
	class Meta:
		model = PaymentProof
		fields = [
			"id",
			"order",
			"image",
			"amount",
			"kind",
			"status",
			"admin_note",
			"reviewed_at",
			"created_at",
		]
		read_only_fields = [
			"id",
			"order",
			"status",
			"admin_note",
			"reviewed_at",
			"created_at",
		]


class PaymentProofCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = PaymentProof
		fields = ["image", "amount", "kind"]

	def validate_amount(self, value):
		if value <= 0:
			raise serializers.ValidationError("Amount must be greater than zero.")
		return value


class PaymentProofReviewSerializer(serializers.Serializer):
	approve = serializers.BooleanField()
	admin_note = serializers.CharField(required=False, allow_blank=True, default="")


class OrderSerializer(serializers.ModelSerializer):
	items = OrderItemSerializer(many=True, read_only=True)
	payment_proofs = PaymentProofSerializer(many=True, read_only=True)
	remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
	deposit_required = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
	has_minimum_deposit = serializers.BooleanField(read_only=True)
	is_fully_paid = serializers.BooleanField(read_only=True)
	production_status = serializers.CharField(read_only=True)
	assigned_expert_name = serializers.CharField(
		source="assigned_expert.full_name", read_only=True, allow_null=True
	)

	class Meta:
		model = Order
		fields = [
			"id",
			"status",
			"total_price",
			"amount_paid",
			"remaining_amount",
			"deposit_required",
			"has_minimum_deposit",
			"is_fully_paid",
			"shipping_address",
			"notes",
			"items",
			"payment_proofs",
			"assigned_expert",
			"assigned_expert_name",
			"estimated_completion_days",
			"expert_started_at",
			"expert_completed_at",
			"production_status",
			"created_at",
			"updated_at",
		]
		read_only_fields = [
			"id",
			"status",
			"total_price",
			"amount_paid",
			"assigned_expert_name",
			"production_status",
			"created_at",
			"updated_at",
		]


class AssignExpertSerializer(serializers.Serializer):
	expert_id = serializers.IntegerField()


class ExpertStartSerializer(serializers.Serializer):
	days = serializers.IntegerField(min_value=1, max_value=365)


class CreateOrderSerializer(serializers.Serializer):
	shipping_address = serializers.CharField(required=False, allow_blank=True, default="")
	notes = serializers.CharField(required=False, allow_blank=True, default="")
	discount_code = serializers.CharField(required=False, allow_blank=True, default="")

	def create(self, validated_data):
		return create_order_from_cart(
			self.context["request"].user,
			shipping_address=validated_data.get("shipping_address", ""),
			notes=validated_data.get("notes", ""),
			discount_code=validated_data.get("discount_code", ""),
		)


class AdminOrderStatusSerializer(serializers.Serializer):
	status = serializers.ChoiceField(choices=Order.Status.choices)
	admin_note = serializers.CharField(required=False, allow_blank=True, default="")


class CustomOrderPaymentProofSerializer(serializers.ModelSerializer):
	class Meta:
		model = CustomOrderPaymentProof
		fields = [
			"id",
			"image",
			"amount",
			"status",
			"admin_note",
			"reviewed_at",
			"created_at",
		]
		read_only_fields = fields


class CustomOrderSerializer(serializers.ModelSerializer):
	payment_proofs = CustomOrderPaymentProofSerializer(many=True, read_only=True)
	remaining_amount = serializers.DecimalField(
		max_digits=12, decimal_places=2, read_only=True, allow_null=True
	)
	deposit_required = serializers.DecimalField(
		max_digits=12, decimal_places=2, read_only=True, allow_null=True
	)
	has_minimum_deposit = serializers.BooleanField(read_only=True)

	class Meta:
		model = CustomOrder
		fields = [
			"id",
			"reference_image",
			"description",
			"quoted_price",
			"amount_paid",
			"remaining_amount",
			"deposit_required",
			"has_minimum_deposit",
			"status",
			"admin_note",
			"customer_confirmed",
			"payment_proofs",
			"created_at",
			"updated_at",
		]
		read_only_fields = [
			"id",
			"quoted_price",
			"amount_paid",
			"status",
			"admin_note",
			"customer_confirmed",
			"created_at",
			"updated_at",
		]


class CustomOrderCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = CustomOrder
		fields = ["reference_image", "description"]


class CustomOrderQuoteSerializer(serializers.Serializer):
	quoted_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
	admin_note = serializers.CharField(required=False, allow_blank=True, default="")


class CustomOrderDecisionSerializer(serializers.Serializer):
	approve = serializers.BooleanField()
	quoted_price = serializers.DecimalField(
		max_digits=12,
		decimal_places=2,
		min_value=Decimal("0.01"),
		required=False,
	)
	admin_note = serializers.CharField(required=False, allow_blank=True, default="")


class CustomOrderPaymentProofCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = CustomOrderPaymentProof
		fields = ["image", "amount"]

	def validate_amount(self, value):
		if value <= 0:
			raise serializers.ValidationError("Amount must be greater than zero.")
		return value
