from django.contrib import admin

from .models import (
	Cart,
	CartItem,
	CustomOrder,
	CustomOrderPaymentProof,
	Order,
	OrderItem,
	PaymentProof,
)


class CartItemInline(admin.TabularInline):
	model = CartItem
	extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
	list_display = ["id", "user", "updated_at"]
	inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ["product_name", "unit_price", "quantity", "line_total"]


class PaymentProofInline(admin.TabularInline):
	model = PaymentProof
	extra = 0
	readonly_fields = ["uploaded_by", "amount", "kind", "status", "created_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ["id", "user", "status", "total_price", "amount_paid", "created_at"]
	list_filter = ["status"]
	search_fields = ["user__email", "id"]
	inlines = [OrderItemInline, PaymentProofInline]


@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
	list_display = ["id", "order", "amount", "kind", "status", "created_at"]
	list_filter = ["status", "kind"]


class CustomPaymentInline(admin.TabularInline):
	model = CustomOrderPaymentProof
	extra = 0


@admin.register(CustomOrder)
class CustomOrderAdmin(admin.ModelAdmin):
	list_display = ["id", "customer", "status", "quoted_price", "amount_paid", "created_at"]
	list_filter = ["status"]
	search_fields = ["customer__email", "description"]
	inlines = [CustomPaymentInline]
