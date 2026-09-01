"""
Django settings for the Tahweel backend.

Configuration is environment-driven so the exact same codebase runs in
local dev (SQLite/Postgres + local media) and in production (Postgres +
Cloudflare R2), per the project's storage/DB abstraction requirements.
"""
from datetime import timedelta
from pathlib import Path
import os

import dj_database_url
from corsheaders.defaults import default_headers
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-do-not-use-in-production")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # local apps
    "apps.core",
    "apps.accounts",
    "apps.products",
    "apps.documents",
    "apps.inquiries",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.accounts.middleware.SiteAccessMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_ENGINE = os.environ.get("DB_ENGINE", "postgres").lower()
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "tahweel"),
            "USER": os.environ.get("POSTGRES_USER", "tahweel"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "tahweel"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media / storage abstraction
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES_STATICFILES_BACKEND = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = f"/{STATIC_URL}media/"
STATICFILES_DIRS = [
    (str(Path("media") / "products"), MEDIA_ROOT / "products"),
    (
        str(Path("media") / "documents" / "covers"),
        MEDIA_ROOT / "documents" / "covers",
    ),
]

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local").lower()

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "tahweel-media")
R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN", "")

if STORAGE_BACKEND == "r2":
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": R2_ACCESS_KEY_ID,
                "secret_key": R2_SECRET_ACCESS_KEY,
                "bucket_name": R2_BUCKET_NAME,
                "endpoint_url": f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                "custom_domain": R2_PUBLIC_DOMAIN or None,
                "default_acl": None,
                "signature_version": "s3v4",
                "region_name": "auto",
                "querystring_auth": not bool(R2_PUBLIC_DOMAIN),
                "file_overwrite": False,
            },
        },
        "staticfiles": {
            "BACKEND": STORAGES_STATICFILES_BACKEND,
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": STORAGES_STATICFILES_BACKEND,
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ALLOW_HEADERS = (*default_headers, "x-site-access")

# ---------------------------------------------------------------------------
# Site-wide passcode gate
# ---------------------------------------------------------------------------
# The gate is disabled when SITE_ACCESS_PASSCODE is blank. Keep this secret on
# the backend; never expose it through a VITE_* variable, which would embed it
# in the public browser bundle.
SITE_ACCESS_PASSCODE = os.environ.get("SITE_ACCESS_PASSCODE", "")
SITE_ACCESS_TOKEN_MAX_AGE = int(
    os.environ.get("SITE_ACCESS_TOKEN_MAX_AGE", "").strip() or 60 * 60 * 12
)

# ---------------------------------------------------------------------------
# DRF / JWT / OpenAPI
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "apps.core.permissions.IsStaffOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_THROTTLE_RATES": {
        "site_access": "10/minute",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("JWT_ACCESS_LIFETIME_MINUTES", 30))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_REFRESH_LIFETIME_DAYS", 7))),
    "ROTATE_REFRESH_TOKENS": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Tahweel API",
    "DESCRIPTION": "Public + admin API for the Tahweel product/document catalogue.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

AUTH_USER_MODEL = "auth.User"

DEFAULT_AUTO_PK = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
