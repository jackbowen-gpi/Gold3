"""
Main Django settings file # Import local settings if they exist (for local overrides)
# Note: settings_local.py doesn't exist yet, but this allows for future local overrides
# try:
#     from config.settings_local import DEBUG, DATABASES
# except ImportError:
#     passld3 project.
This file orchestrates the settings by importing from modular configuration files.
"""

import os
import sys
from pathlib import Path

# Import base settings that are common to all environments
from config.settings_base import DEBUG, STATIC_URL

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DEV_DB_NAME", "gchub_dev"),
        "USER": os.environ.get("DEV_DB_USER", "gchub"),
        "PASSWORD": os.environ.get("DEV_DB_PASSWORD", "gchub"),
        "HOST": os.environ.get("DEV_DB_HOST", "db"),
        "PORT": os.environ.get("DEV_DB_PORT", "5432"),
    }
}

# Application definition
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
    # Third-party apps
    "django_extensions",
    "formtools",
    "django_celery_beat",
    "debug_toolbar",  # Django Debug Toolbar
    # Project apps
    "gchub_db.apps.accounts",
    "gchub_db.apps.legacy_support",
    "gchub_db.apps.admin_log",
    "gchub_db.apps.archives",
    "gchub_db.apps.bev_billing",
    "gchub_db.apps.budget",
    "gchub_db.apps.joblog",
    "gchub_db.apps.workflow",
    "gchub_db.apps.item_catalog",
    "gchub_db.apps.address",
    "gchub_db.apps.color_mgt",
    "gchub_db.apps.error_tracking",
    "gchub_db.apps.carton_billing",
    "gchub_db.apps.catscanner",
    "gchub_db.apps.draw_down",
    "gchub_db.apps.fedexsys",
    "gchub_db.apps.manager_tools",
    "gchub_db.apps.news",
    "gchub_db.apps.performance",
    "gchub_db.apps.qad_data",
    "gchub_db.apps.qc",
    "gchub_db.apps.queues",
    "gchub_db.apps.sbo",
    "gchub_db.apps.software",
    "gchub_db.apps.timesheet",
    "gchub_db.apps.video_player",
    "gchub_db.apps.xml_io",
    "gchub_db.apps.django_su",
    "gchub_db.apps.auto_corrugated",
    "gchub_db.apps.auto_ftp",
    "gchub_db.apps.art_req",
    "gchub_db.apps.calendar",
]

# Import SECRET_KEY from secrets or use fallback
try:
    from config.secrets import SECRET_KEY
except ImportError:
    SECRET_KEY = "fallback-secret-key-change-in-production"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Add the project root to Python path
sys.path.insert(0, str(BASE_DIR))

# Determine the environment
ENVIRONMENT = os.environ.get("DJANGO_ENV", "development").lower()

# Import environment-specific settings
if ENVIRONMENT == "production":
    from config.settings_production import DEBUG
elif ENVIRONMENT == "staging":
    # Staging settings not implemented yet, use development
    from config.settings_development import DEBUG
else:
    # Default to development
    from config.settings_development import DEBUG

# Import local settings if they exist (for local overrides)
try:
    from config.local_settings import (
        ALLOWED_HOSTS as LOCAL_ALLOWED_HOSTS,
    )
    from config.local_settings import (
        DATABASES as LOCAL_DATABASES,
    )
    from config.local_settings import (
        DEBUG as LOCAL_DEBUG,
    )
    from config.local_settings import (
        EMAIL_BACKEND as LOCAL_EMAIL_BACKEND,
    )
    from config.local_settings import (
        EMAIL_HOST as LOCAL_EMAIL_HOST,
    )
    from config.local_settings import (
        INTERNAL_IPS as LOCAL_INTERNAL_IPS,
    )
    from config.local_settings import (
        LOGGING as LOCAL_LOGGING,
    )
    from config.local_settings import (
        MIDDLEWARE as LOCAL_MIDDLEWARE,
    )
    from config.local_settings import (
        ROOT_URLCONF as LOCAL_ROOT_URLCONF,
    )
    from config.local_settings import (
        STATIC_ROOT as LOCAL_STATIC_ROOT,
    )

    # Apply local overrides if they exist
    if "LOCAL_DEBUG" in locals():
        DEBUG = LOCAL_DEBUG
    if "LOCAL_ALLOWED_HOSTS" in locals():
        ALLOWED_HOSTS = LOCAL_ALLOWED_HOSTS
    if "LOCAL_ROOT_URLCONF" in locals():
        ROOT_URLCONF = LOCAL_ROOT_URLCONF
    if "LOCAL_MIDDLEWARE" in locals():
        MIDDLEWARE = LOCAL_MIDDLEWARE
    if "LOCAL_INTERNAL_IPS" in locals():
        INTERNAL_IPS = LOCAL_INTERNAL_IPS
    if "LOCAL_LOGGING" in locals():
        LOGGING = LOCAL_LOGGING
    if "LOCAL_DATABASES" in locals():
        DATABASES = LOCAL_DATABASES
    if "LOCAL_EMAIL_BACKEND" in locals():
        EMAIL_BACKEND = LOCAL_EMAIL_BACKEND
    if "LOCAL_EMAIL_HOST" in locals():
        EMAIL_HOST = LOCAL_EMAIL_HOST
    if "LOCAL_STATIC_ROOT" in locals():
        STATIC_ROOT = LOCAL_STATIC_ROOT
except ImportError:
    pass

# Override settings with environment variables if provided
# This allows for Docker/container environment configuration
debug_env = os.environ.get("DJANGO_DEBUG")
if debug_env:
    DEBUG = debug_env.lower() in ("true", "1", "yes")

secret_key_env = os.environ.get("DJANGO_SECRET_KEY")
if secret_key_env:
    SECRET_KEY = secret_key_env

# Database configuration from environment variables (overrides settings files)
# Note: dj_database_url package not installed, uncomment when needed
# if os.environ.get("DATABASE_URL"):
#     try:
#         import dj_database_url
#         DATABASES["default"] = dj_database_url.config(
#             default=os.environ.get("DATABASE_URL")
#         )
#     except ImportError:
#         # dj_database_url not installed, skip database URL configuration
#         pass

# Email configuration from environment variables
if os.environ.get("EMAIL_HOST"):
    EMAIL_HOST = os.environ.get("EMAIL_HOST")  # type: ignore[assignment]
if os.environ.get("EMAIL_PORT"):
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 25))
if os.environ.get("EMAIL_HOST_USER"):
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")  # type: ignore[assignment]
if os.environ.get("EMAIL_HOST_PASSWORD"):
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")  # type: ignore[assignment]

# Redis/Celery configuration from environment variables
if os.environ.get("REDIS_URL"):
    CELERY_BROKER_URL = os.environ.get("REDIS_URL")
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")

# Static files configuration for production
if not DEBUG:
    # Use environment variables for CDN/static file configuration
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        # AWS S3 configuration
        AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
        AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
        AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
        AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
        AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN")

        # Use S3 for static files
        STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
        STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    elif os.environ.get("STATIC_URL_CDN"):
        static_url_cdn = os.environ.get("STATIC_URL_CDN")
        if static_url_cdn:
            STATIC_URL = static_url_cdn
            if not STATIC_URL.endswith("/"):
                STATIC_URL += "/"

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
