import json

from django.core.management.base import BaseCommand
from django.db.models import Count


class Command(BaseCommand):
    help = "Dump job counts and samples (dev helper)"

    def handle(self, *args, **options):
        # Import via full package path to avoid ModuleNotFoundError when
        # this command is executed from manage.py in diverse environments.
        from gchub_db.apps.workflow.models import Job

        qs = Job.objects.all()
        self.stdout.write(f"JOB_COUNT: {qs.count()}")
        self.stdout.write("BY_WORKFLOW:")
        for r in qs.values("workflow__name").annotate(cnt=Count("id")):
            self.stdout.write(json.dumps(r, default=str))
        self.stdout.write("SAMPLE (up to 50):")
        for j in qs.order_by("-id")[:50]:
            d = {
                "id": j.id,
                "name": (j.name[:120] if j.name else None),
                "status": j.status,
                "workflow": (j.workflow.name if j.workflow else None),
                "artist": (j.artist.username if getattr(j, "artist", None) else None),
                "salesperson": (j.salesperson.username if getattr(j, "salesperson", None) else None),
                "items_in_job": getattr(j, "items_in_job", None),
            }
            self.stdout.write(json.dumps(d, default=str))
