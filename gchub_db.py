"""
Compatibility alias module to satisfy imports of `gchub_db.gchub_db`.

This repository historically uses a nested package layout and some scripts
or tests import `gchub_db.gchub_db`. Creating this alias module makes that
import succeed by loading the inner package and exposing it under the
expected dotted name.

This is an aggressive compatibility shim; keep it only until callers are
updated to the modern import form.
"""

import importlib
import importlib.util
import os
import sys
import types

# Locate inner package: repo_root/gchub_db
_this = os.path.dirname(os.path.abspath(__file__))
_inner_pkg_init = os.path.join(_this, "gchub_db", "__init__.py")

if os.path.exists(_inner_pkg_init):
    try:
        # Prefer normal import if sys.path already allows it
        pkg = importlib.import_module("gchub_db")
    except Exception:
        # Load inner package by path to ensure correct module object
        spec = importlib.util.spec_from_file_location("gchub_db", _inner_pkg_init)
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["gchub_db"] = pkg
        spec.loader.exec_module(pkg)

    # Create an alias module object for gchub_db.gchub_db
    alias_name = "gchub_db.gchub_db"
    if alias_name not in sys.modules:
        alias = types.ModuleType(alias_name)
        # copy attributes to alias so it behaves like the package
        for k, v in pkg.__dict__.items():
            alias.__dict__[k] = v
        alias.__path__ = getattr(pkg, "__path__", [])
        sys.modules[alias_name] = alias
