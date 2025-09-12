"""Carton Billing/Invoicing Application."""

from django.contrib.auth.models import User
from django.db import models


class CartonSapEntry(models.Model):
    """Carton SAP billing entries. Items that need to be entered into SAP"""

    # Importing the Job model name as a string to avoid a circular import.
    job = models.ForeignKey("workflow.Job", on_delete=models.CASCADE)
    creation_date = models.DateTimeField("Date Created", auto_now_add=True)
    qad_entry_date = models.DateField("QAD Entry Date", blank=True, null=True)
    qad_entry_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        """String representation."""
        return "%s" % (self.job)
