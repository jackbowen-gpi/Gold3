"""
This file holds common configuration that may be used between more than
two different sites. This should generally never be modified, override values
via a local_settings.py file.
"""

import os
import sys

# The path to the root directory of the project (has this settings.py file in it) with
# trailing slash.
MAIN_PATH = os.path.abspath(os.path.split(__file__)[0])
sys.path.insert(0, os.path.join(MAIN_PATH, "includes"))
sys.path.insert(0, os.path.join(MAIN_PATH, "middleware"))

# Much slower when True, populates debugging variables. Sucks memory.
# Enable DEBUG for local development so dev-only helpers can run. Override
# this in production via `local_settings.py` if needed.
DEBUG = True

# Serve media files through Django dev server. Never use in production.
DJANGO_SERVE_MEDIA = True

# allowed_hosts determins which addresses are allowed to serve up django
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "172.23.8.16",
    "10.144.96.36",
    "gchub.ipaper.com",
    "141.129.41.107",
    "gchub",
    "gchub.everpack.local",
    "10.91.209.116",
    "160.109.16.228",
    "gchub.graphicpkg.com",
]

# Development convenience: allow relaxing security controls during local debug.
# Set RELAX_DEV_SECURITY=1 in the environment to allow permissive settings
# (ALLOWED_HOSTS='*', disable secure cookies/redirects, etc.). This is
# intended for local dev only; do not enable in production.
try:
    if str(os.environ.get("RELAX_DEV_SECURITY", "0")).lower() in ("1", "true", "yes"):
        ALLOWED_HOSTS = ["*"]
        # Allow local test origins
        CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]
        SESSION_COOKIE_SECURE = False
        CSRF_COOKIE_SECURE = False
        SECURE_SSL_REDIRECT = False
        SECURE_HSTS_SECONDS = 0
        SECURE_HSTS_INCLUDE_SUBDOMAINS = False
        SECURE_BROWSER_XSS_FILTER = False
        # Relax frame options so dev UIs that embed the app work
        X_FRAME_OPTIONS = "SAMEORIGIN"
except Exception:
    pass

# Tuple of people who will receive error emails.
ADMINS = (
    #     ('James McCracken', 'James.Mccracken@GraphicPkg.com'),
    ("Clemson Support", "clemson.support@GraphicPkg.com"),
)
MANAGERS = ADMINS

SERVER_ADMIN = "noreply@gchub.graphicpkg.com"
EMAIL_SUPPORT = "clemson.support@graphicpkg.com"
EMAIL_GCHUB = "gchub.clemson@graphicpkg.com"
# Error emails come from this address. GPI won't allow the default root@localhost
SERVER_EMAIL = EMAIL_SUPPORT
# Django server IP address needs to be added to relay list in Server Settings.
EMAIL_HOST = "172.23.8.16"
EMAIL_PORT = 25
EMAIL_FROM_ADDRESS = EMAIL_SUPPORT

# Where to go after we logout successfully
LOGOUT_REDIRECT_URL = "/accounts/login/?next=/"

# Any IP address in this list is able to see on-page debugging info.
# Anyone in this list is also exempt from maintenance mode.
INTERNAL_IPS = ("127.0.0.1",)

# IP:Port for the webserver
WEBSERVER_HOST = "http://172.23.8.16"
# A URL to the downloader instance of Thundercuddles. This is used to serve
# uninterrupted downloads of long stuff like tiffs.
DLOADER_URL = "http://172.23.8.59"

sys.path.insert(0, os.path.join(MAIN_PATH, "includes"))

# When this is True, any non-staff user is shown a 'down for maintenance' page.
MAINTENANCE_MODE = False

