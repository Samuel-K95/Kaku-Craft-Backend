from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _user_from_token(token):
	from django.contrib.auth import get_user_model
	from rest_framework_simplejwt.tokens import AccessToken

	User = get_user_model()
	try:
		access = AccessToken(token)
		return User.objects.get(pk=access["user_id"])
	except Exception:
		return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
	async def __call__(self, scope, receive, send):
		query = parse_qs(scope.get("query_string", b"").decode())
		token_list = query.get("token") or []
		if token_list:
			scope["user"] = await _user_from_token(token_list[0])
		elif "user" not in scope:
			scope["user"] = AnonymousUser()
		return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
	return JwtAuthMiddleware(inner)
