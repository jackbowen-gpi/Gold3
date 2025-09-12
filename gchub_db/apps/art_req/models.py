"""
Module gchub_db\apps\art_req\\models.py
"""

from django.contrib.auth.models import User
from django.db import models

from gchub_db.apps.qad_data.models import QAD_CasePacks, QAD_PrintGroups
from gchub_db.apps.workflow import app_defs
from gchub_db.apps.workflow.models.general import ItemCatalog

from .state_choices import STATE_CHOICES


class ChannelChoices(models.TextChoices):
    ENDUSER = "enduser", "End User"
    DISTRIBUTOR = "distributor", "Distributor"


class PrintTypeChoices(models.TextChoices):
    STOCK = "stock", "Stock"
    LOCAL = "local", "Local"
    NATIONAL = "national", "National"
    TRADE = "trade", "Trade"
    BRANDED = "branded", "Branded"


class CorrugatedTypeChoices(models.TextChoices):
    IPFB = "ipfb", "IPFB"  # Legacy choice
    GPI = "gpi", "GPI"
    CUSTOM = "custom", "Custom"
    PREPRINT = "preprint", "Preprint"


CORRUGATED_TYPE_CHOICES = CorrugatedTypeChoices.choices


class ForecastChoices(models.TextChoices):
    FLOORSTOCK = "floorstock", "Floor Stock"
    MAKEANDSHIP = "makeandship", "Make and Ship"
    PROMOTIONAL = "promotional", "Promotional"


class MarketSegment(models.Model):
    """
    The various market segments and their descriptions that can be assigned to
    an art request.
    """

    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return str(self.name)

    class Meta:
        app_label = "art_req"


class ArtReq(models.Model):
    """Represents an Art Request which is used to create Jobs."""

    design_name = models.CharField(
        max_length=255, help_text="Primary design identifier"
    )
    contact_name = models.CharField(
        max_length=255, help_text="Primary contact for this request"
    )
    contact_email = models.EmailField(
        max_length=255, help_text="Primary contact email for this request"
    )
    sales_rep = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="artreq_salesrep"
    )
    csr = models.ForeignKey(User, on_delete=models.CASCADE, related_name="artreq_csr")
    channel = models.CharField(
        max_length=25,
        choices=ChannelChoices.choices,
        help_text="Distribution channel for this request",
    )
    mkt_segment = models.ForeignKey(
        MarketSegment, on_delete=models.CASCADE, verbose_name="Market Segment"
    )
    print_type = models.CharField(
        max_length=25, choices=PrintTypeChoices.choices, verbose_name="Print Type"
    )
    printgroup = models.ForeignKey(
        QAD_PrintGroups, on_delete=models.CASCADE, verbose_name="Print Group"
    )
    ship_to_name = models.CharField(max_length=255)
    ship_to_company = models.CharField(max_length=255, blank=True)
    ship_to_addy_1 = models.CharField(max_length=255)
    ship_to_addy_2 = models.CharField(max_length=255, blank=True)
    ship_to_city = models.CharField(max_length=255)
    ship_to_state = models.CharField(max_length=255, blank=True)
    # Not all countries use postal/zip codes
    ship_to_zip = models.CharField(max_length=255, blank=True)
    ship_to_country = models.CharField(max_length=255, blank=True)
    ship_to_email = models.CharField(max_length=255, blank=True)
    ship_to_phone = models.CharField(max_length=255)
    # If a GOLD job is created from this artreq record the number here.
    job_num = models.IntegerField(blank=True, null=True)
    corr_job_num = models.IntegerField(blank=True, null=True)
    # We'll record who makes the art request and when quitely in the background.
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="artreq_created_by",
    )
    creation_date = models.DateTimeField("Creation Date", auto_now_add=True)

    def __str__(self):
        return f"{self.design_name} ({self.get_channel_display()})"

    class Meta:
        app_label = "art_req"
        verbose_name = "Art Request"
        verbose_name_plural = "Art Requests"
        ordering = ["-creation_date"]
        indexes = [
            models.Index(fields=["job_num"]),
            models.Index(fields=["creation_date"]),
            models.Index(fields=["sales_rep", "creation_date"]),
        ]


class PartialArtReq(models.Model):
    fieldData = models.TextField(blank=True, null=True, verbose_name="Field Data")
    fileData = models.TextField(blank=True, null=True, verbose_name="File Data")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="partial_artreq_created_by",
    )
    creation_date = models.DateTimeField("Creation Date", auto_now_add=True)
    last_updated = models.DateTimeField("Last Updated", auto_now=True)
    artReq = models.ForeignKey(
        ArtReq,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Art Request",
    )
    partial_name = models.CharField(max_length=255, verbose_name="Partial Name")
    is_completed = models.BooleanField(default=False, verbose_name="Completed")

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.partial_name} ({status})"

    class Meta:
        app_label = "art_req"
        verbose_name = "Partial Art Request"
        verbose_name_plural = "Partial Art Requests"
        ordering = ["-last_updated"]


