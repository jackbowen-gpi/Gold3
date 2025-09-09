import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.test_settings")

import django

try:
    django.setup()
except Exception as e:
    print("django.setup() failed:", type(e), e)

try:
    import importlib

    mod = importlib.import_module("gchub_db.apps.workflow.urls")
    print("imported gchub_db.apps.workflow.urls OK")
    up = getattr(mod, "urlpatterns", None)
    print("urlpatterns type:", type(up), "len:", len(up) if up is not None else "None")
    names = []
    if up:
        for p in up[:200]:
            try:
                names.append(getattr(p, "name", None))
            except Exception as e:
                names.append(("err", repr(e)))
    print("first 200 names:", names[:200])
except Exception:
    import traceback

    print("import error:")
    traceback.print_exc()
