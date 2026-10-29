from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
	sender_email = serializers.EmailField(source="sender.email", read_only=True)
	sender_role = serializers.CharField(source="sender.role", read_only=True)

	class Meta:
		model = Message
		fields = ["id", "sender", "sender_email", "sender_role", "body", "is_read", "created_at"]
		read_only_fields = ["id", "sender", "is_read", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
	messages = MessageSerializer(many=True, read_only=True)
	unread_count = serializers.SerializerMethodField()

	class Meta:
		model = Conversation
		fields = [
			"id",
			"customer",
			"order",
			"custom_order",
			"subject",
			"is_closed",
			"messages",
			"unread_count",
			"created_at",
			"updated_at",
		]
		read_only_fields = fields

	def get_unread_count(self, obj):
		user = self.context["request"].user
		return obj.messages.exclude(sender=user).filter(is_read=False).count()


class ConversationCreateSerializer(serializers.Serializer):
	order_id = serializers.IntegerField(required=False)
	custom_order_id = serializers.IntegerField(required=False)
	subject = serializers.CharField(required=False, allow_blank=True, max_length=200)
	body = serializers.CharField(required=False, allow_blank=True)

	def validate(self, attrs):
		if not attrs.get("order_id") and not attrs.get("custom_order_id"):
			# Support general support threads with no linked order.
			return attrs
		if attrs.get("order_id") and attrs.get("custom_order_id"):
			raise serializers.ValidationError("Provide either order_id or custom_order_id, not both.")
		return attrs


class MessageCreateSerializer(serializers.Serializer):
	body = serializers.CharField()