class ExtraProof(models.Model):
    """An address where additional proofs from an art request must be sent."""

    artreq = models.ForeignKey(ArtReq, on_delete=models.CASCADE)
    ship_to_name = models.CharField(verbose_name="Name", max_length=255, blank=True)
    ship_to_company = models.CharField(
        verbose_name="Company", max_length=255, blank=True
    )
    ship_to_addy_1 = models.CharField(
        verbose_name="Address 1", max_length=255, blank=True
    )
    ship_to_addy_2 = models.CharField(
        verbose_name="Address 2", max_length=255, blank=True
    )
    ship_to_city = models.CharField(verbose_name="City", max_length=255, blank=True)
    ship_to_state = models.CharField(blank=True, max_length=255, verbose_name="State")
    # Not all countries use postal/zip codes
    ship_to_zip = models.CharField(verbose_name="Zip", max_length=255, blank=True)
    ship_to_country = models.CharField(
        verbose_name="Country", max_length=255, blank=True
    )
    ship_to_email = models.CharField(verbose_name="Email", max_length=255, blank=True)
    ship_to_phone = models.CharField(verbose_name="Phone", max_length=255, blank=True)

    def __str__(self):
        return "%s-%s" % (str(self.ship_to_name), str(self.artreq))


class Product(models.Model):
    """New items to be created by an art request."""

    artreq = models.ForeignKey(ArtReq, on_delete=models.CASCADE)
    size = models.ForeignKey(ItemCatalog, on_delete=models.CASCADE)
    case_pack = models.ForeignKey(
        QAD_CasePacks,
        on_delete=models.CASCADE,
        verbose_name="Case Pack",
        blank=True,
        null=True,
    )
    annual_usage = models.IntegerField(verbose_name="Annual Usage")
    order_quantity = models.IntegerField(
        verbose_name="Estimated Order Quantity", blank=True, null=True
    )
    customer_number = models.CharField(
        verbose_name="Customer Number", blank=True, max_length=255
    )
    render = models.BooleanField(verbose_name="Render", default=False)
    wrap_proof = models.BooleanField(verbose_name="Wrap Proof", default=False)
    ink_jet_promo = models.BooleanField(verbose_name="Ink Jet Promo", default=False)
    label_promo = models.BooleanField(verbose_name="Label Promo", default=False)
    mock_up = models.BooleanField(verbose_name="Mock-Ups", default=False)
    plant1 = models.CharField(blank=True, max_length=255)
    plant2 = models.CharField(blank=True, max_length=255)
    plant3 = models.CharField(blank=True, max_length=255)
    press1 = models.CharField(blank=True, max_length=255)
    press2 = models.CharField(blank=True, max_length=255)
    press3 = models.CharField(blank=True, max_length=255)
    ship_to_state = models.CharField(
        blank=True, max_length=2, verbose_name="Ship to State", choices=STATE_CHOICES
    )
    # The below fields are used to generate corrigated items.
    corr_type = models.CharField(
        verbose_name="Corrugated Type",
        choices=CorrugatedTypeChoices.choices,
        max_length=255,
        blank=True,
        default="gpi",
    )
    corr_only = models.BooleanField(default=False)
    label_color = models.CharField(
        verbose_name="Label Color", max_length=255, blank=True
    )
    label_copy_1 = models.CharField(
        verbose_name="Label Copy 1", max_length=22, blank=True
    )
    label_copy_2 = models.CharField(
        verbose_name="Label Copy 2", max_length=22, blank=True
    )
    label_copy_3 = models.CharField(
        verbose_name="Label Copy 3", max_length=22, blank=True
    )
    corr_plant1 = models.CharField(blank=True, max_length=255)
    corr_plant2 = models.CharField(blank=True, max_length=255)
    corr_plant3 = models.CharField(blank=True, max_length=255)
    sleeve_count = models.IntegerField(
        verbose_name="Sleeve Count", blank=True, null=True
    )
    print_color = models.CharField(
        verbose_name="Print Color", blank=True, max_length=255
    )
    case_color = models.CharField(verbose_name="Case Color", blank=True, max_length=255)

    def __str__(self):
        return "%s-%s" % (str(self.size), str(self.artreq))


class AdditionalInfo(models.Model):
    """Misc. additional info to be recorded about an art request."""

    artreq = models.ForeignKey(ArtReq, on_delete=models.CASCADE)
    keep_same_upc = models.BooleanField(default=False)
    replaces_prev_design = models.BooleanField(default=False)
    prev_9_digit = models.CharField(
        max_length=255, blank=True, verbose_name="Previous 9-Digit #"
    )
    forecast = models.CharField(
        verbose_name="Forecast", choices=ForecastChoices.choices, max_length=255
    )
    incoming_art_format = models.IntegerField(
        choices=app_defs.ART_REC_TYPES, blank=True, null=True
    )
    arrival_date = models.DateField(blank=True, null=True)
    sender = models.CharField(max_length=255, blank=True)
    date_needed = models.DateField(blank=True, null=True)
    special_instructions = models.TextField(blank=True)

    def __str__(self):
        return str(self.artreq)
