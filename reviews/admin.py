from django.contrib import admin

from .models import Review, WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
	list_display = ["id", "user", "product", "created_at"]
	search_fields = ["user__email", "product__name"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ["id", "product", "user", "rating", "is_approved", "is_flagged", "created_at"]
	list_filter = ["is_approved", "is_flagged", "rating"]
	search_fields = ["user__email", "product__name", "comment"]
