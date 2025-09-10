"""Local shim module named `api` to satisfy legacy imports during local development.

This module intentionally provides a minimal surface so `import api` does
not raise ModuleNotFoundError. It's a temporary workaround — replace or
remove when the real top-level `api` package is available.
"""

# Minimal configuration placeholder used by various legacy modules.
STUB = True


def get_setting(name, default=None):
    """Return a default or None for requested names; keeps legacy callers happy."""
    return default


__all__ = ["STUB", "get_setting"]
