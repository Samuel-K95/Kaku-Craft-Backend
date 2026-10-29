import os
from importlib.util import find_spec

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

if find_spec("channels") is not None:
	from channels.routing import ProtocolTypeRouter, URLRouter

	from messaging.middleware import JwtAuthMiddlewareStack
	from messaging.routing import websocket_urlpatterns

	application = ProtocolTypeRouter(
		{
			"http": django_asgi_app,
			"websocket": JwtAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
		}
	)
else:
	application = django_asgi_app
