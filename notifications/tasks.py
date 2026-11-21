import logging

logger = logging.getLogger(__name__)


def _run_send(user_id=None, event="", title="", body="", payload=None):
	from .models import TelegramLink
	from .services import send_telegram_message

	if not user_id:
		return {"sent": False, "reason": "no_user"}

	link = (
		TelegramLink.objects.filter(user_id=user_id, is_active=True)
		.exclude(telegram_chat_id="")
		.first()
	)
	if not link:
		return {"sent": False, "reason": "not_linked"}

	text = f"{title}\n{body}".strip()
	ok = send_telegram_message(link.telegram_chat_id, text)
	return {"sent": ok, "event": event, "payload": payload or {}}


def _run_email_send(user_id=None, event="", title="", body="", payload=None):
	from django.contrib.auth import get_user_model
	from django.core.mail import send_mail

	if not user_id:
		return {"sent": False, "reason": "no_user"}

	User = get_user_model()
	user = User.objects.filter(pk=user_id).first()
	if not user or not user.email:
		return {"sent": False, "reason": "no_email"}

	try:
		subject = f"[Kaku Craft] {title}"
		message = (
			f"Hello {user.full_name or 'Valued Customer'},\n\n"
			f"{body}\n\n"
			f"---\n"
			f"Kaku Craft Studio • Addis Ababa, Ethiopia\n"
			f"Artisan Handmade Crochet & Bespoke Orders"
		)
		sent_count = send_mail(
			subject=subject,
			message=message,
			from_email=None,
			recipient_list=[user.email],
			fail_silently=False,
		)
		return {"sent": sent_count > 0, "event": event, "recipient": user.email}
	except Exception as exc:
		logger.warning("Email dispatch failed for user #%s: %s", user_id, exc)
		return {"sent": False, "reason": str(exc)}



try:
	from celery import shared_task

	@shared_task(name="notifications.send_telegram_notification")
	def send_telegram_notification(user_id=None, event="", title="", body="", payload=None):
		return _run_send(user_id, event, title, body, payload)

	@shared_task(name="notifications.send_email_notification")
	def send_email_notification(user_id=None, event="", title="", body="", payload=None):
		return _run_email_send(user_id, event, title, body, payload)

	send_telegram_notification.run = send_telegram_notification  # type: ignore[attr-defined]
	send_email_notification.run = send_email_notification  # type: ignore[attr-defined]

except Exception:  # Celery not installed — sync fallback
	class _SyncTask:
		@staticmethod
		def delay(**kwargs):
			return _run_send(**kwargs)

		@staticmethod
		def __call__(**kwargs):
			return _run_send(**kwargs)

	send_telegram_notification = _SyncTask()
