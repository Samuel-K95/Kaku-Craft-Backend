from django.contrib import admin

from .models import FAQEntry, SiteContent


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
	list_display = ["key", "section", "title", "is_published", "sort_order", "updated_at"]
	list_filter = ["section", "is_published"]
	search_fields = ["key", "title", "body"]
	prepopulated_fields = {"key": ("title",)}


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
	list_display = ["question", "is_active", "updated_at"]
	list_filter = ["is_active"]
	search_fields = ["question", "answer", "keywords"]
