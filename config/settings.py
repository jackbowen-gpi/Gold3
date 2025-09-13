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
# Note: settings_local.py doesn't exist yet, but this allows for future local overrides
# try:
#     from config.settings_local import DATABASES, DEBUG
# except ImportError:
#     pass

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
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
if os.environ.get("EMAIL_PORT"):
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 25))
if os.environ.get("EMAIL_HOST_USER"):
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
if os.environ.get("EMAIL_HOST_PASSWORD"):
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

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