# Path to the 'bin' directory that holds scripts and binaries.
BIN_PATH = os.path.join(MAIN_PATH, "bin")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",  # Add 'postgresql_psycopg2'
        "NAME": "thundercuddles",  # Or path to database file if using sqlite3.
        "USER": "thundercuddles",  # Not used with sqlite3.
        "PASSWORD": "332088",  # Not used with sqlite3.
        "HOST": "172.23.8.73",  # Set to empty string for localhost. Not used w/sqlite3.
        "PORT": "5432",  # Set to empty string for default. Not used with sqlite3.
    }
}

# Allow switching between 'dev' and 'prod' database configurations using the
# GCHUB_DB_ENV environment variable. Default to 'dev' for safer local
# development when GCHUB_DB_ENV is not set. This keeps the original
# production values available as the 'prod' configuration.
_db_env = os.environ.get("GCHUB_DB_ENV", "dev").lower()

# Production (original) DB values preserved here as a named config.
DATABASES_RAW_PROD = {
    "ENGINE": "django.db.backends.postgresql_psycopg2",
    "NAME": "thundercuddles",
    "USER": "thundercuddles",
    "PASSWORD": "332088",
    "HOST": "172.23.8.73",
    "PORT": "5432",
}

# Dev DB values are read from environment variables if provided, falling back
# to a sensible local Postgres development database on 127.0.0.1:5432.
DATABASES_RAW_DEV = {
    "ENGINE": os.environ.get("DEV_DB_ENGINE", "django.db.backends.postgresql"),
    "NAME": os.environ.get("DEV_DB_NAME", "gchub_dev"),
    # Allow overriding the dev DB user/password/port via environment variables.
    # Default to the 'gchub' role and the PostgreSQL default port so compose
    # services and the local Postgres image work without further edits.
    "USER": os.environ.get("DEV_DB_USER", os.environ.get("POSTGRES_USER", "gchub")),
    "PASSWORD": os.environ.get(
        "DEV_DB_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "gchub")
    ),
    "HOST": os.environ.get("DEV_DB_HOST", "127.0.0.1"),
    "PORT": os.environ.get("DEV_DB_PORT", os.environ.get("POSTGRES_PORT", "5432")),
}

# Apply the selected profile. Keep the final DATABASES dict shape the same.
if _db_env == "prod":
    DATABASES = {"default": DATABASES_RAW_PROD}
else:
    # default to dev profile
    DATABASES = {"default": DATABASES_RAW_DEV}

# Safety guard: the project should not run using SQLite as the primary DB by
# accident. Third-party packages or tests may still use sqlite when they
# explicitly configure it, but the project-level default should be Postgres
# in normal development. To allow sqlite for the whole project (explicitly),
# set the environment variable ALLOW_PROJECT_SQLITE=1.
try:
    _allow_sqlite = str(os.environ.get("ALLOW_PROJECT_SQLITE", "0")).lower() in (
        "1",
        "true",
        "yes",
    )
except Exception:
    _allow_sqlite = False

if not _allow_sqlite:
    _default_engine = DATABASES.get("default", {}).get("ENGINE", "")
    if _default_engine and "sqlite3" in _default_engine:
        raise RuntimeError(
            "Project-level DATABASES is configured to use sqlite3. "
            "This is not allowed by default. To bypass, set "
            "ALLOW_PROJECT_SQLITE=1 in the environment."
        )

# Caching configuration for improved performance
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
        "TIMEOUT": 300,  # 5 minutes default timeout
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
            "CULL_FREQUENCY": 3,
        },
    }
}

# Cache settings for different types of data
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = "gchub"

# The host/port of the FS daemon. Should run on master.
FS_SERVER_HOST = "172.23.8.60"
FS_SERVER_PORT = 8000

# The ODBC DSN to the eTools MS SQL database. This must exist on the server's
# iODBC System DSN list to work.
ETOOLS_ODBC_DSN = "DSN=etoolsnew;UID=clemson-gs;PWD=havaba11"
QAD_ODBC_DSN = "DSN=datawarehouse2014;UID=fsbuser;PWD=fsbIT2008"
FSCORRUGATED_ODBC_DSN = "DSN=fscorrugated;UID=fs;PWD=fsacid"

