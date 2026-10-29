from rest_framework import serializers

from orders.models import Order, OrderItem
from products.models import Product
from products.serializers import ProductSerializer

from .models import Review, WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
	product_detail = ProductSerializer(source="product", read_only=True)

	class Meta:
		model = WishlistItem
		fields = ["id", "product", "product_detail", "created_at"]
		read_only_fields = ["id", "created_at"]


class WishlistAddSerializer(serializers.Serializer):
	product_id = serializers.IntegerField()

	def validate_product_id(self, value):
		if not Product.objects.filter(
			pk=value, is_active=True, status=Product.ProductStatus.ACTIVE
		).exists():
			raise serializers.ValidationError("Product not found or unavailable.")
		return value


class ReviewSerializer(serializers.ModelSerializer):
	user_email = serializers.EmailField(source="user.email", read_only=True)
	product_name = serializers.CharField(source="product.name", read_only=True)

	class Meta:
		model = Review
		fields = [
			"id",
			"product",
			"product_name",
			"order",
			"user_email",
			"rating",
			"comment",
			"is_approved",
			"is_flagged",
			"created_at",
			"updated_at",
		]
		read_only_fields = [
			"id",
			"is_approved",
			"is_flagged",
			"created_at",
			"updated_at",
			"user_email",
			"product_name",
		]


class ReviewCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = Review
		fields = ["product", "order", "rating", "comment"]

	def validate(self, attrs):
		user = self.context["request"].user
		order = attrs["order"]
		product = attrs["product"]

		if order.user_id != user.id:
			raise serializers.ValidationError({"order": "You can only review your own orders."})
		if order.status != Order.Status.COMPLETED:
			raise serializers.ValidationError(
				{"order": "Reviews are only allowed for completed orders."}
			)
		if not OrderItem.objects.filter(order=order, product=product).exists():
			raise serializers.ValidationError(
				{"product": "This product was not part of the selected order."}
			)
		if Review.objects.filter(user=user, product=product, order=order).exists():
			raise serializers.ValidationError(
				{"non_field_errors": ["You already reviewed this product for this order."]}
			)
		return attrs


class ReviewModerationSerializer(serializers.Serializer):
	is_approved = serializers.BooleanField(required=False)
	is_flagged = serializers.BooleanField(required=False)
