"""This is used for the configuration of the downloader instance."""

# This imports a bunch of common stuff.
from config.settings_common import *  # noqa: F403  # type: ignore
from typing import TYPE_CHECKING

# Handle MIDDLEWARE type compatibility for mypy
if not TYPE_CHECKING:
    # Runtime: ensure MIDDLEWARE is a list for mutability
    try:
        if isinstance(MIDDLEWARE, tuple):  # type: ignore  # noqa: F405
            MIDDLEWARE = list(MIDDLEWARE)  # type: ignore  # noqa: F405
    except NameError:
        # MIDDLEWARE might not be defined in some configurations
        pass

# We'll use the same urls file as primary GOLD, since this is
# another cloned instance.
ROOT_URLCONF = "gchub_db.urls"

SITE_ID = 2

try:
    from config.local_settings import *  # noqa: F403  # type: ignore
except ImportError:
    pass

# Legacy compatibility: MIDDLEWARE is now handled above in a mypy-safe way
