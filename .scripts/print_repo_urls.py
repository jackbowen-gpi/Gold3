r"""
Module .scripts\print_repo_urls.py
"""

import os
import sys
import traceback

sys.path.insert(0, os.getcwd())
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

print("PYTHONPATH[0]", sys.path[0])

import django

try:
    django.setup()
    print("django.setup ok")
except Exception:
    print("django.setup failed")
    traceback.print_exc()

try:
    import config.urls as repo_urls

    patterns = getattr(repo_urls, "urlpatterns", None)
    if patterns is None:
        print("Imported urls but no urlpatterns found")
    else:
        print("Imported repo-root urls, urlpatterns len=", len(patterns))
        for i, p in enumerate(patterns[:30]):
            try:
                name = getattr(p, "name", None)
            except Exception:
                name = "<err>"
            print(i, type(p), "name=", name, "repr=", p)
except Exception:
    print("EXCEPTION importing repo-root urls:")
    traceback.print_exc()
