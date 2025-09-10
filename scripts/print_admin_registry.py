#!/usr/bin/env python
"""Print Django admin registry (app_label -> model names) for debugging."""

import os
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django

django.setup()

from django.contrib import admin

apps = {}
for m in admin.site._registry.keys():
    apps.setdefault(m._meta.app_label, []).append(m._meta.model_name)

print(json.dumps({k: sorted(v) for k, v in apps.items()}, indent=2))
print("django_celery_beat_present:", "django_celery_beat" in apps)
