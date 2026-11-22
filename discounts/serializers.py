from rest_framework import serializers

from products.models import Product

from .models import Discount


class DiscountSerializer(serializers.ModelSerializer):
    product_ids = serializers.PrimaryKeyRelatedField(
        source="products",
        many=True,
        queryset=Product.objects.all(),
        required=False,
    )

    class Meta:
        model = Discount
        fields = [
            "id",
            "name",
            "code",
            "discount_type",
            "value",
            "applies_to_all",
            "product_ids",
            "starts_at",
            "ends_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        discount_type = attrs.get("discount_type", getattr(self.instance, "discount_type", None))
        value = attrs.get("value", getattr(self.instance, "value", None))
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if discount_type == Discount.DiscountType.PERCENT and value is not None and value > 100:
            raise serializers.ValidationError({"value": "Percent cannot exceed 100."})
        if starts_at and ends_at and ends_at < starts_at:
            raise serializers.ValidationError({"ends_at": "End must be after start."})
        return attrs


class DiscountValidateSerializer(serializers.Serializer):
    code = serializers.CharField()
    product_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
