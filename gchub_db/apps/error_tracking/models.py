"""Error tracking application"""

from django.contrib.auth.models import User
from django.db import models

from gchub_db.apps.workflow.models import Item, Job

ERROR_STAGES = (
    ("1", "Prepress"),
    ("2", "Films"),
    ("3", "Plates"),
    ("4", "Press"),
    ("5", "Forming"),
    ("6", "Shipped"),
)


class Error(models.Model):
    """A reported error tied to a job or an item."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="job_error_set")
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="item_error_set",
        blank=True,
        null=True,
    )
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    reported_date = models.DateTimeField("Error Date", auto_now_add=True)
    stage = models.CharField(choices=ERROR_STAGES, max_length=4)
    description = models.TextField()

    def __str__(self):
        return str(self.job) + " - " + str(self.item)
