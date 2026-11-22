from django.contrib import admin

from .models import Category, Product, ProductImage, ProductSizeVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "is_active", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("name", "slug")
	prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
	model = ProductImage
	extra = 1


class ProductSizeVariantInline(admin.TabularInline):
	model = ProductSizeVariant
	extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = (
		"name",
		"category",
		"price",
		"stock_quantity",
		"production_days",
		"status",
		"is_active",
		"sold_count",
		"created_at",
	)
	list_filter = ("status", "is_active", "category")
	search_fields = ("name", "slug", "description", "source_key")
	prepopulated_fields = {"slug": ("name",)}
	inlines = [ProductSizeVariantInline, ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
	list_display = ("product", "is_primary", "created_at")
	list_filter = ("is_primary",)


@admin.register(ProductSizeVariant)
class ProductSizeVariantAdmin(admin.ModelAdmin):
	list_display = ("product", "size", "stock_quantity")
	list_filter = ("size",)
