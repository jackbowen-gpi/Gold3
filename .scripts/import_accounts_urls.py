r"""
Module .scripts\import_accounts_urls.py
"""

import os
import sys
import traceback

sys.path.insert(0, os.getcwd())
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))

import django

try:
    django.setup()
    print("django.setup ok")
except Exception:
    print("django.setup failed")
    traceback.print_exc()

try:
    import gchub_db.apps.accounts.urls as acc_urls

    print(
        "imported accounts.urls, urlpatterns len",
        len(getattr(acc_urls, "urlpatterns", [])),
    )
except Exception:
    print("EXCEPTION importing accounts.urls:")
    traceback.print_exc()
