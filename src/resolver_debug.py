"""
Module src\resolver_debug.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django

try:
    django.setup()
    from django.conf import settings
    from django.urls import get_resolver, resolve

    print("ROOT_URLCONF=", getattr(settings, "ROOT_URLCONF", None))
    print("DEBUG=", getattr(settings, "DEBUG", None))

    try:
        r = resolve("/")
        print(
            "RESOLVED: func=%r, url_name=%r, view_name=%r"
            % (
                getattr(r, "func", None),
                getattr(r, "url_name", None),
                getattr(r, "view_name", None),
            )
        )
    except Exception as e:
        print("RESOLVE_ERROR:", type(e).__name__, e)

    res = get_resolver(None)
    print("TOP_PATTERNS_COUNT=", len(res.url_patterns))
    for i, p in enumerate(res.url_patterns[:40]):
        try:
            name = getattr(p, "name", None)
        except Exception:
            name = None
        try:
            pat = getattr(p, "pattern", p)
        except Exception:
            pat = p
        print(i, type(p).__name__, "name=", name, "repr=", repr(p))
except Exception as exc:
    print("DJANGO_SETUP_ERROR", exc)
