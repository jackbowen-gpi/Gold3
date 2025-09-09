"""These models serve as queues for various systems and scritps that run in the
background. These models are those that don't fit cleanly under their own apps.
For example, there is no Hughes Uploading app, and there is not enough
functionality needed to necessitate such an app.

As of 2015 the tiff2pdf workflow is handled in Automation Engine. The TiffToPDF
queue is no longer in use but for now we're leaving it just in case we need the
info for something.
"""

from django.db import models
from django.utils import timezone


class ColorKeyQueue(models.Model):
    """Color_Key_Queue queue."""

    item = models.ForeignKey("workflow.Item", on_delete=models.CASCADE, editable=False)
    date_queued = models.DateTimeField("Date Queued", auto_now_add=True)
    date_processed = models.DateTimeField("Date Processed", blank=True, null=True)
    number_of_attempts = models.IntegerField(
        "Attempts", default=0, blank=True, null=True
    )

    class Meta:
        ordering = ["-date_queued"]

    def mark_as_processed(self):
        """The item has either started processing or has been processed. In either
        case, this prevents the queue watcher from picking the item up again
        and double-processing it.
        """
        self.date_processed = timezone.now()
        self.save()

    def process(self):
        """Marks the queue entry as processed and makes the jdfs."""
        self.mark_as_processed()
        self.item.do_jdf_fsb_colorkeys()


class TiffToPDF(models.Model):
    """Tiff_to_PDF queue."""

    item = models.ForeignKey("workflow.Item", on_delete=models.CASCADE, editable=False)
    date_queued = models.DateTimeField("Date Queued", auto_now_add=True)
    date_processed = models.DateTimeField("Date Processed", blank=True, null=True)

    class Meta:
        ordering = ["-date_queued"]

    def mark_as_processed(self):
        """The item has either started processing or has been processed. In either
        case, this prevents the queue watcher from picking the item up again
        and double-processing it.
        """
        self.date_processed = timezone.now()
        self.save()

    def process(self):
        """Marks the queue entry as processed and makes the tiffs."""
        self.mark_as_processed()
        self.item.do_tiff_to_pdf()
