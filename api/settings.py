"""
Minimal settings shim for `api.settings` used by some legacy modules.

This file is intentionally minimal. Add values as needed when the import
fails for a specific variable.
"""

# Example placeholder values. Real deployments should provide the proper
# `api` package and settings.
DEBUG = True
DATABASES = {}


def get(name, default=None):
    """
    Return a settings value by name with an optional default.

    This helper mirrors a tiny subset of Django's settings access patterns
    used by legacy modules that import `api.settings`.
    """
    return globals().get(name, default)
