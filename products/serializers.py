from rest_framework import serializers

from .models import Category, Product, ProductImage, ProductSizeVariant


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary"]
        read_only_fields = ["id"]


class ProductSizeVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSizeVariant
        fields = ["id", "size", "stock_quantity"]
        read_only_fields = ["id"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    size_variants = ProductSizeVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_name",
            "category_slug",
            "name",
            "slug",
            "description",
            "price",
            "size",
            "stock_quantity",
            "production_days",
            "source_key",
            "status",
            "is_active",
            "sold_count",
            "social_links",
            "images",
            "size_variants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "sold_count", "created_at", "updated_at"]


class ProductWriteSerializer(serializers.ModelSerializer):
    size_variants = ProductSizeVariantSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "slug",
            "description",
            "price",
            "size",
            "stock_quantity",
            "production_days",
            "source_key",
            "status",
            "is_active",
            "social_links",
            "size_variants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def _sync_variants(self, product, variants_data):
        if variants_data is None:
            return
        seen = set()
        for item in variants_data:
            size = item["size"]
            stock = item.get("stock_quantity", 0)
            variant, _ = ProductSizeVariant.objects.update_or_create(
                product=product,
                size=size,
                defaults={"stock_quantity": stock},
            )
            seen.add(variant.pk)
        ProductSizeVariant.objects.filter(product=product).exclude(pk__in=seen).delete()
        total = sum(
            ProductSizeVariant.objects.filter(product=product).values_list(
                "stock_quantity", flat=True
            )
        )
        product.stock_quantity = total
        product.save(update_fields=["stock_quantity", "status", "updated_at"])

    def create(self, validated_data):
        variants_data = validated_data.pop("size_variants", None)
        product = super().create(validated_data)
        if variants_data is not None:
            self._sync_variants(product, variants_data)
        return product

    def update(self, instance, validated_data):
        variants_data = validated_data.pop("size_variants", None)
        product = super().update(instance, validated_data)
        if variants_data is not None:
            self._sync_variants(product, variants_data)
        return product


class ProductImageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary"]
        read_only_fields = ["id"]
