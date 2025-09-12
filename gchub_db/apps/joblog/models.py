"""
Module gchub_db\apps\\joblog\\models.py
"""

from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import signals

from gchub_db.apps.joblog.app_defs import (
    JOBLOG_TYPE_BILLING,
    JOBLOG_TYPE_CRITICAL,
    JOBLOG_TYPE_ERROR,
    JOBLOG_TYPE_FEDEX,
    JOBLOG_TYPE_FTP,
    JOBLOG_TYPE_ITEM_ADDED,
    JOBLOG_TYPE_ITEM_APPROVED,
    JOBLOG_TYPE_ITEM_DELETED,
    JOBLOG_TYPE_ITEM_FILED_OUT,
    JOBLOG_TYPE_ITEM_FORECAST,
    JOBLOG_TYPE_ITEM_PREFLIGHT,
    JOBLOG_TYPE_ITEM_PROOFED_OUT,
    JOBLOG_TYPE_ITEM_REJECTED,
    JOBLOG_TYPE_ITEM_REVISION,
    JOBLOG_TYPE_ITEM_SAVED,
    JOBLOG_TYPE_JDF,
    JOBLOG_TYPE_JDF_ERROR,
    JOBLOG_TYPE_JOBLOG_DELETED,
    JOBLOG_TYPE_JOB_CREATED,
    JOBLOG_TYPE_JOB_SAVED,
    JOBLOG_TYPE_NOTE,
    JOBLOG_TYPE_PRODUCTION_EDITED,
    JOBLOG_TYPE_WARNING,
    JOBLOG_TYPES,
)
from gchub_db.middleware import threadlocals


class JobLog(models.Model):
    """Represents a logged event for a job."""

    job = models.ForeignKey("workflow.Job", on_delete=models.CASCADE, related_name="job_set")
    item = models.ForeignKey(
        "workflow.Item",
        on_delete=models.CASCADE,
        related_name="item_set",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, editable=False)
    type = models.IntegerField(choices=JOBLOG_TYPES)
    log_text = models.TextField()
    is_editable = models.BooleanField(default=True)
    event_time = models.DateTimeField("Date", auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Ensure event_time is timezone-aware to avoid runtime warnings when
        tests or seed data provide naive datetimes.
        """
        try:
            from django.utils import timezone

            if self.event_time and timezone.is_naive(self.event_time):
                self.event_time = timezone.make_aware(self.event_time, timezone.get_current_timezone())
        except Exception:
            # best-effort: if timezone helpers not available, ignore
            pass
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Job Log"
        verbose_name_plural = "Job Logs"

    def get_icon_url(self):
        """Returns the appropriate joblog icon for the log type."""
        retval = "page_white.png"
        if self.type == JOBLOG_TYPE_JOB_SAVED or self.type == JOBLOG_TYPE_ITEM_SAVED:
            retval = "disk.png"
        elif self.type == JOBLOG_TYPE_JOB_CREATED or self.type == JOBLOG_TYPE_ITEM_ADDED:
            retval = "add.png"
        elif self.type == JOBLOG_TYPE_ITEM_DELETED:
            retval = "delete.png"
        elif self.type == JOBLOG_TYPE_CRITICAL:
            retval = "flag_red.png"
        elif self.type == JOBLOG_TYPE_WARNING:
            retval = "flag_yellow.png"
        elif self.type == JOBLOG_TYPE_PRODUCTION_EDITED:
            retval = "cog_edit.png"
        elif self.type == JOBLOG_TYPE_NOTE:
            retval = "comments.png"
        elif self.type == JOBLOG_TYPE_JDF:
            retval = "lightning_go.png"
        elif self.type == JOBLOG_TYPE_JDF_ERROR or self.type == JOBLOG_TYPE_ERROR or self.type == JOBLOG_TYPE_ITEM_REJECTED:
            retval = "error.png"
        elif self.type == JOBLOG_TYPE_ITEM_REVISION:
            retval = "note_edit.png"
        elif self.type == JOBLOG_TYPE_FTP:
            retval = "server.png"
        elif self.type == JOBLOG_TYPE_BILLING:
            retval = "money_dollar.png"
        elif self.type == JOBLOG_TYPE_FEDEX:
            retval = "email.png"
        elif self.type == JOBLOG_TYPE_ITEM_PREFLIGHT:
            retval = "thumb_up.png"
        elif self.type == JOBLOG_TYPE_ITEM_APPROVED:
            retval = "picture_go.png"
        elif self.type == JOBLOG_TYPE_ITEM_FORECAST:
            retval = "rainbow.png"
        elif self.type == JOBLOG_TYPE_ITEM_FILED_OUT:
            retval = "film_go.png"
        elif self.type == JOBLOG_TYPE_ITEM_PROOFED_OUT:
            retval = "package_go.png"
        elif self.type == JOBLOG_TYPE_JOBLOG_DELETED:
            retval = "bin.png"
        return settings.MEDIA_URL + "img/icons/" + retval

    def __str__(self):
        """String representation of the object."""
        return "%s (%s)" % (self.job.name, self.get_type_display())

    def is_log_text_truncated(self, truncate_words=200):
        """
        Checks the log text to see if it would be truncated, given a limit
        of truncate_words words.
        """
        split_comment = self.log_text.split()
        if len(split_comment) > truncate_words:
            return True
        else:
            return False

    def can_edit_comment(self):
        """Test if the user can edit the given comment"""
        today = date.today()
        cutoff_date = today + timedelta(days=-30)

        if cutoff_date < self.event_time.date() and threadlocals.get_current_user() == self.user:
            return True
        else:
            return False


def joblog_post_save(sender, instance, created, *args, **kwargs):
    """Things to happen after an JobLog object is saved."""
    # Call job save to regenerate keywords.
    instance.job.save()


"""
Register dispatchers
"""
signals.post_save.connect(joblog_post_save, sender=JobLog)