# Path to the directory containing all of the workflow directories.
# By default, this is /Volumes.
# WORKFLOW_ROOT_DIR = '/Volumes'
WORKFLOW_ROOT_DIR = "/mnt"
# Beverage drop folder, for general uploading of files.
BEVERAGE_DROP_FOLDER = os.path.join(WORKFLOW_ROOT_DIR, "Beverage/Drop/From_Database/")
# The master storage directory for all job files.
JOBSTORAGE_DIR = os.path.join(WORKFLOW_ROOT_DIR, "JobStorage/")
# Path to the Production share.
PRODUCTION_DIR = os.path.join(WORKFLOW_ROOT_DIR, "Production")
# Path to the Backup share.
BACKUP_DIR = os.path.join(WORKFLOW_ROOT_DIR, "Backup")
# Item template root directory.
ITEM_TEMPLATE_DIR = os.path.join(PRODUCTION_DIR, "templates/")
# Ink coverage XML file directory (with trailing slash).
INK_COVERAGE_DIR = os.path.join(PRODUCTION_DIR, "ink_coverage/")
# Path to the Tiff_to_PDF script's tiff die lines.
TIFF_TO_PDF_DIES_DIR = os.path.join(PRODUCTION_DIR, "1_bit_tiff_dies_backstage/")
# Path to tiff noise hotfolder watched by the script in bin.
TIFF_NOISE_QUEUE_DIR = os.path.join(PRODUCTION_DIR, "tiff_noise_queue/")
# Path to FSB PDF Templates directory.
FSB_TEMPLATES = os.path.join(WORKFLOW_ROOT_DIR, "Templates/PDF_Templates/")
# Path to FSB production templates directory.
FSB_PROD_TEMPLATES = os.path.join(WORKFLOW_ROOT_DIR, "Templates/")
# Path to the Esko CMS data directory. This resides on the Backstage machine.
ESKO_CMS_DATA_DIR = os.path.join(WORKFLOW_ROOT_DIR, "bg_data_cms_v010", "w", "idb")
# Path to dropfolders directory.
DROPFOLDERS_DIR = os.path.join(WORKFLOW_ROOT_DIR, "DropFolders/")
# Path to the directory where we copy NX Plates
NXPLATES_DIR = os.path.join(WORKFLOW_ROOT_DIR, "Perry/")
# Path to the XML files we read to see what's been proofed by AE/FlexRIP.
PRINTED_PROOFS_DIR = os.path.join(WORKFLOW_ROOT_DIR, "Tickets/")

# Path to temporary location for Art Request before submission
ARTREQFILES_DIR = os.path.join(DROPFOLDERS_DIR, "ArtReqFiles/")

# This is needed for JMF+JDF to work right
APPEND_SLASH = False
# Backstage's JMF web connector address and port in host:port format.
JMF_GATEWAY = "172.23.8.55:4411"
# Path to append to the JMF_GATEWAY to build the JMF query URL.
JMF_GATEWAY_PATH = "/JDFP/JMF/"
# JDF hot folder root directory.
JDF_ROOT = os.path.join(PRODUCTION_DIR, "jdf_queue/")

# Fusion Flexo FTP information
FUSION_FLEXO_FTP_HOST = "exchange.graphicpkg.com"
FUSION_FLEXO_FTP_USERNAME = "fusionflexo"
FUSION_FLEXO_FTP_PASSWORD = "y;_1NNH7"

FUSION_FLEXO_FTP = {
    "HOST": "exchange.graphicpkg.com",
    "USERNAME": "fusionflexo",
    "PASSWORD": "y;_1NNH7",
    "ROOT_DIR": "togpi",
}

# Cyber Graphics FTP information
CYBER_GRAPHICS_FTP = {
    "HOST": "exchange.graphicpkg.com",
    "USERNAME": "cybergraphics",
    "PASSWORD": "TdF`vx97",
    "ROOT_DIR": "togpi",
}

