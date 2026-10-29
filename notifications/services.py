import logging
import secrets

from django.conf import settings
from django.utils import timezone

from .models import Notification, TelegramLink

logger = logging.getLogger(__name__)


EVENT_TEMPLATES = {
	"order_placed": ("Order placed", "Your order #{order_id} was placed successfully."),
	"payment_proof_uploaded": ("Payment proof uploaded", "Payment proof received for order #{order_id}."),
	"payment_verified": ("Payment verified", "Payment for order #{order_id} was verified."),
	"payment_rejected": ("Payment rejected", "Payment proof for order #{order_id} was rejected."),
	"order_status_updated": ("Order updated", "Order #{order_id} status is now {status}."),
	"custom_order_created": ("Custom order submitted", "Your custom order #{custom_order_id} was submitted."),
	"custom_order_approved": ("Custom order approved", "Custom order #{custom_order_id} was approved."),
	"custom_order_rejected": ("Custom order rejected", "Custom order #{custom_order_id} was rejected."),
	"custom_payment_proof_uploaded": (
		"Custom payment uploaded",
		"Payment proof uploaded for custom order #{custom_order_id}.",
	),
	"custom_payment_verified": (
		"Custom payment verified",
		"Payment verified for custom order #{custom_order_id}.",
	),
	"custom_order_status_updated": (
		"Custom order updated",
		"Custom order #{custom_order_id} status is now {status}.",
	),
	"new_message": ("New message", "You have a new message in conversation #{conversation_id}."),
}


def _payload_from_kwargs(**kwargs):
	payload = {}
	order = kwargs.get("order")
	if order is not None:
		payload["order_id"] = order.pk
		payload["status"] = getattr(order, "status", None)
	custom_order = kwargs.get("custom_order")
	if custom_order is not None:
		payload["custom_order_id"] = custom_order.pk
		payload["status"] = getattr(custom_order, "status", payload.get("status"))
	conversation = kwargs.get("conversation")
	if conversation is not None:
		payload["conversation_id"] = conversation.pk
	return payload


def create_notification(user, event, **kwargs):
	if user is None:
		return None
	title_template, body_template = EVENT_TEMPLATES.get(
		event, (event.replace("_", " ").title(), event)
	)
	payload = _payload_from_kwargs(**kwargs)
	context = {**payload}
	title = title_template.format(**context) if "{" in title_template else title_template
	try:
		body = body_template.format(**context)
	except KeyError:
		body = body_template

	notification = Notification.objects.create(
		user=user,
		event=event,
		title=title,
		body=body,
		payload=payload,
	)
	return notification


def dispatch_event(event, **kwargs):
	"""Create in-app notification and enqueue Telegram delivery."""
	user = kwargs.pop("user", None)
	notification = create_notification(user, event, **kwargs) if user else None

	try:
		from .tasks import send_telegram_notification

		send_telegram_notification.delay(
			user_id=getattr(user, "id", None),
			event=event,
			title=getattr(notification, "title", event),
			body=getattr(notification, "body", ""),
			payload=_payload_from_kwargs(**kwargs),
		)
	except Exception as exc:
		logger.debug("Telegram dispatch skipped: %s", exc)

	return notification


def ensure_telegram_link(user):
	link, created = TelegramLink.objects.get_or_create(
		user=user,
		defaults={"link_token": secrets.token_urlsafe(24)},
	)
	if not created and not link.link_token:
		link.link_token = secrets.token_urlsafe(24)
		link.save(update_fields=["link_token"])
	return link


def activate_telegram_link(token, chat_id):
	link = TelegramLink.objects.filter(link_token=token).select_related("user").first()
	if not link:
		return None
	link.telegram_chat_id = str(chat_id)
	link.is_active = True
	link.linked_at = timezone.now()
	link.save(update_fields=["telegram_chat_id", "is_active", "linked_at"])
	return link


def send_telegram_message(chat_id, text):
	token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
	if not token or not chat_id:
		logger.info("Telegram skipped (missing token/chat_id): %s", text[:120])
		return False

	try:
		import urllib.parse
		import urllib.request

		url = f"https://api.telegram.org/bot{token}/sendMessage"
		data = urllib.parse.urlencode(
			{"chat_id": chat_id, "text": text}
		).encode("utf-8")
		req = urllib.request.Request(url, data=data, method="POST")
		with urllib.request.urlopen(req, timeout=10) as resp:
			return 200 <= resp.status < 300
	except Exception as exc:
		logger.warning("Telegram send failed: %s", exc)
		return False
