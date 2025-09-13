import importlib
import os
import sys

sys.path.insert(0, "C:/Dev/Gold")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.gchub_db.test_settings")
import django
from django.conf import settings

print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))
try:
    django.setup()
except Exception as e:
    print("django.setup() failed:", type(e).__name__, e)
    # Try to import each installed app module
    for app in getattr(settings, "INSTALLED_APPS", []):
        try:
            importlib.import_module(app)
            print("OK", app)
        except Exception as e2:
            print("ERR", app, type(e2).__name__, e2)
