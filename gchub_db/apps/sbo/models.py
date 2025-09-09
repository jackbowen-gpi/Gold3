"""SBO models used for Safety Behavior Observations Program"""

from django.contrib.auth.models import User
from django.db import models

from gchub_db.middleware import threadlocals

risk_safe_choices = (
    ("at_risk", "At Risk"),
    ("safe", "Safe"),
)


class SBO(models.Model):
    """A single observation of safety"""

    date_added = models.DateTimeField("Date Added", auto_now_add=True)
    date_observed = models.DateTimeField("Date Observed")
    observer = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="observer"
    )
    observed = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="observed"
    )

    task = models.TextField(max_length=500)
    behavior = models.TextField(max_length=500)
    behavior_type = models.CharField(choices=risk_safe_choices, max_length=7)
    reason = models.TextField(max_length=500)

    communication = models.BooleanField(default=False)
    describe_communication = models.TextField(max_length=500, blank=True, null=True)
    additional_comments = models.TextField(
        max_length=500,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["date_added"]

    def __str__(self):
        return str(self.behavior_type)

    def save(self):
        """Overriding the SBO's standard save() so we can save current user"""
        current_user = threadlocals.get_current_user()
        if self.observer is None:
            self.observer = current_user
        return super(SBO, self).save()
