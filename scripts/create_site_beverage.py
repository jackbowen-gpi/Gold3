"""
Ensure a local 'Beverage' Site exists using Django ORM (uses configured DATABASES).

This avoids direct sqlite usage and will work with Postgres or whatever DB is configured
via settings/local_settings/env vars.
"""

import os
import sys

# Run from repository root (manage.py directory)
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

import django

django.setup()

from django.contrib.sites.models import Site

site, created = Site.objects.get_or_create(domain="localhost", defaults={"name": "Beverage"})
if created:
    print("Inserted Beverage site (domain=localhost)")
else:
    # Ensure name is set
    if site.name != "Beverage":
        site.name = "Beverage"
        site.save()
        print("Updated Beverage site name")
    else:
        print("Beverage site already exists, id=", site.id)
