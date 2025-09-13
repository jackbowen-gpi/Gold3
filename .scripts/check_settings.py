r"""
Module .scripts\check_settings.py
"""

import os
import sys

sys.path.insert(0, os.getcwd())
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
import django

try:
    django.setup()
except Exception as e:
    print("django.setup() failed:", repr(e))
    raise
from django.conf import settings

print("DEBUG =", settings.DEBUG)
print("MIDDLEWARE (first 20):")
for i, m in enumerate(getattr(settings, "MIDDLEWARE", [])[:20]):
    print(i, m)
