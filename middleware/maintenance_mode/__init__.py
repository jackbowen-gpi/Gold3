# -*- coding: utf-8 -*-
"""Lightweight shim for the optional `maintenance_mode` package.

Some deployments don't install the 3rd-party `maintenance_mode` package.
Guard the import so that importing this module doesn't raise during project
startup (which would allow top-level URL imports to fail). If the package
is missing, expose a sensible default version string.
"""

try:
    from maintenance_mode.version import __version__
except Exception:
    # Optional dependency missing — expose a safe default value and avoid
    # raising at import time so repo-level URLConf can be imported.
    __version__ = "0.0.0"
