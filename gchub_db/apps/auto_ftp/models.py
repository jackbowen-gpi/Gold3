"""Automatic uploading of Tiffs to remote platemaking FTP sites."""

import re

from django.conf import settings
from django.db import models
from django.utils import timezone

DESTINATION_FUSION_FLEXO = 6
DESTINATION_CYBER_GRAPHICS = 11
DESTINATION_SOUTHERN_GRAPHIC = 16
DESTINATION_PHOTOTYPE = 21

DESTINATION_CHOICES = (
    (DESTINATION_FUSION_FLEXO, "Fusion_Flexo"),
    (DESTINATION_CYBER_GRAPHICS, "Cyber_Graphics"),
    (DESTINATION_SOUTHERN_GRAPHIC, "Southern_Graphic"),
    (DESTINATION_PHOTOTYPE, "Phototype"),
)


class AutoFTPTiff(models.Model):
    """Automatically uploades the tiffs for the given items."""

    job = models.ForeignKey("workflow.Job", on_delete=models.CASCADE)
    items = models.ManyToManyField("workflow.Item")
    destination = models.IntegerField(choices=DESTINATION_CHOICES)
    date_queued = models.DateTimeField("Date Queued", auto_now_add=True)
    date_processed = models.DateTimeField("Date Processed", blank=True, null=True)

    class Meta:
        ordering = ["-date_queued"]

    def item_number(self):
        itemList = self.items.all()
        returnStr = ""
        for item in itemList:
            returnStr += "," + str(item.num_in_job)
        if returnStr == "":
            return "None"
        else:
            return returnStr[1:]

    def get_settings_dict(self):
        """
        Gets the correct FTP account data dict from settings.py based
        on the destination.
        """
        ftp_dict_key = self.get_destination_display().upper()
        return settings.TIFF_FTP[ftp_dict_key]

    def get_remote_job_path(self):
        """Returns the full path to the job's remote FTP folder."""
        # Spaces aren't valid in FTP.
        strip_spaces = self.job.name.replace(" ", "_")

        # Matches any non-alphanumeric character plus underscores.
        regexp_non_alnum = re.compile(r"[^a-zA-Z0-9_]+")
        # Matches a non-alphanumeric character surrounded by underscores: _?_
        regexp_avoid_double_underscore = re.compile(r"([_]+)")

        # Yank any alphanumeric characters.
        stripped_name = regexp_non_alnum.sub("", strip_spaces)
        # Strip stuff and avoid double underscores.
        stripped_name = regexp_avoid_double_underscore.sub("_", stripped_name)

        if not stripped_name[-1:].isalnum():
            stripped_name = stripped_name[:-1]

        sdict = self.get_settings_dict()
        remote_dir = sdict["ROOT_DIR"]
        return "%s/%s_%s" % (remote_dir, self.job.id, stripped_name)

    def mark_as_processed(self):
        """
        The items have been uploaded or the attempt has been made. Removes
        the upload from the queue.
        """
        self.date_processed = timezone.now()
        self.save()
