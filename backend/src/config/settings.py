import secrets
import sys
from pathlib import Path

from config.environment import Environment
from config.logging import console_handler

environment = Environment()
SECRET_KEY = environment.DJANGO_SECRET_KEY.get_secret_value() or secrets.token_urlsafe(48)
DEBUG = False
ALLOWED_HOSTS = environment.DJANGO_ALLOWED_HOSTS.split(",")
ROOT_URLCONF = "config.urls"
BASE_DIR = Path(__file__).resolve().parents[3]
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.import_export",
    "unfold.contrib.simple_history",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "import_export",
    "simple_history",
    "adminsortable2",
    "django_filters",
    "apps.hello.apps.HelloConfig",
    "apps.notes.apps.NotesConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": environment.DJANGO_DB_PATH,
        "OPTIONS": {"timeout": 20},
    }
}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
STATIC_URL = "/static/"
STATIC_ROOT = Path(getattr(sys, "_MEIPASS", BASE_DIR / "backend/build")) / "static"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DESKTOP_TOKEN = environment.DESKTOP_TOKEN.get_secret_value()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"()": console_handler}},
    "loggers": {
        "app_base.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["api.permissions.DesktopAccess"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "UNAUTHENTICATED_USER": None,
}
# Next dev only; production and desktop serve the static UI on the API origin.
CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:3100", "http://localhost:3100"]

CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

SPECTACULAR_SETTINGS = {
    "TITLE": "App Base API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

IMPORT_EXPORT_IMPORT_PERMISSION_CODE = "change"
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = "view"
IMPORT_EXPORT_USE_TRANSACTIONS = True
SIMPLE_HISTORY_REVERT_DISABLED = True
