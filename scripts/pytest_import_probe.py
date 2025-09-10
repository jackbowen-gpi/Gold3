import os
import sys
import traceback

print("CWD:", os.getcwd())
print("sys.path[0:6]=", sys.path[0:6])
print("env PYTHONPATH=", os.environ.get("PYTHONPATH"))

# Ensure Django settings module matches how
# pytest will run it (legacy project uses repo-root shim `settings`)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))

try:
    import django

    print("django version=", django.get_version())
except Exception:
    print("failed importing django:")
    traceback.print_exc()

print("\nAttempting to import gchub_db.apps.fedexsys.test_models")
try:
    from importlib import import_module

    import_module("gchub_db.apps.fedexsys.test_models")
    print("IMPORT OK")
except Exception:
    traceback.print_exc()
