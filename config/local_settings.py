"""Local overrides for development settings (kept out of source control)."""

import os  # Operating System level things (files, dirs, etc)
import os.path
import warnings

# WORKFLOW_ROOT_DIR = '/mnt'
WORKFLOW_ROOT_DIR = "/tmp"  # Default for development
PRODUCTION_DIR = os.path.join(WORKFLOW_ROOT_DIR, "Production")
# BACKUP_DIR = os.path.join(WORKFLOW_ROOT_DIR, 'Testing/Backup')ANGO_SERVE_MEDIA = True
DEBUG = True
YUI_URL = "/media/yui/"

# Work from home stuff.
EMAIL_HOST = "apache1.na.graphicpkg.pri"
WEBSERVER_HOST = "http://apache1.na.graphicpkg.pri"
FS_SERVER_HOST = "gcmaster.na.graphicpkg.pri"
# LIVE GOLD DATABASE!!! USE WITH CAUTION!!!
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
#         'NAME': 'thundercuddles',                            # Or path to database file if using sqlite3.
#         'USER': 'thundercuddles',                            # Not used with sqlite3.
#         'PASSWORD': '332088',                                # Not used with sqlite3.
#         'HOST': 'db2017.na.graphicpkg.pri',                  # Set to empty string for localhost. Not used with sqlite3.
#         'PORT': '5432',                                      # Set to empty string for default. Not used with sqlite3.
#     }
# }

# Uncomment these three lines to use jdf_queue_test in the Production directory.
# WORKFLOW_ROOT_DIR = '/mnt'
# PRODUCTION_DIR = os.path.join(WORKFLOW_ROOT_DIR, 'Production')
# JDF_ROOT = os.path.join(PRODUCTION_DIR, 'jdf_queue_test/')

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "172.23.8.29",
    "10.211.55.4",
    "192.168.7.214",
    "*",
]

# Use the real project URL configuration for normal development.
ROOT_URLCONF = "gchub_db.urls"

# Development-only middleware additions: include a pretty exception logger
# so terminal logs include concise exception summaries.
# Ensure MIDDLEWARE is defined before appending to it.
if "MIDDLEWARE" not in globals():
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ]

# Append our middleware at the end so Django's default error handling still runs.
MIDDLEWARE.append("gchub_db.middleware.pretty_exception.PrettyExceptionMiddleware")

# Add Django Debug Toolbar middleware for development
if DEBUG:
    try:
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    except Exception:
        # Don't fail startup if debug toolbar middleware can't be added
        pass

# Configure INTERNAL_IPS for Django Debug Toolbar in Docker environment
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
    "172.19.0.1",  # Docker network gateway
    "172.19.0.0/16",  # Allow entire Docker network subnet
    "192.168.0.0/16",  # Allow common local network ranges
    "10.0.0.0/8",  # Allow common local network ranges
    "0.0.0.0/0",  # Allow all IPs (for development)
]

# Ensure the development-only middleware that strips Permissions-Policy/Feature-Policy
# headers is active when running locally with DEBUG=True. Put it early in the
# chain so it can modify response headers from other middleware/views.
if DEBUG:
    dev_mw = "gchub_db.middleware.remove_permissions_policy.RemovePermissionsPolicyHeaderMiddleware"
    try:
        if isinstance(MIDDLEWARE, list):
            if dev_mw not in MIDDLEWARE:
                MIDDLEWARE.insert(0, dev_mw)
        else:
            # If it's a tuple, convert safely to keep ordering
            if dev_mw not in tuple(MIDDLEWARE):  # type: ignore[unreachable]
                MIDDLEWARE = (dev_mw,) + tuple(MIDDLEWARE)  # type: ignore[unreachable]
    except Exception:
        # Don't fail startup for a non-critical dev convenience change
        pass

# Improve console logging for development: concise formatter and WARN level for
# noisy third-party libs. This keeps the console readable while still writing
# full traces to Django/error logs when needed.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "compact": {"format": "%(levelname)s %(name)s: %(message)s"},
        "verbose": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "compact",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        # Dev-friendly overrides
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "pretty_exceptions": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Silence some noisy third-party modules at WARNING level
        "gntp": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "colormath": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

# Filter noisy SyntaxWarning messages from third-party libraries during dev runs

warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"gntp\..*")
warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"colormath\..*")


# Use Postgres for local development by default. Configure the connection
# via environment variables (recommended) or rely on the project-level
# `settings_common.py` DATABASES value which already targets Postgres.
#
# To explicitly control local Postgres settings, set USE_PG_DEV=1 (or
# TRUE) and provide DEV_DB_NAME/DEV_DB_USER/DEV_DB_PASSWORD/DEV_DB_HOST/DEV_DB_PORT
# as needed. If those are not set we will fall back to the DATABASES value
# provided by the imported shared settings.
try:
    use_pg = os.environ.get("USE_PG_DEV", "1").lower() in ("1", "true", "yes")
except Exception:
    use_pg = True

if use_pg:
    DEV_DB_NAME = os.environ.get("DEV_DB_NAME", os.environ.get("PG_DB_NAME", None))
    DEV_DB_USER = os.environ.get("DEV_DB_USER", os.environ.get("PG_DB_USER", None))
    DEV_DB_PASSWORD = os.environ.get(
        "DEV_DB_PASSWORD", os.environ.get("PG_DB_PASSWORD", None)
    )
    DEV_DB_HOST = os.environ.get(
        "DEV_DB_HOST", os.environ.get("PG_DB_HOST", "localhost")
    )
    DEV_DB_PORT = os.environ.get("DEV_DB_PORT", os.environ.get("PG_DB_PORT", "5432"))
    DEV_DB_ENGINE = os.environ.get("DEV_DB_ENGINE", "django.db.backends.postgresql")

    # If a DEV_DB_NAME (or PG_DB_NAME) is present we will construct DATABASES
    # from the environment; otherwise we assume the project default (from
    # settings_common) is a Postgres configuration and leave it intact.
    if DEV_DB_NAME:
        DATABASES = {
            "default": {
                "ENGINE": DEV_DB_ENGINE,
                "NAME": DEV_DB_NAME,
                "USER": DEV_DB_USER or "",
                "PASSWORD": DEV_DB_PASSWORD or "",
                "HOST": DEV_DB_HOST,
                "PORT": DEV_DB_PORT,
            }
        }
    # else: leave DATABASES alone so settings_common or an external config
    # drives the DB selection (expected to be Postgres).

# Test email. Prints emails to console instead of sending them. For testing.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# WORKFLOW_ROOT_DIR = '/mnt'
WORKFLOW_ROOT_DIR = "/tmp"  # Default for development
# BACKUP_DIR = os.path.join(WORKFLOW_ROOT_DIR, 'Testing/Backup')

# Beverage drop folder for development
BEVERAGE_DROP_FOLDER = os.path.join(WORKFLOW_ROOT_DIR, "Beverage", "Drop")

# FSB templates
FSB_TEMPLATES = os.path.join(WORKFLOW_ROOT_DIR, "Templates", "FSB")
FSB_PROD_TEMPLATES = os.path.join(WORKFLOW_ROOT_DIR, "Templates", "FSB", "Production")

# Job storage directory
JOBSTORAGE_DIR = os.path.join(WORKFLOW_ROOT_DIR, "Jobs")

# File server port
FS_SERVER_PORT = 8080

# Email from address
EMAIL_FROM_ADDRESS = "noreply@localhost"

# For testing postfix installed locally.
# EMAIL_HOST = "172.23.8.29"

# LDAP_SERVER_URI = "ldap://GPIPTCDC01.na.graphicpkg.pri"

# Disable ETOOLS connection for development (no ODBC DSN available)
ETOOLS_ENABLED = False

# Disable QAD connection for development (no ODBC DSN available)
QAD_ENABLED = False

# Disable Auto FTP system for development (no external FTP servers available)
AUTO_FTP_ENABLED = False

# Disable file system access for development (no network file system available)
# This includes preview art, print separations, and other job file access
FS_ACCESS_ENABLED = False

# Default static files destination for local development.
# Collectstatic needs STATIC_ROOT set to a filesystem path. Use an env override
# if provided; otherwise write to a local staticfiles directory for Windows development.
STATIC_ROOT = os.environ.get(
    "STATIC_ROOT", os.path.join(os.path.dirname(__file__), "..", "staticfiles")
)
