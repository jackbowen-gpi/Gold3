"""
Base settings that are common across all environments.
This file contains non-sensitive configuration that can be safely committed to version control.
"""

import os
from typing import Any, Dict, cast

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

DEBUG = True  # Will be overridden in production

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

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

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gchub_db.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
            os.path.join(BASE_DIR, "html"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gchub_db.wsgi.application"

# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "gchub_dev",
        "USER": "gchub",
        "PASSWORD": "gchub",
        "HOST": "127.0.0.1",
        "PORT": "5438",
    }
}

# =============================================================================
# AUTHENTICATION & AUTHORIZATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# =============================================================================
# MEDIA FILES
# =============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# =============================================================================
# OTHER SETTINGS
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_ID = 1

# Cache settings
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Session settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400  # 24 hours

# CSRF settings
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False

# Security settings (will be overridden in production)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# =============================================================================
# WORKFLOW AND FILE SYSTEM SETTINGS
# =============================================================================

# Path to the directory containing all of the workflow directories.
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

# The host/port of the FS daemon. Should run on master.
FS_SERVER_HOST = "172.23.8.60"
FS_SERVER_PORT = 8000

# IP:Port for the webserver
WEBSERVER_HOST = "http://172.23.8.16"

# A URL to the downloader instance of Thundercuddles. This is used to serve
# uninterrupted downloads of long stuff like tiffs.
DLOADER_URL = "http://172.23.8.59"

# URL to the YUI installation.
YUI_URL = "http://172.23.8.16/media/yui/"

# How many days to retain old backups before deletion
BACKUP_LIFE_DAYS = 7

# Local time zone for this installation.
TIME_ZONE = "America/New_York"

# Language code for this installation.
LANGUAGE_CODE = "en-us"

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# URL that handles the media served from MEDIA_ROOT.
MEDIA_URL = "/media/"

# URL prefix for admin media -- CSS, JavaScript and images.
STATIC_URL = "/static/"

# Absolute path to the directory that holds static files.
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Additional locations of static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Static file optimization settings
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Cache settings for improved performance
CACHES = cast(
    Dict[str, Any],
    {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "django_cache_table",
            "TIMEOUT": 300,  # 5 minutes default timeout
            "OPTIONS": {
                "MAX_ENTRIES": 1000,
                "CULL_FREQUENCY": 3,
            },
        }
    },
)

# Cache settings for different types of data
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = "gchub"

# Any IP address in this list is able to see on-page debugging info.
INTERNAL_IPS = ["127.0.0.1"]

# Where to go after we logout successfully
LOGOUT_REDIRECT_URL = "/accounts/login/?next=/"

# Files in these directories are loaded upon syncing and populate initial
# data in JSON or XML format.
FIXTURE_DIRS = [
    os.path.join(BASE_DIR, "fixtures"),
]

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"

# The model to be used to hold extended user profile information.
# AUTH_PROFILE_MODULE = 'accounts.UserProfile'

# Tuple of people who will receive error emails.
ADMINS = [
    ("Clemson Support", "clemson.support@GraphicPkg.com"),
]

MANAGERS = ADMINS

SERVER_ADMIN = "noreply@gchub.graphicpkg.com"
EMAIL_SUPPORT = "clemson.support@graphicpkg.com"
EMAIL_GCHUB = "gchub.clemson@graphicpkg.com"

# Error emails come from this address.
SERVER_EMAIL = EMAIL_SUPPORT

# Django server IP address needs to be added to relay list in Server Settings.
EMAIL_HOST = "172.23.8.16"
EMAIL_PORT = 25
EMAIL_FROM_ADDRESS = EMAIL_SUPPORT

# When this is True, any non-staff user is shown a 'down for maintenance' page.
MAINTENANCE_MODE = False

# Path to the 'bin' directory that holds scripts and binaries.
BIN_PATH = os.path.join(BASE_DIR, "bin")
