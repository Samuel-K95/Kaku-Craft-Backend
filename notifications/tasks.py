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


try:
	from celery import shared_task

	@shared_task(name="notifications.send_telegram_notification")
	def send_telegram_notification(user_id=None, event="", title="", body="", payload=None):
		return _run_send(user_id, event, title, body, payload)

	# Allow `.delay(...)` compatibility helpers.
	send_telegram_notification.run = send_telegram_notification  # type: ignore[attr-defined]

except Exception:  # Celery not installed — sync fallback
	class _SyncTask:
		@staticmethod
		def delay(**kwargs):
			return _run_send(**kwargs)

		@staticmethod
		def __call__(**kwargs):
			return _run_send(**kwargs)

	send_telegram_notification = _SyncTask()
