"""Lazy wrapper scheduler to delay importing django_celery_beat until runtime.

Celery imports the scheduler module at import time; some third-party schedulers
import Django models at module import-time which raises AppRegistryNotReady if
django.setup() hasn't run. This wrapper defines a lightweight class that only
imports and instantiates the real DatabaseScheduler inside __init__, after the
Django app registry is ready.
"""

from __future__ import annotations


class LazyDatabaseScheduler:
    """
    Proxy scheduler that instantiates
    django_celery_beat.schedulers.DatabaseScheduler lazily.
    """

    def __init__(self, *args, **kwargs):
        # Import the real scheduler only when the scheduler is instantiated.
        from importlib import import_module

        module = import_module("django_celery_beat.schedulers")
        RealScheduler = getattr(module, "DatabaseScheduler")
        self._impl = RealScheduler(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._impl, name)

    # Support attribute lookup that some callers use directly
    def __dir__(self):
        return dir(self._impl)
