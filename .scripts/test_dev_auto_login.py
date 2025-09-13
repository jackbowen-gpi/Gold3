"""
Module .scripts\test_dev_auto_login.py
"""

import os
import sys
import traceback

sys.path.insert(0, os.getcwd())
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

import django

django.setup()
print("django setup complete")

from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from gchub_db.middleware.dev_auto_login import DevAutoLoginMiddleware

rf = RequestFactory()
req = rf.get("/")

# Attach session and auth middleware to the request so login() works
SessionMiddleware(lambda r: None).process_request(req)
AuthenticationMiddleware(lambda r: None).process_request(req)

mw = DevAutoLoginMiddleware(lambda r: r)
try:
    resp = mw(req)
except Exception:
    print("middleware raised:")
    traceback.print_exc()

user = getattr(req, "user", None)
if user and getattr(user, "is_authenticated", False):
    print("DEV ADMIN logged in:", user.username, "is_superuser=", user.is_superuser)
else:
    print("DEV ADMIN NOT logged in")
    traceback.print_stack()
