from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer, TelegramLinkSerializer
from .services import activate_telegram_link, ensure_telegram_link


class NotificationListView(APIView):
	def get(self, request):
		qs = Notification.objects.filter(user=request.user)
		unread_only = request.query_params.get("unread")
		if unread_only in {"1", "true", "True"}:
			qs = qs.filter(is_read=False)
		return Response(NotificationSerializer(qs[:100], many=True).data)


class NotificationMarkReadView(APIView):
	def post(self, request, pk):
		notification = get_object_or_404(Notification, pk=pk, user=request.user)
		notification.is_read = True
		notification.save(update_fields=["is_read"])
		return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
	def post(self, request):
		updated = Notification.objects.filter(user=request.user, is_read=False).update(
			is_read=True
		)
		return Response({"marked_read": updated})


class TelegramLinkView(APIView):
	def get(self, request):
		link = ensure_telegram_link(request.user)
		return Response(TelegramLinkSerializer(link).data)

	def delete(self, request):
		link = ensure_telegram_link(request.user)
		link.is_active = False
		link.telegram_chat_id = ""
		link.save(update_fields=["is_active", "telegram_chat_id"])
		return Response(TelegramLinkSerializer(link).data)


class TelegramWebhookView(APIView):
	"""Optional webhook endpoint for /start <token> deep-link activation."""

	permission_classes = [AllowAny]
	authentication_classes = []

	def post(self, request):
		from django.conf import settings as dj_settings

		secret = getattr(dj_settings, "TELEGRAM_WEBHOOK_SECRET", "") or ""
		provided = (
			request.headers.get("X-Telegram-Bot-Api-Secret-Token")
			or request.META.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN")
			or ""
		)
		if secret:
			if provided != secret:
				return Response(
					{"ok": False, "detail": "invalid webhook secret"},
					status=status.HTTP_403_FORBIDDEN,
				)
		elif not getattr(dj_settings, "DEBUG", False):
			return Response(
				{"ok": False, "detail": "webhook secret not configured"},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		message = request.data.get("message") or {}
		chat = message.get("chat") or {}
		text = (message.get("text") or "").strip()
		chat_id = chat.get("id")
		if not text.startswith("/start") or not chat_id:
			return Response({"ok": True})

		parts = text.split(maxsplit=1)
		token = parts[1].strip() if len(parts) > 1 else ""
		if not token:
			return Response({"ok": True, "detail": "missing token"})

		link = activate_telegram_link(token, chat_id)
		if not link:
			return Response({"ok": False, "detail": "invalid token"}, status=status.HTTP_400_BAD_REQUEST)
		return Response({"ok": True, "linked_user": link.user_id})
