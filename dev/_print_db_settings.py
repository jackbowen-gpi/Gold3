import json
import os

import django
from django.conf import settings

# Use the package settings module to match manage.py and restart_app behavior
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

django.setup()

print(json.dumps(settings.DATABASES))
