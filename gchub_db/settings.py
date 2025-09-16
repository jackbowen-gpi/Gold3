"""Project package settings (moved from repo root settings.py)"""

import os
import pprint
import sys

# Import the main settings configuration
from config.settings import (
    ALLOWED_HOSTS,
    DEBUG,
    EMAIL_BACKEND,
    EMAIL_HOST,
    INTERNAL_IPS,
    MIDDLEWARE,
)  # type: ignore[assignment]

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

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

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

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")

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
            # Add debug_toolbar templates directory
            "/usr/local/lib/python3.11/site-packages/debug_toolbar/templates",
        ],
        "APP_DIRS": True,  # Enable app directories loader for third-party packages like debug_toolbar
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

    # Add debug_toolbar middleware if not already present
    if "debug_toolbar" in [app.split(".")[-1] for app in INSTALLED_APPS]:
        if "MIDDLEWARE" in globals():
            if "debug_toolbar.middleware.DebugToolbarMiddleware" not in globals()["MIDDLEWARE"]:
                globals()["MIDDLEWARE"].insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
        else:
            # Define MIDDLEWARE if not imported
            MIDDLEWARE = [
                "debug_toolbar.middleware.DebugToolbarMiddleware",
                "django.middleware.security.SecurityMiddleware",
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.middleware.common.CommonMiddleware",
                "django.middleware.csrf.CsrfViewMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
                "django.middleware.clickjacking.XFrameOptionsMiddleware",
            ]

# Default values for missing settings used in context processors
DLOADER_URL = "http://localhost:8080"
EMAIL_SUPPORT = "support@localhost"
EMAIL_GCHUB = "gchub@localhost"

try:
    # Import specific variables from local_settings to avoid type conflicts
    from config.local_settings import (
        ALLOWED_HOSTS,
        AUTO_FTP_ENABLED,
        BEVERAGE_DROP_FOLDER,
        DJANGO_SERVE_MEDIA,
        EMAIL_BACKEND,
        EMAIL_FROM_ADDRESS,
        EMAIL_HOST,
        ETOOLS_ENABLED,
        FS_ACCESS_ENABLED,
        FS_SERVER_HOST,
        FS_SERVER_PORT,
        FSB_PROD_TEMPLATES,
        FSB_TEMPLATES,
        JOBSTORAGE_DIR,
        PRODUCTION_DIR,
        QAD_ENABLED,
        ROOT_URLCONF,
        STATIC_ROOT,
        WEBSERVER_HOST,
        WORKFLOW_ROOT_DIR,
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
    # Define missing settings for development
    WORKFLOW_ROOT_DIR = "/tmp"
    PRODUCTION_DIR = "/tmp/Production"
    BEVERAGE_DROP_FOLDER = "/tmp/Beverage/Drop"
    FSB_TEMPLATES = "/tmp/Templates/FSB"
    FSB_PROD_TEMPLATES = "/tmp/Templates/FSB/Production"
    JOBSTORAGE_DIR = "/tmp/Jobs"
    FS_SERVER_PORT = 8080
    EMAIL_FROM_ADDRESS = "noreply@localhost"

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
