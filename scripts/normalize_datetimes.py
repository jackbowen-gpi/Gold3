"""Normalize naive datetimes in DB to timezone-aware UTC datetimes.

Run from repo root with the project venv activated:
  .\.venv\Scripts\python.exe scripts\normalize_datetimes.py

This script does an in-place update. BACKUP your DB before running.
"""

import datetime as _dt
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
# Ensure the project root is on sys.path so Django can import the project package
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import django

django.setup()

from django.apps import apps
from django.utils import timezone

# Models/fields to normalize: (app_label, model_name, field_name)
TARGETS = [
    ("news", "CodeChange", "creation_date"),
    ("joblog", "JobLog", "event_time"),
]


def make_aware_utc(dt):
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is not None and dt.tzinfo.utcoffset(dt) is not None:
        return dt
    try:
        return timezone.make_aware(dt, timezone=_dt.timezone.utc)
    except Exception:
        # Fallback: attach UTC tzinfo
        return dt.replace(tzinfo=_dt.timezone.utc)


def main():
    total = 0
    for app_label, model_name, field_name in TARGETS:
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            print(f"Model {app_label}.{model_name} not found; skipping")
            continue
        qs = model.objects.all()
        updated = 0
        for obj in qs:
            dt = getattr(obj, field_name, None)
            if dt is None:
                continue
            if getattr(dt, "tzinfo", None) is None or dt.tzinfo.utcoffset(dt) is None:
                aware = make_aware_utc(dt)
                setattr(obj, field_name, aware)
                try:
                    obj.save(update_fields=[field_name])
                except Exception as e:
                    print(
                        f"Failed to save {app_label}.{model_name} id={getattr(obj,'id',None)}: {e}"
                    )
                    continue
                updated += 1
        total += updated
        print(f"Updated {updated} rows on {app_label}.{model_name}.{field_name}")
    print(f"Normalization complete. Total rows updated: {total}")


if __name__ == "__main__":
    main()
