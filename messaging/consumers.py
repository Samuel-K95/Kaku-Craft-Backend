import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
		self.group_name = f"chat_{self.conversation_id}"
		user = self.scope.get("user")

		if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
			await self.close()
			return

		allowed = await self._can_access(user.id, int(self.conversation_id))
		if not allowed:
			await self.close()
			return

		await self.channel_layer.group_add(self.group_name, self.channel_name)
		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(self.group_name, self.channel_name)

	async def receive(self, text_data=None, bytes_data=None):
		user = self.scope.get("user")
		if not user or not user.is_authenticated:
			return

		try:
			payload = json.loads(text_data or "{}")
		except json.JSONDecodeError:
			await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
			return

		body = (payload.get("body") or "").strip()
		if not body:
			await self.send(text_data=json.dumps({"error": "body is required"}))
			return

		message = await self._create_message(user.id, int(self.conversation_id), body)
		event = {
			"type": "chat.message",
			"message": message,
		}
		await self.channel_layer.group_send(self.group_name, event)

	async def chat_message(self, event):
		await self.send(text_data=json.dumps(event["message"]))

	@database_sync_to_async
	def _can_access(self, user_id, conversation_id):
		from django.contrib.auth import get_user_model

		User = get_user_model()
		try:
			user = User.objects.get(pk=user_id)
			conversation = Conversation.objects.get(pk=conversation_id)
		except (User.DoesNotExist, Conversation.DoesNotExist):
			return False
		if getattr(user, "role", None) in {"admin", "super_admin"}:
			return True
		return conversation.customer_id == user_id

	@database_sync_to_async
	def _create_message(self, user_id, conversation_id, body):
		from django.contrib.auth import get_user_model
		from django.utils import timezone

		User = get_user_model()
		user = User.objects.get(pk=user_id)
		conversation = Conversation.objects.get(pk=conversation_id)
		message = Message.objects.create(conversation=conversation, sender=user, body=body)
		conversation.updated_at = timezone.now()
		conversation.save(update_fields=["updated_at"])
		return {
			"id": message.id,
			"conversation_id": conversation_id,
			"sender_id": user_id,
			"sender_email": user.email,
			"body": message.body,
			"created_at": message.created_at.isoformat(),
		}
