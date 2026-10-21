"""Calculus settings.

Storage is split into four SQLite files inside the data/ folder:
  credentials.sqlite3  usernames + password hashes only
  users.sqlite3        companies, user profiles, and which areas each user may open
  invoices.sqlite3     sales invoices + customers
  purchases.sqlite3    purchase bills + suppliers
core/routers.py decides which app uses which file.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("CALCULUS_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def env_list(name, default):
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


SECRET_KEY = os.environ.get("CALCULUS_SECRET_KEY", "change-this-secret-before-going-live")
DEBUG = os.environ.get("CALCULUS_DEBUG") == "1"
ALLOWED_HOSTS = env_list("CALCULUS_ALLOWED_HOSTS", "127.0.0.1,localhost")
CSRF_TRUSTED_ORIGINS = env_list("CALCULUS_CSRF_ORIGINS", "")  # e.g. https://app.yourdomain.com

INSTALLED_APPS = [
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "directory",
    "sales",
    "purchases",
    "statements",
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "core.middleware.CurrentUserMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.messages.context_processors.messages",
        "core.context.globals",
    ]},
}]


def sqlite(name):
    return {"ENGINE": "django.db.backends.sqlite3", "NAME": DATA_DIR / name}


DATABASES = {
    "default": sqlite("users.sqlite3"),
    "credentials": sqlite("credentials.sqlite3"),
    "invoices": sqlite("invoices.sqlite3"),
    "purchases": sqlite("purchases.sqlite3"),
}
DATABASE_ROUTERS = ["core.routers.AppRouter"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sessions live in a signed cookie (nothing stored in any database).
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 8 * 60 * 60          # automatic logout after 8 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_FAILURE_VIEW = "core.views.errors.csrf_failure"

if os.environ.get("CALCULUS_HTTPS") == "1":   # set this once your site runs on https://
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)
WHITENOISE_USE_FINDERS = True
