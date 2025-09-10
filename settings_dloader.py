"""This is used for the configuration of the downloader instance."""  # type: ignore

# This imports a bunch of common stuff.
from settings_common import *  # noqa: F403  # type: ignore
from typing import Any, List, TYPE_CHECKING

# Declare a module-level annotation so mypy treats `MIDDLEWARE` as
# a `list[str]` in this module. This intentionally shadows the imported
# symbol's runtime value for type checking; silence the redefinition
# warning since the import provides the runtime value.
MIDDLEWARE: List[str]  # type: ignore[no-redef]

# Provide a mypy-friendly runtime coercion for MIDDLEWARE. Some configs
# define MIDDLEWARE as a tuple in settings_common; runtime code expects a
# mutable list. We read the value from globals() and then replace the
# module-level name with a list while keeping mypy quiet using per-line
# ignores where necessary.
# Declare a mypy-friendly annotation for MIDDLEWARE so its static type is
# consistently a list[str] across modules that import it.
if not TYPE_CHECKING:
    _MIDDLEWARE: Any = globals().get("MIDDLEWARE")
    if _MIDDLEWARE is not None:
        if isinstance(_MIDDLEWARE, tuple):
            # Convert to list for runtime code; write back into module globals
            globals()["MIDDLEWARE"] = list(_MIDDLEWARE)  # type: ignore
        else:
            globals()["MIDDLEWARE"] = _MIDDLEWARE  # type: ignore

# We'll use the same urls file as primary GOLD, since this is
# another cloned instance.
ROOT_URLCONF = "gchub_db.urls"

SITE_ID = 2

try:
    from local_settings import *  # noqa: F403
except ImportError:
    pass

# Legacy compatibility: MIDDLEWARE is now handled above in a mypy-safe way
