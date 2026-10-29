from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
	model = Message
	extra = 0
	readonly_fields = ["sender", "body", "is_read", "created_at"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
	list_display = ["id", "customer", "order", "custom_order", "is_closed", "updated_at"]
	list_filter = ["is_closed"]
	inlines = [MessageInline]
