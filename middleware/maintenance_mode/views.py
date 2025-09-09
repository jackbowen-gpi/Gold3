# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect

try:
    from maintenance_mode import core as _maintenance_core
except Exception:
    _maintenance_core = None


def maintenance_mode_off(request):
    # Only attempt to call the optional maintenance_mode API when available
    if (
        _maintenance_core is not None
        and getattr(request, "user", None)
        and getattr(request.user, "is_superuser", False)
    ):
        try:
            _maintenance_core.set_maintenance_mode(False)
        except Exception:
            # Best-effort: don't raise during imports or runtime in dev mode
            pass

    return HttpResponseRedirect("/")


def maintenance_mode_on(request):
    if (
        _maintenance_core is not None
        and getattr(request, "user", None)
        and getattr(request.user, "is_superuser", False)
    ):
        try:
            _maintenance_core.set_maintenance_mode(True)
        except Exception:
            pass

    return HttpResponseRedirect("/")
