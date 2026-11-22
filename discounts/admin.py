from django.contrib import admin

from .models import Discount


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "discount_type", "value", "is_active", "starts_at", "ends_at"]
    list_filter = ["discount_type", "is_active", "applies_to_all"]
    search_fields = ["code", "name"]
    filter_horizontal = ["products"]
