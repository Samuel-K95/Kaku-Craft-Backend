from rest_framework import serializers

from .models import Notification, TelegramLink


class NotificationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notification
		fields = ["id", "event", "title", "body", "payload", "is_read", "created_at"]
		read_only_fields = fields


class TelegramLinkSerializer(serializers.ModelSerializer):
	bot_username = serializers.SerializerMethodField()
	deep_link = serializers.SerializerMethodField()

	class Meta:
		model = TelegramLink
		fields = [
			"link_token",
			"telegram_chat_id",
			"is_active",
			"linked_at",
			"bot_username",
			"deep_link",
		]
		read_only_fields = fields

	def get_bot_username(self, obj):
		from django.conf import settings

		return getattr(settings, "TELEGRAM_BOT_USERNAME", "")

	def get_deep_link(self, obj):
		from django.conf import settings

		username = getattr(settings, "TELEGRAM_BOT_USERNAME", "")
		if not username:
			return ""
		return f"https://t.me/{username}?start={obj.link_token}"
