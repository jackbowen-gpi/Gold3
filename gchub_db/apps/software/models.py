"""Stores software data for Clemson."""

from django.db import models


class Software(models.Model):
    """A contact in the address book."""

    application_name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=255, blank=True)
    vendor = models.CharField(max_length=255, blank=True)
    os = models.CharField(max_length=255, blank=True)
    installation_location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["application_name"]
        verbose_name_plural = "Software"

    def __str__(self):
        """String representation."""
        return self.application_name
