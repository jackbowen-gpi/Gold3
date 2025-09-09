import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.gchub_db.test_settings")
print("DJANGO_SETTINGS_MODULE =", os.environ["DJANGO_SETTINGS_MODULE"])
# ensure repo root on sys.path
sys.path.insert(0, os.path.abspath("."))
print("sys.path[0]=", sys.path[0])
import django

print("django version", django.get_version())
try:
    django.setup()
    print("django.setup OK")
except Exception as e:
    print("django.setup failed:", e)

from importlib import import_module

try:
    mod = import_module("gchub_db.test_urls")
    print("imported gchub_db.test_urls OK")
    print("test_urls module file:", getattr(mod, "__file__", None))
except Exception as e:
    print("import gchub_db.test_urls failed:", e)

# try include resolution
from django.urls import include

try:
    include("gchub_db.apps.workflow.urls")
    print("django.include OK")
except Exception as e:
    print("django.include failed:", e)
