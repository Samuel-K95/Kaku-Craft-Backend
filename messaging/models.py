from django.conf import settings
from django.db import models

from orders.models import CustomOrder, Order


class Conversation(models.Model):
	customer = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="conversations",
	)
	order = models.ForeignKey(
		Order,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name="conversations",
	)
	custom_order = models.ForeignKey(
		CustomOrder,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name="conversations",
	)
	subject = models.CharField(max_length=200, blank=True)
	is_closed = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-updated_at"]
		constraints = [
			models.CheckConstraint(
				condition=(
					models.Q(order__isnull=False, custom_order__isnull=True)
					| models.Q(order__isnull=True, custom_order__isnull=False)
					| models.Q(order__isnull=True, custom_order__isnull=True)
				),
				name="conversation_single_or_no_order_link",
			),
		]

	def __str__(self):
		return f"Conversation#{self.pk}"


class Message(models.Model):
	conversation = models.ForeignKey(
		Conversation,
		on_delete=models.CASCADE,
		related_name="messages",
	)
	sender = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="sent_messages",
	)
	body = models.TextField()
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["created_at"]

	def __str__(self):
		return f"Message#{self.pk} conv={self.conversation_id}"
