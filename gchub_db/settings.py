"""Project package settings (moved from repo root settings.py)"""

import os
import sys
import pprint

# Import common settings
# Import all common settings
from config.settings_common import *  # noqa: F403
from config.settings_common import DEBUG  # noqa: F401

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

MIDDLEWARE = (
    # Ensure dev auto-login runs early in the middleware chain when debugging.
    *(("gchub_db.middleware.dev_auto_login.DevAutoLoginMiddleware",) if DEBUG else ()),
    # In DEBUG, remove Permissions-Policy / Feature-Policy to avoid blocking
    # legacy vendor scripts that register `unload` handlers (prototype/YUI/etc.).
    *(("gchub_db.middleware.remove_permissions_policy.RemovePermissionsPolicyHeaderMiddleware",) if DEBUG else ()),
    # Django Debug Toolbar middleware - only in DEBUG mode
    *(("debug_toolbar.middleware.DebugToolbarMiddleware",) if DEBUG else ()),
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    #'django.middleware.doc.XViewMiddleware',
    "gchub_db.middleware.threadlocals.ThreadLocals",
    "gchub_db.middleware.maintenance_mode.middleware.MaintenanceModeMiddleware",
)

INSTALLED_APPS = (
    "maintenance_mode",
    "django.contrib.admindocs",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "gchub_db.apps.django_su",
    "django.contrib.admin",
    "django.contrib.humanize",
    "django.contrib.staticfiles",
    "formtools",
    "django_extensions",
    # Django Debug Toolbar - only in DEBUG mode
    *(("debug_toolbar",) if DEBUG else ()),
    "django_celery_beat",
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
    "gchub_db.apps.calendar",
    "gchub_db.apps.xml_io",
    "gchub_db.apps.queues",
    "gchub_db.apps.auto_ftp",
    "gchub_db.apps.fedexsys",
    "gchub_db.apps.qad_data",
    "gchub_db.apps.software",
    "gchub_db.apps.news",
    "gchub_db.apps.qc",
    "gchub_db.apps.auto_corrugated",
    "gchub_db.apps.manager_tools",
    "gchub_db.apps.draw_down",
    "gchub_db.apps.video_player",
    "gchub_db.apps.timesheet",
    "gchub_db.apps.art_req",
    "gchub_db.apps.sbo",
    "gchub_db.apps.carton_billing",
    "gchub_db.apps.catscanner",
)

# Logging configuration mirrored from root settings copy

try:
    from rich.logging import RichHandler  # type: ignore

    RICH_AVAILABLE = True
except Exception:
    RichHandler = None
    RICH_AVAILABLE = False

LOG_DIR = os.path.join(MAIN_PATH, "logs")
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    pass

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": ("logging.StreamHandler" if not RICH_AVAILABLE else "rich.logging.RichHandler"),
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "gchub.log"),
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "db_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "db_queries.log"),
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["db_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "gchub_db": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

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

try:
    from config.local_settings import *  # noqa: F403
except ImportError:
    pass

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
