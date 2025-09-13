"""Print Django DATABASES configured at runtime."""

import os
import pathlib
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

import django
from django.conf import settings

try:
    django.setup()
except Exception:
    print("Django setup failed:")
    import traceback

    traceback.print_exc()
    sys.exit(2)

import json

print(json.dumps(settings.DATABASES, indent=2))
