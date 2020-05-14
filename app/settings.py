import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from app.variables import APP_TIMEZONE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from app.variables import *


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "vh@lz&bd-su!lh9#8y=kz$$tku*6fn-fz+9(tk4*w7(^7igxb-"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("PROD_MODE", "false").lower() == "false"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# MAINTENANCE MODE
MAINTENANCE_MODE = os.environ.get("MAINTENANCE_MODE", "false").lower() == "true"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "bootstrap4",
    "versatileimagefield",
    "app",
    "user",
    "news",
    "event",
    "page",
    "cookielaw",
    "django_social_share",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "app.middlewares.RegisterMiddleware",
    "app.middlewares.MaintenanceModeMiddleware",
]

ROOT_URLCONF = "app.urls"

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
                "app.processor.variables_processor",
            ]
        },
    }
]

WSGI_APPLICATION = "app.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = APP_TIMEZONE

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR + "/staticfiles"
STATICFILES_DIRS = [os.path.join(BASE_DIR, os.path.join("app", "static"))]
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# File upload configuration

MEDIA_URL = "/files/"
MEDIA_ROOT = BASE_DIR + "/files"

# Set up custom authenthication

AUTH_USER_MODEL = "user.User"
PASSWORD_RESET_TIMEOUT_DAYS = 1

# Add domain to allowed hosts

APP_DOMAIN = os.environ.get("APP_DOMAIN", APP_LOCALHOST)
APP_IP = os.environ.get("APP_IP", APP_LOCALHOST)
ALLOWED_HOSTS.append(APP_DOMAIN)
ALLOWED_HOSTS.append("www." + APP_DOMAIN)

# Deployment configurations for proxy pass and CSRF

CSRF_TRUSTED_ORIGINS = ALLOWED_HOSTS
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Maximum file upload size and permissions

MAX_UPLOAD_SIZE = 26214400  # 25 MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Phone number format

PHONENUMBER_DB_FORMAT = "INTERNATIONAL"

# Sentry logging

SE_URL = os.environ.get("SE_URL", None)
if SE_URL:
    sentry_sdk.init(
        dsn=SE_URL,
        integrations=[DjangoIntegration()],
        debug=DEBUG,
        environment=os.environ.get("SE_ENV"),
        send_default_pii=True,
    )

# Signup status

SIGNUP_DISABLED = os.environ.get("SIGNUP_DISABLED", "false").lower() == "true"

# Google Analytics

GO_ID = os.environ.get("GO_ID", None)

# GitHub webhook endpoint availability

GH_KEY = os.environ.get("GH_KEY", None)
GH_BRANCH = os.environ.get("GH_BRANCH", "master")

# Slack integration

SL_INURL = os.environ.get("SL_INURL", None)

# Set CORS allowed hosts

CORS_ORIGIN_WHITELIST = []
for host in ALLOWED_HOSTS:
    list.append(CORS_ORIGIN_WHITELIST, "http://" + host)
    list.append(CORS_ORIGIN_WHITELIST, "https://" + host)

# Google authentication

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("GO_KEY", None)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get("GO_SECRET", None)
LOGIN_URL = "/user/login/google-oauth2/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_USER_MODEL = "user.GoogleUser"

if SOCIAL_AUTH_GOOGLE_OAUTH2_KEY and SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET:
    INSTALLED_APPS += ["social_django"]
    TEMPLATES[0]["OPTIONS"]["context_processors"] + [
        "social_django.context_processors.backends",
        "social_django.context_processors.login_redirect",
    ]
    AUTHENTICATION_BACKENDS = (
        "social_core.backends.google.GoogleOAuth2",
        "django.contrib.auth.backends.ModelBackend",
    )

# SMTP settings
# TODO: Document this
# https://support.google.com/a/answer/2956491?hl=en

EMAIL_HOST = "smtp-relay.gmail.com"
EMAIL_PORT = "587"
EMAIL_USE_TLS = True

# Notify templates

NOTIFY_TEMPLATES = dict(
    email=dict(
        user=dict(
            register=dict(
                subject="Confirm your email to register",
                html="email/user/register.html",
            ),
            password=dict(
                subject="Reset your password to login", html="email/user/password.html"
            ),
            imported=dict(
                subject="Welcome to KTHAIS new website", html="email/user/imported.html"
            ),
        ),
        event=dict(
            register=dict(
                subject="Registration confirmation for {event}",
                html="email/event/register.html",
            ),
            cancel=dict(
                subject="Registration cancellation for {event}",
                html="email/event/cancel.html",
            ),
            url=dict(subject="Remember to join {event}", html="email/event/url.html"),
        ),
    )
)
