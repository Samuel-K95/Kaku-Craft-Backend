from rest_framework import serializers

from .models import Category, Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary"]
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
            "status",
            "is_active",
            "sold_count",
            "social_links",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "sold_count", "created_at", "updated_at"]


class ProductWriteSerializer(serializers.ModelSerializer):
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
            "status",
            "is_active",
            "social_links",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductImageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary"]
        read_only_fields = ["id"]
