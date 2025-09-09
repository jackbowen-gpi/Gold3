import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django

django.setup()
from workflow.models import Job

print("workflow_job count:", Job.objects.count())
print("Latest 5 jobs:")
for j in Job.objects.order_by("-id")[:5]:
    print(
        j.id,
        getattr(j, "name", None),
        getattr(j, "workflow_id", None),
        getattr(j, "is_deleted", None),
        getattr(j, "status", None),
    )
