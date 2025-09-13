"""Project package settings (moved from repo root settings.py)"""

import os
import pprint
import sys

# Import the main settings configuration
from config.settings import DEBUG  # type: ignore[assignment]

# Handle INTERNAL_IPS type conflict
try:
    # If INTERNAL_IPS is imported as tuple, convert to list
    if "INTERNAL_IPS" in globals() and isinstance(globals()["INTERNAL_IPS"], tuple):
        INTERNAL_IPS = list(globals()["INTERNAL_IPS"])  # type: ignore[assignment]
    else:
        INTERNAL_IPS = []
except Exception:
    INTERNAL_IPS = []

# Path to this package directory
MAIN_PATH = os.path.abspath(os.path.split(__file__)[0])
# Ensure the project parent directory is on sys.path so the package can be imported
# as `gchub_db.*` and modules under `gchub_db/apps` resolve correctly.
PROJECT_ROOT = os.path.dirname(MAIN_PATH)

# Make sure PROJECT_ROOT and its parent are early on sys.path so imports
# referenced by settings_common or INSTALLED_APPS find the correct package.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
parent = os.path.dirname(PROJECT_ROOT)
if parent not in sys.path:
    sys.path.insert(0, parent)

SITE_ID = 1

ROOT_URLCONF = "gchub_db.urls"
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"

STATIC_URL = "/static/"

# Templates configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # repo-root html (legacy location) so templates in <repo>/html are found
            os.path.join(PROJECT_ROOT, "html"),
            # package-local html/email_templates
            os.path.join(MAIN_PATH, "html"),
            os.path.join(MAIN_PATH, "email_templates"),
        ],
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "django.contrib.auth.context_processors.auth",
                "gchub_db.includes.extra_context.common_urls",
                "gchub_db.apps.accounts.context_processors.preferences_theme_context",
            ],
            "builtins": ["gchub_db.templatetags.legacy_tags"],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]

# CSRF Configuration for legacy AJAX calls
CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access to CSRF token
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SAMESITE = "Lax"

# For development, ensure CSRF tokens work with localhost
if DEBUG:
    CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]
    CSRF_COOKIE_SECURE = False

# Django Debug Toolbar configuration
# Only enable in DEBUG mode for security
if DEBUG:
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]

    # Additional Debug Toolbar settings
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    }

try:
    # Import specific variables from local_settings to avoid type conflicts
    from config.local_settings import (
        ALLOWED_HOSTS,
        AUTO_FTP_ENABLED,
        DJANGO_SERVE_MEDIA,
        EMAIL_BACKEND,
        EMAIL_HOST,
        ETOOLS_ENABLED,
        FS_ACCESS_ENABLED,
        FS_SERVER_HOST,
        QAD_ENABLED,
        ROOT_URLCONF,
        STATIC_ROOT,
        WEBSERVER_HOST,
        YUI_URL,
    )
except ImportError:
    # Define defaults if local_settings doesn't exist
    DJANGO_SERVE_MEDIA = True
    YUI_URL = "/media/yui/"
    EMAIL_HOST = "apache1.na.graphicpkg.pri"
    WEBSERVER_HOST = "http://apache1.na.graphicpkg.pri"
    FS_SERVER_HOST = "gcmaster.na.graphicpkg.pri"
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    ROOT_URLCONF = "gchub_db.urls"
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    ETOOLS_ENABLED = False
    QAD_ENABLED = False
    AUTO_FTP_ENABLED = False
    FS_ACCESS_ENABLED = False
    STATIC_ROOT = None

# DEBUG: Print DATABASES config at runtime
if (
    not os.environ.get("PYTEST_CURRENT_TEST")
    and not os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith("test_settings")
    and "test" not in sys.argv
):
    print("\n[DEBUG] settings.DATABASES at runtime:")
    pprint.pprint(globals().get("DATABASES", "<not set>"))

# DEBUG: Print TEMPLATES config at runtime
if (
    not os.environ.get("PYTEST_CURRENT_TEST")
    and not os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith("test_settings")
    and "test" not in sys.argv
):
    print("\n[DEBUG] settings.TEMPLATES at runtime:")
    pprint.pprint(globals().get("TEMPLATES", "<not set>"))
