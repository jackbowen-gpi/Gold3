import os
import sys
import traceback

# Make sure we import the project package from the inner package path so
# there is a single resolution for `gchub_db` during this probe.
INNER = r"C:\Dev\Gold\gchub_db"
if INNER not in sys.path:
    sys.path.insert(0, INNER)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

print("sys.path[0] ->", sys.path[0])
print("DJANGO_SETTINGS_MODULE ->", os.environ.get("DJANGO_SETTINGS_MODULE"))

try:
    import django

    print("django version ->", django.get_version())
    django.setup()
    from django.conf import settings

    print("settings module ->", getattr(settings, "__file__", None))
    print("INSTALLED_APPS count ->", len(getattr(settings, "INSTALLED_APPS", [])))
except Exception:
    print("django.setup() raised:")
    traceback.print_exc()

print("\nAttempting to import gchub_db.apps.fedexsys.test_models")
try:
    import importlib

    m = importlib.import_module("gchub_db.apps.fedexsys.test_models")
    print("Imported:", getattr(m, "__file__", m))
except Exception:
    traceback.print_exc()
