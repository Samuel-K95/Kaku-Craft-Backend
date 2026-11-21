import json
import logging
import time
import urllib.parse
import urllib.request
from django.conf import settings
from django.core.management.base import BaseCommand
from notifications.services import activate_telegram_link, send_telegram_message

logger = logging.getLogger(__name__)


class Command(BaseCommand):
	help = "Runs a local polling worker for Telegram Bot to process /start deep-links"

	def handle(self, *args, **options):
		token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
		if not token:
			self.stderr.write(self.style.ERROR("TELEGRAM_BOT_TOKEN is not configured in settings/env."))
			return

		self.stdout.write(self.style.SUCCESS(f"Starting Telegram Bot polling for @{settings.TELEGRAM_BOT_USERNAME}..."))
		offset = None

		while True:
			try:
				url = f"https://api.telegram.org/bot{token}/getUpdates?timeout=30"
				if offset:
					url += f"&offset={offset}"

				req = urllib.request.urlopen(url, timeout=40)
				data = json.loads(req.read().decode("utf-8"))

				for update in data.get("result", []):
					update_id = update["update_id"]
					offset = update_id + 1

					message = update.get("message") or {}
					chat = message.get("chat") or {}
					chat_id = chat.get("id")
					text = (message.get("text") or "").strip()

					if text.startswith("/start") and chat_id:
						parts = text.split(maxsplit=1)
						token_code = parts[1].strip() if len(parts) > 1 else ""

						if token_code:
							link = activate_telegram_link(token_code, chat_id)
							if link:
								self.stdout.write(self.style.SUCCESS(f"Linked user #{link.user_id} to Telegram chat #{chat_id}"))
								send_telegram_message(
									chat_id,
									"Welcome to Kaku Craft!\n\nYour Telegram account is now connected. You will receive instant alerts for your order deposits, custom quotes, and atelier progress here."
								)
							else:
								send_telegram_message(chat_id, "Sorry, this link token has expired or is invalid.")
						else:
							send_telegram_message(
								chat_id,
								"Welcome to Kaku Craft Bot!\n\nPlease link your account through the Kaku Craft website to receive order updates."
							)

			except Exception as exc:
				self.stderr.write(f"Telegram polling error: {exc}")
				time.sleep(3)
