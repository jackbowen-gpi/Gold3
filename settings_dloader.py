"""This is used for the configuration of the downloader instance."""

# This imports a bunch of common stuff.
from settings_common import *  # noqa: F403

# We'll use the same urls file as primary GOLD, since this is
# another cloned instance.
ROOT_URLCONF = "gchub_db.urls"

SITE_ID = 2

try:
    from local_settings import *  # noqa: F403
except ImportError:
    pass
