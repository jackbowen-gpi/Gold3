import os
import sys
import traceback

print("sys.path[0:6]=", sys.path[0:6])
print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))
try:
    import importlib

    print("importing gchub_db.conftest")
    m = importlib.import_module("gchub_db.conftest")
    print("imported conftest:", m)
except Exception:
    traceback.print_exc()
    sys.exit(2)
print("done")