# Southern Graphic FTP information
SOUTHERN_GRAPHIC_FTP = {
    "HOST": "exchange.graphicpkg.com",
    "USERNAME": "southerngraphic",
    "PASSWORD": ".;AA8iyM",
    "ROOT_DIR": "togpi",
}

# Phototype FTP information
PHOTOTYPE_FTP = {
    "HOST": "exchange.graphicpkg.com",
    "USERNAME": "phototype",
    "PASSWORD": ";3{dKqQe",
    "ROOT_DIR": "togpi",
}

TIFF_FTP = {
    "FUSION_FLEXO": FUSION_FLEXO_FTP,
    "CYBER_GRAPHICS": CYBER_GRAPHICS_FTP,
    "SOUTHERN_GRAPHIC": SOUTHERN_GRAPHIC_FTP,
    "PHOTOTYPE": PHOTOTYPE_FTP,
}

# How many days to retain old backups before deletion
BACKUP_LIFE_DAYS = 7

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "America/New_York"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(MAIN_PATH, "..", "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/media/"
# URL to the YUI installation.
YUI_URL = "http://172.23.8.16/media/yui/"

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".

# Make this unique, and don't share it with anybody.
SECRET_KEY = "jks@9EklalsSlE+29-!kldf~lkd(lkjlkfd$lk.ASd/f#42jlk8$&*89ao"

# The model to be used to hold extended user profile information.
# AUTH_PROFILE_MODULE = 'accounts.UserProfile'

# Files in these directories are loaded upon syncing and populate initial
# data in JSON or XML format. Note that applications automatically check their
# fixtures/initial_data.json file.
FIXTURE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(MAIN_PATH, "fixtures/"),
)

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"

STATIC_URL = "/static/"

# CDN Configuration - Production Only
# Only enable CDN in production (when DEBUG=False and STATIC_URL_CDN is set)
if not DEBUG and os.environ.get("STATIC_URL_CDN"):
    cdn_url = os.environ.get("STATIC_URL_CDN")
    if cdn_url:  # Ensure it's not None
        STATIC_URL = cdn_url
        # Ensure CDN URL ends with /
        if not STATIC_URL.endswith("/"):
            STATIC_URL += "/"

# Static file optimization settings for improved performance
# Enable static file compression and caching with cache busting
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Static file caching headers - cache static files for 1 year
STATIC_CACHE_TIMEOUT = 31536000  # 1 year in seconds

# Add cache control headers for static files
STATICFILES_DIRS = [
    os.path.join(MAIN_PATH, "staticfiles"),  # Include existing collected static files
    # Add any additional static file directories here if needed
]

# Enable GZip compression for static files (requires WhiteNoise or similar)
# For production, consider using a CDN or reverse proxy for static file serving
# STATIC_URL_CDN is now handled above in the main STATIC_URL configuration

# Cache versioning for cache busting
STATICFILES_USE_GZIP = True

# Production Monitoring Settings
# Only active when DEBUG=False
SLOW_REQUEST_THRESHOLD = 2.0  # seconds - requests slower than this are logged as slow
MONITORING_LOG_LEVEL = "INFO"  # Log level for monitoring messages

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",  # Add cache middleware for static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Ensure CSRF tokens are available to templates and POST handlers.
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Dev-only middleware to auto-create and login a development superuser.
    "gchub_db.middleware.dev_auto_login.DevAutoLoginMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    #'django.middleware.doc.XViewMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    "gchub_db.middleware.threadlocals.ThreadLocals",
    "gchub_db.middleware.maintenance_mode.middleware.MaintenanceModeMiddleware",
    "gchub_db.middleware.static_cache.StaticFileCacheMiddleware",  # Custom static file caching
    "django.middleware.cache.FetchFromCacheMiddleware",  # Add cache fetch middleware
)

