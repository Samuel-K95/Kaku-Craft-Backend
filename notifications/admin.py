from django.contrib import admin

from .models import Notification, TelegramLink


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ["id", "user", "event", "title", "is_read", "created_at"]
	list_filter = ["event", "is_read"]
	search_fields = ["user__email", "title", "body"]


@admin.register(TelegramLink)
class TelegramLinkAdmin(admin.ModelAdmin):
	list_display = ["user", "telegram_chat_id", "is_active", "linked_at"]
	search_fields = ["user__email", "telegram_chat_id", "link_token"]
