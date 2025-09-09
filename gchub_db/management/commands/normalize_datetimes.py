
from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime

# This management command will scan specified models and fields for naive
# datetimes and convert them to timezone-aware datetimes in UTC.
# Usage: manage.py normalize_datetimes

TARGETS = [
    # (app_label, model_name, field_name)
    ("news", "CodeChange", "creation_date"),
    ("workflow", "JobLog", "event_time"),
]


class Command(BaseCommand):
    help = "Normalize naive datetimes in DB to timezone-aware UTC datetimes"

    def handle(self, *args, **options):
        from django.apps import apps

        for app_label, model_name, field_name in TARGETS:
            model = apps.get_model(app_label, model_name)
            if model is None:
                self.stdout.write(
                    self.style.WARNING(f"Model {app_label}.{model_name} not found")
                )
                continue
            qs = model.objects.all()
            count = 0
            for obj in qs:
                dt = getattr(obj, field_name, None)
                if dt is None:
                    continue
                if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                    # naive -> make aware in UTC
                    aware = timezone.make_aware(dt, timezone=datetime.timezone.utc)
                    setattr(obj, field_name, aware)
                    obj.save(update_fields=[field_name])
                    count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated {count} rows on {app_label}.{model_name}.{field_name}"
                )
            )
