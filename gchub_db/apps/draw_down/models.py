"""Ink Drawdown Request application"""

from django.contrib.auth.models import User
from django.db import models

from gchub_db.apps.workflow.models import PrintLocation


class DrawDownRequest(models.Model):
    """A request for draw downs of items on a job"""

    send_prints_to = models.TextField(max_length=255)
    comments = models.TextField(max_length=500, blank=True)
    date_needed = models.DateField("Date Needed", blank=True, null=True)
    creation_date = models.DateField("Date Created", blank=True, null=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    request_complete = models.BooleanField(default=False)
    job_number = models.IntegerField(blank=True, null=True)
    customer_name = models.CharField(max_length=255)

    class Meta:
        ordering = ["customer_name"]
        app_label = "draw_down"

    def __str__(self):
        """String representation."""
        return "Drawdown for: %s" % self.customer_name

    def getDrawdownItems(self):
        return DrawDownItem.objects.filter(draw_down_request=self)

    def getDrawdownItemsPrintLocations(self):
        printLocs = ""
        drawdownItems = DrawDownItem.objects.filter(draw_down_request=self)
        for item in drawdownItems:
            printLocs += str(item.print_location) + ", "
        return printLocs


class DrawDownItem(models.Model):
    """An item that needs a draw down"""

    item_number = models.IntegerField(blank=True, null=True)
    substrate = models.CharField(max_length=255)
    print_location = models.ForeignKey(PrintLocation, on_delete=models.CASCADE)
    colors_needed = models.CharField(max_length=255)
    number_copies = models.IntegerField(blank=True, null=True)
    artwork = models.BooleanField(default=True)
    draw_down_request = models.ForeignKey(DrawDownRequest, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["item_number"]

    def __str__(self):
        """String representation."""
        return "%s - %d" % (self.substrate, self.item_number)


class Drawdown(models.Model):
    """A contact in the address book."""

    customer_name = models.CharField(max_length=255)
    job_number = models.IntegerField(blank=True, null=True)
    substrate = models.CharField(max_length=255)
    print_location = models.ForeignKey(PrintLocation, on_delete=models.CASCADE)
    colors_needed = models.CharField(max_length=255)
    number_copies = models.IntegerField(blank=True, null=True)
    send_prints_to = models.TextField(max_length=255)
    comments = models.TextField(max_length=500, blank=True)
    date_needed = models.DateField("Date Needed", blank=True, null=True)
    creation_date = models.DateField("Date Created", blank=True, null=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    request_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ["customer_name"]

    def __str__(self):
        """String representation."""
        return "Drawdown for: %s" % self.customer_name
