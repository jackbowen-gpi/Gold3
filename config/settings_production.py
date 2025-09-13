"""
Production environment settings.
This file contains production-specific configuration.
"""

# Try to load secrets configuration
try:
    from .secrets import DATABASE_CREDENTIALS

    print("Loaded database credentials from config/secrets.py")
except ImportError:
    print("Warning: config/secrets.py not found. Using fallback database values.")
    DATABASE_CREDENTIALS = {
        "production": {
            "NAME": "thundercuddles",
            "USER": "thundercuddles",
            "PASSWORD": "332088",
            "HOST": "172.23.8.73",
            "PORT": "5432",
        }
    }

# Override base settings for production
DEBUG = False

# Production-specific security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Production allowed hosts (will be overridden by secrets)
ALLOWED_HOSTS = [
    "gchub.ipaper.com",
    "141.129.41.107",
    "gchub.everpack.local",
    "10.91.209.116",
    "160.109.16.228",
    "gchub.graphicpkg.com",
]

# Production database (uses secrets or environment variables)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        **DATABASE_CREDENTIALS["production"],
    }
}

# Production email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Production logging
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
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "/var/log/gchub/django.log",
            "formatter": "verbose",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "gchub_db": {
            "handlers": ["file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
