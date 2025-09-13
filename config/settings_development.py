"""
Development environment settings.
This file contains development-specific configuration.
"""

from .settings_base import INSTALLED_APPS, MIDDLEWARE

# Try to load secrets configuration
try:
    from .secrets import DATABASE_CREDENTIALS

    print("Loaded database credentials from config/secrets.py")
except ImportError:
    print("Warning: config/secrets.py not found. Using fallback database values.")
    DATABASE_CREDENTIALS = {
        "development": {
            "NAME": "gchub_dev",
            "USER": "gchub",
            "PASSWORD": "gchub",
            "HOST": "127.0.0.1",
            "PORT": "5438",
        }
    }

# Override base settings for development
DEBUG = True

# Development-specific apps
INSTALLED_APPS += [
    "debug_toolbar",
]

# Development-specific middleware
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

# Django Debug Toolbar configuration
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}

# Development database (uses secrets or environment variables)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        **DATABASE_CREDENTIALS["development"],
    }
}

# Development-specific allowed hosts
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "172.23.8.29",
    "10.211.55.4",
    "192.168.7.214",
]

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable security features in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Development-specific logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "gchub_db": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