# Production-only middleware for monitoring (only add if not DEBUG)
if not DEBUG:
    # Convert tuple to list for modification, then back to tuple
    middleware_list = list(MIDDLEWARE)
    # Add monitoring middleware at the end
    middleware_list.extend(
        [
            "gchub_db.middleware.monitoring.PerformanceMonitoringMiddleware",
            "gchub_db.middleware.monitoring.StaticFileMonitoringMiddleware",
        ]
    )
    MIDDLEWARE = tuple(middleware_list)  # type: ignore[assignment]

INSTALLED_APPS = (
    "maintenance_mode",
    "django.contrib.django_su",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.humanize",
    "django.contrib.staticfiles",
    "formtools",
    # Lots of useful extensions for Django and manage.py
    # http://code.google.com/p/django-command-extensions/
    "django_extensions",
    "gchub_db",  # Main app for management commands
    "gchub_db.apps.accounts",
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
    "gchub_db.apps.art_req",
    "gchub_db.apps.sbo",
    "gchub_db.apps.timesheet",
    "gchub_db.apps.carton_billing",
)

# Use BigAutoField as the default auto-created primary key type to satisfy
# Django system checks and modernize defaults.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

"""
-- Fedex - Account Specifics
"""
# Testing
FEDEX_TEST_ACCOUNT_NUM = "510087780"
FEDEX_TEST_METER_NUM = "118501898"
FEDEX_TEST_PASSWORD = "vuyQ28rEV4Ah6aw7F5dAMwMv3"
FEDEX_TEST_KEY = "ZyNQQFdcxUATOx9L"

# Production
FEDEX_DOMAIN = "gateway.fedex.com"
FEDEX_ACCOUNT_NUM = "248430818"
FEDEX_METER_NUM = "1301709"
# New FedEx SOAP API meter num.
FEDEX_METER_NUM2 = "101397836"
FEDEX_PASSWORD = "7A3Q73u6ygBlVKRUkyAEd9qL7"
FEDEX_KEY = "txCf12dOfHg99RCt"

"""
-- Fedex - GCHUB Constants
"""
GCHUB_COMPANY = "Graphic Packaging International"
GCHUB_PERSON = "Donna Loudermilk"
GCHUB_PHONE = "8646336000"
GCHUB_ADDRESS1 = "155 Old Greenville Hwy"
GCHUB_ADDRESS2 = "Suite 103"
GCHUB_CITY = "Clemson"
GCHUB_STATE = "SC"
GCHUB_ZIP = "29631"
GCHUB_COUNTRY_CODE = "US"

"""
-- Fedex - Printer Settings
"""
# Where is the doc-tab when looking at the label upright.
# Values: TOP, BOTTOM, NONE
FEDEX_DOCTAB_LOCATION = "BOTTOM"

# Specifies whether label stock has doc-tab on leading or trailing end of label
# as it emerges from the printer, or has none.
# Values: LEADING, TRAILING, NONE
FEDEX_LABEL_ORIENTATION = "LEADING"

# Specifies the format for the label output.
# Values: PDF, PNG4X6, ELTRON, ZEBRA, UNIMARK
# FEDEX_LABEL_IMG_TYPE = "PNG4X6"
FEDEX_LABEL_IMG_TYPE = "ELTRON"

# Label type. Not documented well in the Fedex API, no idea what it does or
# what other possible values there are.
FEDEX_LABEL_TYPE = "2DCOMMON"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
            # Always use forward slashes, even on Windows.
            # Don't forget to use absolute paths, not relative paths.
            os.path.join(MAIN_PATH, "html"),
            os.path.join(MAIN_PATH, "email_templates"),
        ],
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "django.contrib.auth.context_processors.auth",
                "gchub_db.includes.extra_context.common_urls",
            ],
            # Register legacy template tags as builtins so old templates work
            "builtins": ["gchub_db.templatetags.legacy_tags"],
            "loaders": [
                # List of callables that know how to import templates from various
                # sources.
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]
