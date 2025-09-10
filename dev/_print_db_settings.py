import json
import os

# Use the package settings module to match manage.py and restart_app behavior
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django

django.setup()
from django.conf import settings  # noqa: E402

print(json.dumps(settings.DATABASES))
