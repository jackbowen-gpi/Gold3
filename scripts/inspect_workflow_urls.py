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

    m = importlib.import_module("gchub_db.apps.workflow.urls")
    print("imported gchub_db.apps.workflow.urls OK")
    print("Found urlpatterns length:", len(m.urlpatterns))
    names = []
    for u in m.urlpatterns:
        name = getattr(u, "name", None)
        if name:
            names.append(name)
    print("Sample names:", names[:40])
    for u in m.urlpatterns:
        if getattr(u, "name", None) == "todo_list":
            print("FOUND todo_list pattern:", u, getattr(u, "pattern", None))
            break
    else:
        print("todo_list not found in workflow urlpatterns")
except Exception:
    import traceback

    print("import error:")
    traceback.print_exc()
