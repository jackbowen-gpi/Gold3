"""Lazy shim to forward attribute access to the sibling ``views.py`` file.

We intentionally avoid importing the sibling module at package import time
because that file imports Django models and will trigger settings access.
Instead, implement a module-level __getattr__ that loads the real module on
first attribute access (e.g. when Django resolves a view during request
handling).
"""

import os
import importlib.util

_real_mod = None


def _sibling_path():
    root = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(root, "..", "views.py"))


def _load_real_module():
    """Load the sibling views.py as a separate module and cache it.

    This is executed lazily when an attribute on this package is requested.
    Errors are propagated so callers (e.g. Django request handling) see the
    underlying ImportError / ImproperlyConfigured if settings are missing.
    """
    global _real_mod
    if _real_mod is not None:
        return _real_mod

    path = _sibling_path()
    if not os.path.exists(path):
        raise ImportError("sibling views.py not found")

    spec = importlib.util.spec_from_file_location(
        "gchub_db.apps.accounts._views_py", path
    )
    mod = importlib.util.module_from_spec(spec)
    # Execute the module in its own namespace.
    spec.loader.exec_module(mod)
    _real_mod = mod
    return mod


def __getattr__(name: str):
    # Forward attribute access to the loaded views.py module.
    mod = _load_real_module()
    try:
        return getattr(mod, name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    # Provide a helpful dir() that includes attributes from the real module if
    # available.
    result = list(globals().keys())
    try:
        mod = _load_real_module()
    except Exception:
        return sorted(result)
    for k in dir(mod):
        if k not in result:
            result.append(k)
    return sorted(result)
