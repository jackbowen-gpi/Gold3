"""
Administrative log model. This records errors and information that is helpful
in diagnosing problems and monitoring things.
"""

from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.db import models

# General useful information, nothing to be alarmed about.
LOG_TYPE_GENERAL_INFO = 0
# Things that may be cause for concern, but aren't show-stoppers.
LOG_TYPE_WARNING = 5
# Critical failures and problems.
LOG_TYPE_ERROR = 10

# Assembled choices tuple
LOG_TYPES = (
    (LOG_TYPE_GENERAL_INFO, "General Information"),
    (LOG_TYPE_WARNING, "Warnings"),
    (LOG_TYPE_ERROR, "Error"),
)


class AdminLogCreatorManager(models.Manager):
    """
    Used to provide shortcuts to creating new log entries. For example:

    AdminLog.create.warning('Some message')
    AdminLog.create.error('Some message', origin=some_job)
    """

    def new_entry(self, log_type, message, origin=None):
        """Creates a new log entry of the desired type."""
        AdminLog = ContentType.objects.get(app_label="admin_log", model="adminlog").model_class()

        # It's silly we have to do this, but apparently the origin field can't
        # accept a None argument through the constructor.
        if origin:
            new_log = AdminLog(type=log_type, log_text=message, origin=origin)
        else:
            new_log = AdminLog(type=log_type, log_text=message)

        new_log.save()
        return new_log

    def warning(self, message, origin=None):
        """Creates a new warning message."""
        return self.new_entry(LOG_TYPE_WARNING, message, origin)

    def error(self, message, origin=None):
        """Creates a new error message."""
        return self.new_entry(LOG_TYPE_ERROR, message, origin)

    def info(self, message, origin=None):
        """Creates a new informative message."""
        return self.new_entry(LOG_TYPE_GENERAL_INFO, message, origin)


class AdminLog(models.Model):
    """An administrative log entry."""

    # Stores the ID of the model the 'origin' field is relating to.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    # Stores the ID of the object that the 'origin' field is relating to.
    object_id = models.PositiveIntegerField(blank=True, null=True)
    # Where the error came from, can be just about any model class.
    origin = fields.GenericForeignKey("content_type", "object_id")
    # See LOG_TYPES choices tuple for details.
    type = models.IntegerField(choices=LOG_TYPES)
    log_text = models.TextField()
    event_time = models.DateTimeField("Date", auto_now_add=True)

    # New log creation manager
    create = AdminLogCreatorManager()

    class Meta:
        verbose_name = "Admin Log"
        verbose_name_plural = "Admin Logs"

    def get_absolute_url(self):
        """Returns the absolute URL of the origin object (if there is one)."""
        if self.origin:
            return self.origin.get_absolute_url()
        return None
