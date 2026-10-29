"""
Django settings for config project.
"""

import os
from pathlib import Path
from datetime import timedelta
from importlib.util import find_spec

BASE_DIR = Path(__file__).resolve().parent.parent

# Optional local .env support (no hard dependency if python-dotenv is absent).
_env_path = BASE_DIR / ".env"
if _env_path.exists():
	try:
		from dotenv import load_dotenv

		load_dotenv(_env_path)
	except ImportError:
		for _line in _env_path.read_text(encoding="utf-8").splitlines():
			_line = _line.strip()
			if not _line or _line.startswith("#") or "=" not in _line:
				continue
			_key, _value = _line.split("=", 1)
			_key = _key.strip()
			_value = _value.strip().strip('"').strip("'")
			os.environ.setdefault(_key, _value)

SECRET_KEY = os.getenv(
	"DJANGO_SECRET_KEY",
	"django-insecure-dev-only-key-change-me-please-1234567890",
)

DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = [
	host.strip()
	for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
	if host.strip()
]

CHANNELS_AVAILABLE = find_spec("channels") is not None
CELERY_AVAILABLE = find_spec("celery") is not None
DAPHNE_AVAILABLE = find_spec("daphne") is not None

INSTALLED_APPS = []
if DAPHNE_AVAILABLE:
	INSTALLED_APPS.append("daphne")

INSTALLED_APPS += [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"rest_framework",
	"corsheaders",
	"drf_spectacular",
	"users",
	"products",
	"orders",
	"reviews",
	"messaging",
	"notifications",
	"cms",
]

if CHANNELS_AVAILABLE:
	INSTALLED_APPS.insert(INSTALLED_APPS.index("drf_spectacular") + 1, "channels")

MIDDLEWARE = [
	"corsheaders.middleware.CorsMiddleware",
	"django.middleware.security.SecurityMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = os.getenv("DJANGO_CORS_ALLOW_ALL_ORIGINS", "true").lower() == "true"
CORS_ALLOWED_ORIGINS = [
	origin.strip()
	for origin in os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",")
	if origin.strip()
]

if CORS_ALLOW_ALL_ORIGINS:
	CORS_ALLOWED_ORIGINS = []

ROOT_URLCONF = "config.urls"

TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
			],
		},
	},
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.sqlite3",
		"NAME": BASE_DIR / "db.sqlite3",
	}
}

REST_FRAMEWORK = {
	"DEFAULT_AUTHENTICATION_CLASSES": (
		"rest_framework_simplejwt.authentication.JWTAuthentication",
	),
	"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
	"DEFAULT_PERMISSION_CLASSES": (
		"rest_framework.permissions.IsAuthenticated",
	),
	"DEFAULT_THROTTLE_CLASSES": (
		"rest_framework.throttling.AnonRateThrottle",
		"rest_framework.throttling.UserRateThrottle",
	),
	"DEFAULT_THROTTLE_RATES": {
		"anon": os.getenv("DRF_THROTTLE_ANON", "100/hour"),
		"user": os.getenv("DRF_THROTTLE_USER", "1000/hour"),
	},
}

SPECTACULAR_SETTINGS = {
	"TITLE": "Kaku Craft Backend API",
	"DESCRIPTION": "API documentation for Kaku Craft commerce, messaging, CMS, and assistant.",
	"VERSION": "1.1.0",
}

SIMPLE_JWT = {
	"ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
	"REFRESH_TOKEN_LIFETIME": timedelta(days=1),
	"AUTH_HEADER_TYPES": ("Bearer",),
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
	{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
	{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
	{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
	{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("DJANGO_UPLOAD_MAX_MEMORY", str(5 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE

REDIS_URL = os.getenv("REDIS_URL", "")

if CHANNELS_AVAILABLE:
	if REDIS_URL:
		CHANNEL_LAYERS = {
			"default": {
				"BACKEND": "channels_redis.core.RedisChannelLayer",
				"CONFIG": {"hosts": [REDIS_URL]},
			}
		}
	else:
		CHANNEL_LAYERS = {
			"default": {
				"BACKEND": "channels.layers.InMemoryChannelLayer",
			}
		}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL or "memory://")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "cache+memory://")
CELERY_TASK_ALWAYS_EAGER = (
	os.getenv("CELERY_TASK_ALWAYS_EAGER", "true" if DEBUG else "false").lower() == "true"
)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")

LOGGING = {
	"version": 1,
	"disable_existing_loggers": False,
	"handlers": {
		"console": {
			"class": "logging.StreamHandler",
		}
	},
	"root": {
		"handlers": ["console"],
		"level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
	},
}

if not DEBUG:
	SECURE_SSL_REDIRECT = True
	SESSION_COOKIE_SECURE = True
	CSRF_COOKIE_SECURE = True
	SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
	SECURE_HSTS_INCLUDE_SUBDOMAINS = True
	SECURE_HSTS_PRELOAD = True
	SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
