from django.conf import settings
from django.db import models


class Notification(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="notifications",
	)
	event = models.CharField(max_length=64)
	title = models.CharField(max_length=200)
	body = models.TextField()
	payload = models.JSONField(default=dict, blank=True)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["user", "is_read"]),
			models.Index(fields=["event"]),
		]

	def __str__(self):
		return f"Notification#{self.pk} {self.event}"


class TelegramLink(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="telegram_link",
	)
	telegram_chat_id = models.CharField(max_length=64, blank=True)
	link_token = models.CharField(max_length=64, unique=True)
	is_active = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	linked_at = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return f"TelegramLink<{self.user_id}> active={self.is_active}"
