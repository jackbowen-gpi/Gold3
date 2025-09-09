import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django

django.setup()
import pprint

from django.conf import settings

pprint.pprint(settings.DATABASES)
