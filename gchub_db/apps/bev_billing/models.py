"""Beverage Billing/Invoicing Application."""

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum

from gchub_db.apps.workflow.models import Job


class BevInvoice(models.Model):
    """An invoice to Evergreen Packaging (Beverage)."""

    # Invoice number entered by Acct. Dept. (not an id)
    invoice_number = models.CharField("Invoice No.", max_length=50)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    # Important milestones in an invoice's career.
    creation_date = models.DateTimeField("Date Created", auto_now_add=True)
    qad_entry_date = models.DateField("QAD Entry Date", blank=True, null=True)
    qad_entry_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="qad_entered_by",
    )
    invoice_entry_date = models.DateField("Invoice Date", blank=True, null=True)
    invoice_entry_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="invoice_entered_by",
    )
    pdf_sent_date = models.DateField("PDF Send Date", blank=True, null=True)

    def __str__(self):
        """String representation."""
        if self.invoice_number:
            return "Invoice: %s -- %s" % (self.invoice_number, self.job)
        else:
            return "Invoice: (Number Pending) -- %s" % self.job

    def total_amount(self):
        """Return the total amount charged for this invoice."""
        total = self.charge_set.all().aggregate(Sum("amount"))["amount__sum"]
        if total:
            return total
        else:
            return 0

    def total_graphics(self):
        """Return total amount charges for graphics on this invoice."""
        plate_charges = ["Plates", "Films"]
        total = self.charge_set.exclude(description__type__in=plate_charges).aggregate(Sum("amount"))["amount__sum"]
        if total:
            return total
        else:
            return 0

    def total_plates(self):
        """Return total amount charges for plates on this invoice."""
        plate_charges = ["Plates", "Films"]
        total = self.charge_set.filter(description__type__in=plate_charges).aggregate(Sum("amount"))["amount__sum"]
        if total:
            return total
        else:
            return 0
