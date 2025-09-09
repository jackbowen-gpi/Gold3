"""Main Workflow App: Contains jobs, items, item revisions, item ink usage,
item QCs, and item specification information.
"""

import re
from datetime import date, timedelta

from colormath.color_conversions import convert_color
from colormath.color_objects import LabColor, LCHabColor
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.db import models
from django.db.models import signals
from django.template import loader

from gchub_db.apps.address.models import Contact
from gchub_db.apps.color_mgt.models import ColorDefinition
from gchub_db.apps.fedexsys.models import AddressValidationModel, Shipment
from gchub_db.apps.item_catalog.models import *

# Normally this would be a bad idea, but these variables are uniquely named.
from gchub_db.apps.joblog.app_defs import *
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.app_defs import *
from gchub_db.includes import fs_api, general_funcs
from gchub_db.middleware import threadlocals

# This was used to limit the choices of the Plant:bev_controller field. Broke in 1.2
# BEVERAGE_PERMISSION = Permission.objects.get(codename="beverage_access")


class Plant(models.Model):
    """Represents a Plant/Facility."""

    name = models.CharField(max_length=100)
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, blank=True)
    bev_controller = models.ManyToManyField(
        User, related_name="beverage_controllers", blank=True
    )
    # Does this plant show up in the automated corrugated system?
    is_in_acs = models.BooleanField(default=False)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return self.name


class Press(models.Model):
    """Represents a Press. Will be coupled to Plant in PrintLocation model."""

    name = models.CharField(max_length=100)
    # For use with JDF ticket naming.
    short_name = models.CharField(max_length=20)
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Presses"

    def __str__(self):
        return self.name


class PrintLocation(models.Model):
    """Intermediary model: Plant - Press combinations.
    This model lists all actual combinations of Plant and Press, with
    plants tied to Sites.
    """

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    press = models.ForeignKey(Press, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        ordering = ["plant"]

    def __str__(self):
        return str(self.plant) + " - " + str(self.press)


class ProofTracker(models.Model):
    """A record of a proof printed by Automation Engine."""

    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    creation_date = models.DateTimeField("Date Printed")
    copies = models.IntegerField(default=1)
    xml_filename = models.CharField(max_length=255, blank=True)
    proofer = models.CharField(max_length=255, blank=True)


class Platemaker(models.Model):
    """Represents a Plate Maker."""

    name = models.CharField(max_length=255, unique=True)
    workflow = models.ManyToManyField(
        Site, related_name="platemaking_sites", blank=True
    )
    contacts = models.ManyToManyField(
        User, related_name="platemaking_contacts", blank=True
    )

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return self.name


class SpecialMfgConfiguration(models.Model):
    """Represents a special manufacturing instruction. Typically effects S&R.
    Examples would be Big Cylinder, Small Cylinder, Blank Fed, Roll Fed
    Forms Somewhere Else, etc...
    """

    name = models.CharField(max_length=255, unique=True)
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return self.name


class PlatePackage(models.Model):
    """Intermediary model: Platemaker - Platetype - Workflow combinations.
    For example Acme Plates makes Digital Flexo plates for Foodservice.
    """

    platetype = models.CharField(max_length=50, choices=PLATE_OPTIONS)
    workflow = models.ManyToManyField(
        Site, related_name="platepackage_sites", blank=True
    )
    platemaker = models.ForeignKey(Platemaker, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        ordering = ["platemaker"]

    def __str__(self):
        return str(self.platemaker) + " - " + str(self.platetype)


class ItemCatalog(models.Model):
    """An available products/item."""

    size = models.CharField(max_length=75, unique=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, blank=True)
    productsubcategory = models.ManyToManyField(
        ProductSubCategory,
        related_name="itemcatalog_set",
        blank=True,
        verbose_name="Prod. Category",
    )
    product_substrate = models.IntegerField(
        "Substrate", blank=True, null=True, choices=PROD_SUBSTRATES
    )
    product_board = models.IntegerField(
        "Board", blank=True, null=True, choices=PROD_BOARDS
    )
    # mfg_name: Foodservice 8 char. unique code from MFGPRO system.
    # ie SMR-16 =  SMR-0160
    # This will be used to translate incoming art request information.
    mfg_name = models.CharField(
        "MFG Name", max_length=20, blank=True, null=True, unique=True
    )
    template = models.CharField(max_length=100, blank=True)
    photo = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    last_edit = models.DateTimeField("Last Edit Date", auto_now=True)
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)
    acts_like = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="acts_like_item_set",
        blank=True,
        null=True,
    )
    # Code used for Evergreen's new nomenclature: 10/2009
    # (A=4oz Eco, H=Half Gallon, Q=Quart, etc...)
    bev_size_code = models.CharField(max_length=5, blank=True)
    comments = models.TextField(max_length=500, blank=True, null=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Item Catalog"
        ordering = ["size"]

    def __str__(self):
        return self.size

    def is_metric(self):
        """Returns True if the item is a metric size."""
        return self.size.lower().replace(" ", "") in [
            "250ml",
            "500ml",
            "liter",
            "2liter",
            "1liter",
        ]

    def is_bev_panel(self):
        """Return True if item is a Beverage side panel."""
        if (
            self.workflow.name == "Beverage"
            and ProductSubCategory.objects.get(sub_category="Panel")
            in self.productsubcategory.all()
        ):
            return True
        else:
            return False

    def is_bev_carton(self):
        """Return True if item is a Beverage side panel."""
        if (
            self.workflow.name == "Beverage"
            and ProductSubCategory.objects.get(sub_category="Carton")
            in self.productsubcategory.all()
        ):
            return True
        else:
            return False

    def pdf_template_exists(self):
        """Returns True if PDF template exists."""
        try:
            pdf_file = fs_api.get_pdf_template(self.size)
            return True
        except Exception:
            return False

    def get_stripped_size(self):
        """Returns the stripped and formatted size for use with scripts."""
        return self.size.replace(" ", "").lower()

    def get_coating_type(self, return_abbrev=False):
        """Returns a string representation of this item type's coating.

        Can be one of the following, abbreviations are in parenthesis:
        * Uncoated (or U)
        * Coated (or C)

        A true value for return_abbrev returns the single-character abbreviated
        form of the coating type.
        """
        if self.product_substrate in UNCOATED_SUBSTRATES:
            if return_abbrev:
                return "U"
            else:
                return "Uncoated"
        else:
            # Fits the majority of cases when unknown.
            if return_abbrev:
                return "C"
            else:
                return "Coated"

    def specs_with_item(self):
        number = ItemSpec.objects.filter(size=self.id).count()
        return number

    def active_specs(self):
        """Return active specs associated with catalog."""
        return ItemSpec.objects.filter(size=self.id, active=True).order_by(
            "printlocation__plant__name", "printlocation__press__name"
        )


class BevItemColorCodes(models.Model):
    """Codes for Beverage nomenclature. Use item and number of colors to determine
    code. (ie. Size: Quart + Colors: 3 = Code: 61) And no, there's no
    logic to it...
    """

    size = models.ForeignKey("ItemCatalog", on_delete=models.CASCADE)
    num_colors = models.IntegerField()
    code = models.CharField(max_length=20)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return str(self.size)


class ItemCatalogPhoto(models.Model):
    """Photos and models of stock designs.
    Not currently in use -- will be a Phase 2 feature.
    """

    size = models.ForeignKey("ItemCatalog", on_delete=models.CASCADE)
    stock = models.CharField(max_length=20, blank=True)
    photo = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    last_edit = models.DateTimeField("Last Edit Date", auto_now=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Item Catalog Photos"

    def __str__(self):
        return str(self.size)


class ItemSpec(models.Model):
    """Defines specifcations for items (fsb: plant & press unique)."""

    size = models.ForeignKey("ItemCatalog", on_delete=models.CASCADE)
    printlocation = models.ForeignKey(PrintLocation, on_delete=models.CASCADE)
    # Maximum allowable number of colors for Size X at PrintLocation Y
    #    num_colors = models.IntegerField(blank=True, null=True) #moving to StepSpec model
    stepping_notes = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    # FSB dimensions for the art rectangle.
    horizontal = models.FloatField("Art width", blank=True, null=True)
    vertical = models.FloatField("Art height", blank=True, null=True)
    # Template dimensions (the whole thing, not just the art).
    #    template_horizontal = models.FloatField("Template width", blank=True, null=True)#moving to StepSpec model
    #    template_vertical = models.FloatField("Template height", blank=True, null=True)#moving to StepSpec model
    # FSB Product Catalog information -- to be used later.
    case_dim_w = models.CharField("Case width", max_length=25, blank=True)
    case_dim_h = models.CharField("Case height", max_length=25, blank=True)
    case_dim_d = models.CharField("Case depth", max_length=25, blank=True)
    total_print_area = models.DecimalField(
        "Total Print Area", max_digits=7, decimal_places=2, blank=True, null=True
    )
    case_wt = models.CharField("Case weight", max_length=100, blank=True)
    case_pack = models.IntegerField(blank=True, null=True)
    # Minimum case order quantities.
    min_case = models.IntegerField(blank=True, null=True)
    #    step_around = models.IntegerField(blank=True, null=True)#moving to StepSpec model
    #    step_across = models.IntegerField(blank=True, null=True)#moving to StepSpec model
    # Calculated by multiplying step_around and step_across fields.
    #    num_blanks = models.IntegerField(blank=True, null=True)#moving to StepSpec model

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Item Specifications"
        unique_together = (("size", "printlocation"),)

    def __str__(self):
        return str(self.size) + " - " + str(self.printlocation)

    def get_absolute_url(self):
        return "/workflow/itemcatalog/specs/edit/%d/" % self.id


class StepSpec(models.Model):
    """Defines specifications for step and repeat tickets."""

    itemspec = models.ForeignKey("ItemSpec", on_delete=models.CASCADE)
    special_mfg = models.ForeignKey(
        "SpecialMfgConfiguration", on_delete=models.CASCADE, blank=True, null=True
    )
    eng_num = models.CharField("Engineering drawing number", max_length=20, blank=True)
    num_colors = models.IntegerField("Number of colors", blank=True, null=True)
    status_types = (
        ("created", "Created"),
        ("checked", "Checked"),
        ("verified", "Verified"),
    )
    status = models.CharField(max_length=20, blank=True, choices=status_types)
    # Template dimensions (the whole thing, not just the art).
    template_horizontal = models.FloatField("Template width", blank=True, null=True)
    template_vertical = models.FloatField("Template height", blank=True, null=True)
    step_around = models.IntegerField(blank=True, null=True)
    step_across = models.IntegerField(blank=True, null=True)
    print_repeat = models.FloatField(blank=True, null=True)
    num_blanks = models.IntegerField("Number of blanks", blank=True, null=True)
    comments = models.CharField(max_length=500, blank=True)
    active = models.BooleanField(default=False)
    creation_date = models.DateTimeField("Date created", auto_now_add=True)
    last_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="stepspec_edits",
    )
    last_edit = models.DateTimeField("Last edit date", auto_now=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Step and repeat specifications"
        unique_together = (("itemspec", "special_mfg"),)

    def __str__(self):
        return str(self.itemspec) + " - " + str(self.special_mfg)


def stepspec_pre_save(sender, instance, *args, **kwargs):
    """Things do to before a StepSpec object is saved."""
    # Calculate the num_blanks available and save. This will allow for searching
    # based on this number. If incomplete information, or none at all, set None.
    if instance.step_around and instance.step_across:
        instance.num_blanks = instance.step_around * instance.step_across
    else:
        instance.num_blanks = None


signals.pre_save.connect(stepspec_pre_save, sender=StepSpec)


class Substrate(models.Model):
    """Represents a carton substrate."""

    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Substrates"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CartonWorkflow(models.Model):
    """Represents a carton workflow. Not to be confused with our usual workflows
    like Foodservice and Beverage.
    """

    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Carton Workflows"
        ordering = ["name"]

    def __str__(self):
        return self.name


class LineScreen(models.Model):
    """Represents a carton line screen."""

    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Line Screens"
        ordering = ["name"]

    def __str__(self):
        return self.name


class InkSet(models.Model):
    """Represents a carton ink set."""

    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Ink Sets"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PrintCondition(models.Model):
    """Represents a carton print condition."""

    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Print Conditions"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Trap(models.Model):
    """Represents a carton trap."""

    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Traps"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CartonProfile(models.Model):
    """Represents a carton profile."""

    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    carton_workflow = models.ManyToManyField(
        CartonWorkflow, related_name="carton_workflows"
    )
    line_screen = models.ManyToManyField(LineScreen, related_name="line_screens")
    ink_set = models.ManyToManyField(InkSet, related_name="ink_sets")
    substrate = models.ManyToManyField(Substrate, related_name="substrates")
    print_location = models.ManyToManyField(
        PrintLocation, related_name="print_locations"
    )
    print_condition = models.ManyToManyField(
        PrintCondition, related_name="print_conditions"
    )

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Carton Profiles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TiffCrop(models.Model):
    """Stores crop dimension for the beverage tiff to PDF workflow. Storing the
    dimensions here makes them easier to maintain and easier for Esko software
    to read them.
    """

    size = models.ForeignKey("ItemCatalog", on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    num_up = models.IntegerField()
    special_mfg = models.ForeignKey(
        "SpecialMfgConfiguration", on_delete=models.CASCADE, blank=True, null=True
    )
    x_size = models.FloatField()
    y_size = models.FloatField()
    x_offset = models.FloatField()
    y_offset = models.FloatField()

    class Meta:
        app_label = "workflow"
        verbose_name = "Tiff Crop Dimension"
        verbose_name_plural = "Tiff Crop Dimensions"

    def __str__(self):
        return "%s - %s - %s - %s" % (
            str(self.size),
            str(self.plant),
            str(self.num_up),
            str(self.special_mfg),
        )


class TrackedArt(models.Model):
    """Tracks certain art elements that we need to keep track of for reporting
    and regulatory purposes. Things like Ecotainer logos and erviromental
    verbage.
    """

    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    art_types = (
        ("ecotainer", "Ecotainer Logo"),
        ("hold_go", "Hold & Go Logo"),
        ("bpi", "BPI Logo"),
        ("din_certo", "Din Certo Logo"),
        ("sfi", "SFI Label"),
        ("fsc", "FSC Label"),
        ("pefc", "PEFC Label"),
        ("misc_enviro", "Misc. Enviromental Messaging"),
    )
    art_catagory = models.CharField(max_length=30, choices=art_types)
    addition_comments = models.CharField(max_length=500, blank=True)
    addition_date = models.DateField("Date Added", blank=True, null=True)
    edited_by = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="edited_by"
    )
    removal_comments = models.CharField(max_length=500, blank=True)
    removal_date = models.DateField("Date Removed", blank=True, null=True)
    removed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="removed_by"
    )

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return "%s -%s - %s" % (
            str(self.item.job),
            str(self.item),
            str(self.art_catagory),
        )

    def get_marketing_reviews(self):
        reviews = ItemReview.objects.filter(item=self.item, review_catagory="market")
        return reviews


class ItemTracker(models.Model):
    """These objects are assigned to items to track things like SFI logos and
    QR codes (we'll call these tracker types or just types). Each tracker type
    can also be assigned to a tracker category like marketing or promotional.
    This set-up will make it very easy to run a report for marketing that lists
    all the items with SFI logos on them for example. Tracker types and
    categories will be defined by models so that we can easily add types and
    categories as needed.
    """

    item = models.ForeignKey(
        "Item", on_delete=models.CASCADE
    )  # Which item is being tracked.
    type = models.ForeignKey(
        "ItemTrackerType", on_delete=models.CASCADE
    )  # What in the item is being tracked.
    addition_comments = models.CharField(max_length=500, blank=True, null=True)
    addition_date = models.DateField("Date Added", blank=True, null=True)
    edited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="tracker_edited_by",
    )
    removal_comments = models.CharField(max_length=500, blank=True, null=True)
    removal_date = models.DateField("Date Removed", blank=True, null=True)
    removed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="tracker_removed_by",
    )

    class Meta:
        app_label = "workflow"
        verbose_name = "Item Tracker"
        verbose_name_plural = "Item Trackers"

    def __str__(self):
        return "%s - %s - %s" % (str(self.item.job), str(self.item), str(self.type))


class ItemTrackerType(models.Model):
    """The various types of things we track on items. SFI logos, QR Codes, or
    whatever else we can think of the we might want to keep tabs on for
    reporting purposes.
    """

    name = models.CharField(max_length=50)
    category = models.ForeignKey("ItemTrackerCategory", on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    class Meta:
        app_label = "workflow"
        verbose_name = "Item Tracker Type"
        verbose_name_plural = "Item Tracker Types"

    def __str__(self):
        return "%s" % (str(self.name))


class ItemTrackerCategory(models.Model):
    """These are the categories that item trackers fall into. For example, we track
    SFI logos for marketing so SFI trackers would use the marketing category.
    These categories are mainly used to limit who should see them and what
    reports the various trackers should show up in.
    """

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    class Meta:
        app_label = "workflow"
        verbose_name = "Item Tracker Category"
        verbose_name_plural = "Item Tracker Categories"

    def __str__(self):
        return "%s" % (str(self.name))


class ChargeCategory(models.Model):
    """Defines Billing charge categories -- associated to workflows(sites)"""

    name = models.CharField(max_length=255)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Charge Categories"

    def __str__(self):
        return self.name


class ChargeType(models.Model):
    """Defines billing charge types (ie, proof, pdf, revision, etc...),
    determines actual cost
    """

    type = models.CharField(max_length=255)
    category = models.ForeignKey(ChargeCategory, on_delete=models.CASCADE)
    base_amount = models.FloatField()
    # Selects rush schedule to use in Javascript that determines price.
    rush_type = models.CharField(choices=RUSH_TYPES, max_length=8)
    # Adjust base amount based on number colors if needed.
    adjust_for_colors = models.BooleanField(default=False)
    # Adjust base amount based on item quality if needed.
    adjust_for_quality = models.BooleanField(default=False)
    # Some charges are going to require an extra flat rate. ie.
    # ($75 x num_color) + $150
    extra_amount = models.FloatField(blank=True, null=True)
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Charge Types"

    def __str__(self):
        return str(self.category) + " - " + str(self.type)

    def menu_name(self):  # Defines how charge shows up in Add Charge menu
        return str(self.category) + " - " + str(self.type)

    def actual_charge(self, num_colors=1, quality="B", rush_days="", item=None):
        """Return the actual charge amount, based on number of colors,
        quality and rush days.
        """
        amount = self.base_amount

        # "coating" inks don't count towards "Prepress Production" charges on carton items.
        if self.type == "Prepress Production" and self.workflow.name == "Carton":
            if item:
                num_colors = item.get_num_colors_carton()

        # Adjust amount for quality.
        if self.adjust_for_quality:
            if quality == "A":
                # No change
                pass
            elif quality == "B":
                amount = amount * 0.67
            elif quality == "C":
                amount = amount * 0.33

        # Adjust for number of colors/inks in item.
        if self.adjust_for_colors:
            amount = amount * num_colors

        # Add extra amount if needed.
        if self.extra_amount:
            amount = amount + self.extra_amount

        # Due to math error long ago, this needs to be done here, since it
        # can't really be fit to a formula. Grrr.
        if self.type == "New_w_Digtial_Art":
            if num_colors == 1:
                amount = 218
            if num_colors == 2:
                amount = 303
            if num_colors == 3:
                amount = 374
            if num_colors == 4:
                amount = 459

        if self.type == "Create_From_Drawing":
            if num_colors == 1:
                amount = 279
            if num_colors == 2:
                amount = 391
            if num_colors == 3:
                amount = 502
            if num_colors == 4:
                amount = 615

        # Add in rush charges last.
        # High Multiplier.
        if self.rush_type == "FSBMULTH":
            if rush_days == 0:
                amount = amount * 2
            if rush_days == 1:
                amount = amount * 1.75
            if rush_days == 2:
                amount = amount * 1.6
            if rush_days == 3:
                amount = amount * 1.5
            if rush_days == 4:
                amount = amount * 1.4
            if rush_days == 5:
                amount = amount * 1.3
            if rush_days == 6:
                amount = amount * 1.2
            if rush_days == 7:
                amount = amount * 1.1

        # Low multiplier.
        if self.rush_type == "FSBMULTL":
            if rush_days == 0:
                amount = amount * 1.5
            if rush_days == 1:
                amount = amount * 1.25

        # This is for calculating the price of Beverage plates
        # for a particular item. Needs item to determin size, num_up,
        # and qty of plates being ordered (default = 1)
        if self.type == "Plates":
            # Remove any extra bits like, Fitment or Foil
            simple_size = item.size.size.split(" - ")[0]

            ECO_PAKS = ("4oz", "6oz", "8oz", "10oz", "12oz")

            # Carton pricing.
            if simple_size == "Half Gallon":
                amount = 172.14
            if simple_size == "Quart":
                amount = 122.72
            if simple_size == "Pint":
                amount = 71.72
            if simple_size == "Half Pint":
                if item.num_up == 4:
                    amount = 139.08
                else:
                    amount = 51.53
            if simple_size.replace(" ", "") in ECO_PAKS:
                if item.num_up == 4:
                    amount = 97.75
                else:
                    amount = 48.88
            if simple_size == "2 Liter":
                amount = 181.83
            if simple_size == "1 Liter":
                amount = 129.29
            if simple_size == "500 mL":
                amount = 90.62
            if simple_size in ("250 mL", "250mL", "200 mL"):
                if item.num_up == 4:
                    amount = 139.08
                else:
                    amount = 51.53
            if simple_size == "Third Quart":
                amount = 51.53

            # Sidepanel pricing.
            if simple_size == "Sidepanel":
                # Sidepanels - get that last element of the split for the size.
                panel_size = item.size.size.split(" - ")[-1]
                if panel_size == "Pint":
                    amount = 16.96
                if panel_size == "Half Pint":
                    amount = 16.96
                if panel_size == "Quart":
                    amount = 24.87
                if panel_size == "Half Gallon":
                    amount = 28.26
                if panel_size.replace(" ", "") in ECO_PAKS:
                    amount = 16.96

                # They always make 2, so double the price.
                # Also, tell me these things earlier, damnit.
                amount = amount * 2

            # Raleigh BHS work has separate pricing.
            if (
                item.job.temp_printlocation.plant.name == "Raleigh"
                and item.job.temp_printlocation.press.name == "BHS"
            ):
                if simple_size == "Half Gallon":
                    amount = 254.33
                if simple_size == "Quart":
                    amount = 197.82
                if simple_size == "Pint":
                    amount == 197.82
                if simple_size == "Half Pint":
                    amount = 197.82

            # Now multiply by the number of plates (num_plates of each
            # itemcolor object)
            # Amounts listed above are PER PLATE.
            num_plates = 0
            for color in item.itemcolor_set.all():
                num_plates += color.num_plates
            amount = amount * num_plates
            # END PLATE CHARGE CALCULATION

        # Film pricing is calculated differently from plates.
        elif self.type == "Films":
            # Remove any extra bits like, Fitment or Foil
            simple_size = item.size.size.split(" - ")[0]

            MECO_PAKS = ("4oz", "6oz", "8oz", "10oz")

            # Carton pricing.
            if simple_size == "Half Gallon":
                amount = 33.53
            if simple_size == "Quart":
                amount = 26.26
            if simple_size == "Pint":
                amount = 26.26
            if simple_size == "2 Liter":
                amount = 33.53
            if simple_size == "Third Quart":
                amount = 26.26
            if simple_size == "Half Pint":
                if item.num_up == 4:
                    amount = 26.26
            if simple_size.replace(" ", "") in MECO_PAKS:
                if item.num_up == 4:
                    amount = 21.12

            # Now multiply by the number of plates (num_plates of each
            # itemcolor object)
            # Amounts listed above are PER PLATE.
            num_plates = 0
            for color in item.itemcolor_set.all():
                num_plates += color.num_plates
            amount = amount * num_plates
            # END FILM CHARGE CALCULATION

        return amount


class Charge(models.Model):
    """Tracks all charges -- associated to items."""

    item = models.ForeignKey("workflow.Item", on_delete=models.CASCADE)
    description = models.ForeignKey(ChargeType, on_delete=models.CASCADE)
    # Amount is determined by code in job_detail.js, but can be overridden.
    amount = models.FloatField()
    comments = models.TextField(max_length=5000, blank=True)
    creation_date = models.DateTimeField("Date Billed", auto_now_add=True)
    invoice_date = models.DateField("Date Invoiced", blank=True, null=True)
    invoice_number = models.CharField(max_length=25, blank=True)
    bill_to = models.CharField(max_length=255, blank=True)
    rush_days = models.IntegerField(blank=True, null=True)
    bev_invoice = models.ForeignKey(
        "bev_billing.BevInvoice", on_delete=models.CASCADE, blank=True, null=True
    )
    artist = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return str(self.item) + " --- " + str(self.description)

    def __unicode__(self):
        return self.__str__()

    def is_billable(self, year, month):
        """Determines wether or not the charge is billable for the given year
        and month. This will be used for budget reporting and for invoicing.
        Assume that the workflow is filtered in the code calling this method.
        (ie, Beverage invoicing)
        """
        # A charge is not billable if:
        # - It has already been invoiced (invoice date)
        # - It's item is marked as deleted.
        # - The item was worked on by another supplied.
        if (
            self.invoice_date
            or not self.item.is_deleted
            or self.item.job.prepress_supplier
            in ("PHT", "Phototype", "SGS", "Southern Graphics")
        ):
            return False

        # Now establish billing cycle for each workflow.
        # Calculate Previous/Next Month/Year
        if month == 1:
            last_month = 12
            last_year = year - 1
        else:
            last_month = month - 1
            last_year = year

        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        # Beverage cycle goes between the 21st and the end of the 20th.
        # Since we're using datetimes, using the 21st at 12:00am as a date
        # effectively captures until midnight on the 20th.
        if self.item.job.workflow.name == "Beverage":
            start_date = date(last_year, last_month, 21)
            end_date = date(year, month, 21)
        else:
            start_date = date(year, month, 1)
            end_date = date(next_year, next_month, 1)

        if (
            self.item.final_file_date() > start_date
            and self.item.final_file_date() < end_date
        ):
            return True
        else:
            return False


class PlateOrder(models.Model):
    """Submission and tracking of plate order."""

    item = models.ForeignKey("workflow.Item", on_delete=models.CASCADE)
    date_entered = models.DateField("Date Entered", auto_now_add=True)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="requested_by",
    )
    date_needed = models.DateField("Date Needed", blank=True, null=True)
    instructions = models.CharField(max_length=250, blank=True)
    # Stage 1 would be for film-based workflows.
    stage1_complete_date = models.DateField(
        "Stage1 Complete Date", blank=True, null=True
    )
    # Stage 2 is for the actual plate being made.
    stage2_complete_date = models.DateField(
        "Stage2 Complete Date", blank=True, null=True
    )
    completed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="completed_by",
    )
    # Set to Yes if a user reorders a set of plates, basically duplicating an
    # existing PlateOrder object.
    new_order = models.BooleanField(default=False)
    # Override the initial Plant of the item it's referencing.
    send_to_plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="send_to_plant",
    )
    invoice_date = models.DateField("Order Invoice Date", blank=True, null=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Plate Orders"
        permissions = (("is_platemaker", "Platemaker"),)

    def __str__(self):
        return str(self.id)

    def num_plates(self):
        """Count number of plates associated with this Order."""
        return self.plateorderitem_set.count()


class PlateOrderItem(models.Model):
    """Individual plates needed on a plate order. This will refer to a physical
    printing plate.
    """

    order = models.ForeignKey("PlateOrder", on_delete=models.CASCADE)
    color = models.ForeignKey("ItemColor", on_delete=models.CASCADE)
    quantity_needed = models.IntegerField()

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return str(self.order.id) + "-" + str(self.color)


class SalesServiceRep(models.Model):
    """Sales service reps for Beverage workflow."""

    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        """String representation of the object."""
        return self.name


class BeverageCenterCode(models.Model):
    """Beverage center codes for item nomenclature. Customer/Dairy/Filling
    station ID. Nomenclature in the item model would
    use this for old nomenclature, or BeverageBrandCode for new.
    """

    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return self.code + " - " + self.name[:15] + "..."


class BeverageBrandCode(models.Model):
    """This replaces the center code for Evergreen items. Acts exactly the same
    way, they're just starting all over. Nomenclature in the item model would
    use this for new nomenclature, or BeverageCenterCode for old.
    """

    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return (
            self.code + " (" + self.highest_end_code() + ") - " + self.name[:18] + "..."
        )

    def highest_end_code(self):
        """Returns the highest end code assigned to an item with the given
        brand code. Used for analysts to figure out which codes are already in use.
        For example: for items X-A212-001, X-A212-002, X-A212-003: return 003.
        """
        # Filter out any end codes containing non-digit characters.
        items_with_brand_code = self.item_set.filter(
            bev_end_code__regex=r"^\d*$"
        ).order_by("-bev_end_code")
        # items_with_brand_code = self.item_set.all().order_by('-bev_end_code')
        if items_with_brand_code:
            return items_with_brand_code[0].bev_end_code
        else:
            return "None"


class BeverageLiquidContents(models.Model):
    """Actual liquid contents of a carton (ie. Low Fat Milk, Heavy Cream, Orange
    Juice...) This code goes on the end of the item nomenclature.
    """

    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return self.code + " - " + self.name[:12] + "..."


class Customer(models.Model):
    """Customer information links jobs together with more than just the job name."""

    name = models.CharField(max_length=255)
    printgroup = models.CharField(max_length=255, blank=True)
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)
    primary_salesperson = models.CharField(max_length=255, blank=True)
    comments = models.TextField(max_length=5000, blank=True)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return self.name


class JobComplexity(models.Model):
    """A job complexity report that tells us what sort of job we're starting with
    and how much work it will be. We're making this a stand-alone model because
    we've been told it could change a lot going forward so we want it
    semi-decoupled from the existing job model.
    """

    job = models.ForeignKey("Job", on_delete=models.CASCADE)
    # What sort of job we're starting with.
    category = models.CharField(
        max_length=100, choices=COMPLEXITY_CATEGORIES, blank=True
    )
    # How much work we think it will be.
    complexity = models.CharField(
        max_length=100, choices=COMPLEXITY_OPTIONS, blank=True
    )

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Job Complexity"

    def __unicode__(self):
        return "%s %s" % (self.job.id, self.category)


class JobAddress(AddressValidationModel):
    """Addresses tied specifically to a Job. If proofs are to be sent out via
    Fedex, these are the addresses to be used.
    This was intentionally separate from the Address App, so that addresses can
    be changed and not affect multiple jobs.
    """

    job = models.ForeignKey("Job", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=100, blank=True)
    # Not all countries use postal/zip codes
    zip = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=255)
    phone = models.CharField(max_length=255, blank=True, null=True)
    ext = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    cell_phone = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Job Addresses"

    def __str__(self):
        return "%s %s" % (self.job, self.name)

    def do_create_joblog_entry(self, job_id, logtype, user_override=None):
        """Abstraction for creating joblog entries for items."""
        new_log = JobLog()
        # Reference to the item's job.
        new_log.job = job_id
        # Get the current user from threadlocals.
        if user_override:
            # Sets user to be gchubadmin in the case of scripted events.
            new_log.user = user_override
        else:
            # Get the current user from threadlocals.
            log_user = threadlocals.get_current_user()
            if not log_user:
                # Prevent the is_authenticated from happening on a None.
                pass
            elif not log_user.is_authenticated:
                # This should catch AnonymousUser objects
                pass
            else:
                new_log.user = log_user

        # Textual log type.
        new_log.type = logtype
        # Accompanying log message.
        new_log.log_text = "Shipping address was added to the job."
        new_log.save()

    def copy_to_contacts(self):
        """Copy address over to address app. (Unattached to jobs)"""
        if self.title is None:
            self.title = ""
        if self.address2 is None:
            self.address2 = ""
        if self.state is None:
            self.state = ""
        if self.zip is None:
            self.zip = ""
        if self.phone is None:
            self.phone = ""
        if self.ext is None:
            self.ext = ""
        if self.email is None:
            self.email = ""

        first_name = self.name.split()[0]
        last_name = self.name.split()[1]
        new_contact = Contact(
            first_name=first_name,
            last_name=last_name,
            job_title=self.title,
            company=self.company,
            address1=self.address1,
            address2=self.address2,
            city=self.city,
            state=self.state,
            zip_code=self.zip,
            country=self.country,
            phone=self.phone,
            ext=self.ext,
            email=self.email,
        )
        new_contact.save()
        return new_contact

    def get_shipments(self):
        """Returns a list of shipments associated with this JobAddress. Can't just
        use a typical reverse _set attribute since it's a Generic relation.
        """
        jobaddress_type = ContentType.objects.get_for_model(self)
        return Shipment.objects.filter(
            address_content_type=jobaddress_type, address_id=self.id
        )


def jobaddress_post_save(sender, instance, created, *args, **kwargs):
    """Things to do after a JobAddress object is saved."""
    # Save job to trigger keyword generation.
    instance.job.save()


class ItemColor(models.Model):
    """Colors used in an item."""

    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    definition = models.ForeignKey(
        ColorDefinition, on_delete=models.CASCADE, blank=True, null=True
    )
    color = models.CharField(max_length=255)
    # Calculated from RGB values given through Backstage XML ink coverage file.
    hexvalue = models.CharField(max_length=12, blank=True)
    # BEV specific -- used for plate ordering.
    sequence = models.IntegerField(blank=True, null=True)
    plate_code = models.CharField(max_length=255, blank=True)
    # More data captured from the Backstage XML ink coverage file.
    coverage_sqin = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True
    )
    coverage_perc = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True
    )
    lpi = models.CharField(max_length=5, blank=True)
    angle = models.CharField(max_length=5, blank=True)
    num_plates = models.IntegerField(blank=True, null=True)
    measured_lab_l = models.FloatField(blank=True, null=True)
    measured_lab_a = models.FloatField(blank=True, null=True)
    measured_lab_b = models.FloatField(blank=True, null=True)
    delta_e = models.FloatField(blank=True, null=True)
    delta_e_passes = models.BooleanField(blank=True, default=False)
    proof_out_override_reason = models.TextField(blank=True, null=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Item Colors"
        ordering = ["id"]

    def __str__(self):
        try:
            return "%s - %s" % (str(self.item), str(self.color))
        except Item.DoesNotExist:
            return "Unknown Item - %s" % str(self.color)

    def fsb_display_name(self):
        """Return a color name for Foodservice display, adding GCH- or PMS- where
        applicable.
        """
        """
        Try and see if the color is a number, if not then set ten mill to letters so it fails the regex check
        for ten mill numbers. We have to use a try catch here cause it will error if it is a string.

        These are old checks that we have since gone away with but I am noting in case we need them again:

            or self.color.lower().startswith('dpe') \
            or self.color.lower().startswith('mcd') \
            or self.color.lower().startswith('gpi') \
            or colorCheck.lower().startswith('pms') \
            or re.match(r'^\\d{5}$', colorCheck) \\
        """
        # This check is for all of the HAVI colors that have underscores
        colorCheck = self.color.split("_")

        # check and see if the color is a 10 million number with regex and return Special Match if it is
        if re.match(r"^\d{7,8}$", self.color):
            return self.color
        elif (
            self.color.lower().startswith("qpo")
            or self.color.lower().startswith("var")
            or self.color.lower().startswith("ext")
            or len(colorCheck) > 1
            or self.item.get_inkbook_display().lower() == "other"
        ):
            return self.color
        else:
            return "%s %s" % (str(self.item.get_inkbook_display()), str(self.color))

    def calculated_lch(self):
        """From the given measured Lab values, calculate the C value."""
        if self.measured_lab_l:
            lab = LabColor(
                self.measured_lab_l, self.measured_lab_a, self.measured_lab_b
            )
            lch = convert_color(lab, LCHabColor)
            return lch
        else:
            return None

    def calculate_plate_code(self):
        """Calculate and populate plate_code for FSB ItemColor objects."""
        if self.item.job.workflow.name == "Foodservice":
            if self.item.fsb_nine_digit:
                plate_code = self.item.fsb_nine_digit
            else:
                plate_code = ""
            # Determine sequence code.
            code_seqs = (
                (1, "A"),
                (2, "B"),
                (3, "C"),
                (4, "D"),
                (5, "E"),
                (6, "F"),
                (7, "G"),
                (8, "H"),
                (9, "I"),
                (10, "J"),
            )
            if self.sequence:
                # Pull sequence code from dictionary.
                seq_code = code_seqs[self.sequence - 1][1]
            else:
                # Will need to determine sequence code based on ink order.
                seq_code = "X"
            plate_code += " 1%s" % seq_code
            self.plate_code = plate_code
            self.save()
            return plate_code


class ColorWarning(models.Model):
    pantone_color = models.CharField(max_length=64)
    definition = models.ForeignKey(
        ColorDefinition, on_delete=models.CASCADE, blank=True, null=True
    )
    date_added = models.DateTimeField(auto_now_add=True)
    qpo_number = models.CharField(max_length=32)
    active = models.BooleanField(default=True)
    notes = models.TextField(max_length=500, blank=True, null=True)
    # Dismissed items won't get re-activated over night.
    dismissed = models.BooleanField(blank=True, default=False)
    dismissal_notes = models.TextField(max_length=500, blank=True, null=True)

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Color Warning"
        ordering = ["definition"]

    def __str__(self):
        try:
            return "%s" % (str(self.definition))
        except Item.DoesNotExist:
            return "Unknown Item - %s" % str(self.definition)


def itemcolor_post_save(sender, instance, created, *args, **kwargs):
    """Things to do after a ItemColor object is saved."""
    # Save job to trigger keyword generation.
    instance.item.job.save()


class ItemReview(models.Model):
    """Tracks item review status."""

    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    review_types = (
        ("plant", "Plant Review"),
        ("demand", "Demand Review"),
        ("market", "Marketing Review"),
    )
    review_catagory = models.CharField(max_length=20, choices=review_types)
    entry_comments = models.CharField(max_length=500, blank=True)
    comments = models.CharField(max_length=500, blank=True)
    resub_comments = models.CharField(max_length=500, blank=True)
    review_initiated_date = models.DateTimeField(
        "Date Review Initiated", auto_now_add=True
    )
    review_date = models.DateField("Date Reviewed", blank=True, null=True)
    review_ok = models.BooleanField(default=False)
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="reviewer_test",
    )
    resubmitted = models.BooleanField(default=False)

    class Meta:
        app_label = "workflow"

    def __str__(self):
        return "%s -%s - %s" % (
            str(self.item.job),
            str(self.item),
            str(self.review_catagory),
        )

    def status(self):
        """Determines if the review is approved, rejected, waiting, or expired.
        Also returns icon name so it can be displayed with the status.
        """
        status = {}
        # If it's approved then it's approved. Easy!
        if self.review_ok:
            status["status"] = "OK"
            status["icon"] = "accept"
        # If it's not approved but it has a review date then it's rejected.
        elif self.review_date:
            status["status"] = "Rejected"
            status["icon"] = "exclamation"
        # If it's not approved or rejected check if it's expired.
        elif general_funcs._utcnow_naive() > self.expires():
            status["status"] = "Time Expired"
            status["icon"] = "hourglass"
        # Otherwise keep waiting.
        else:
            status["status"] = "Waiting"
            status["icon"] = "control_pause"

        return status

    def do_ok(self, update_type, comment=False):
        """Function for handling market review objects being accepted,
        rejected, or resubmitted. Results are listed on the Review page.
        """
        self.review_date = date.today()

        # Set up some growl info.
        cat = self.review_catagory
        cat = cat.capitalize()
        if self.review_catagory == "plant":
            whom = "The plant"
        elif self.review_catagory == "demand":
            whom = "Demand planning"
        elif self.review_catagory == "market":
            whom = "Marketing"
        else:
            whom = "unknown"

        # Handles the review being accepted, rejected, or resubbed.
        if update_type == "accept":
            self.review_ok = True
            self.comments = "Accepted: %s" % comment
            self.reviewer = threadlocals.get_current_user()

            # If they supplied comments make a joblog entry.
            log_text = "Artwork for item %s has been accepted by %s." % (
                self.item.num_in_job,
                whom.lower(),
            )
            if comment:
                log_text = log_text + " " + comment
            self.item.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, log_text)

            # If marketing review is accepted.
            if self.review_catagory == "market":
                # Compose Email Approval Notice to Artist when marketing approves
                mail_subject = "%s - %s Approval Notice" % (cat, str(self.item.job.id))
                mail_body = loader.get_template("emails/marketing_review_approved.txt")
                mail_list = []

                # Check For an Artist's email
                # If not, email front desk so approval is seen somewhere
                if self.item.job.artist:
                    mail_list.append(self.item.job.artist.email)
                else:
                    fd_group = User.objects.filter(
                        groups__name="EmailGCHubFrontDesk", is_active=True
                    )
                    for user in fd_group:
                        mail_list.append(user.email)
                # Fill in email template vars
                mail_context = {
                    "reviewer": whom,
                    "job_name": self.item.job.name,
                    "job_id": str(self.item.job.id),
                    "item_num": str(self.item.num_in_job),
                    "item_review": str(self),
                    "site_link": "http://gchub.graphicpkg.com/workflow/mkt_review/",
                }

                # if mail list is empty add me to it and note an error occured.
                if len(mail_list) == 0:
                    mail_list = ["jacey.r.harris@graphicspkg.com"]
                    mail_subject = "Error with " + mail_subject

                email = EmailMessage(
                    mail_subject,
                    mail_body.render(mail_context),
                    settings.EMAIL_FROM_ADDRESS,
                    mail_list,
                )
                # email.attach_file('filename.xls')

                # Send
                email.send(fail_silently=False)

        elif update_type == "reject":
            self.review_ok = False
            self.reviewer = threadlocals.get_current_user()
            self.comments = comment
            log_text = "Artwork for item %s has been rejected by %s." % (
                self.item.num_in_job,
                whom.lower(),
            )
            # Log this event, along with the warnings and comments.
            if comment:
                log_text = log_text + " " + comment
            self.item.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, log_text)

            # Send a growl notification to the artist.
            self.item.job.growl_at_artist(
                "%s Rejection Notice" % cat,
                "%s has rejected artwork for %s, %s-%s %s."
                % (
                    whom,
                    self.item.job.name,
                    str(self.item.job.id),
                    str(self.item.num_in_job),
                    str(self),
                ),
                pref_field="growl_hear_plant_rejections",
            )

        elif update_type == "resub":
            # Resubmitted items are available again for Accept or Reject.
            # A new item review object is created and the old one is hidden away.
            # That way we have the old object to look back at and see why it was
            # rejected in the first place.
            new_review = ItemReview()
            new_review.item = self.item
            new_review.review_catagory = self.review_catagory
            new_review.entry_comments = self.entry_comments
            new_review.comments = "Resubmitted"
            if self.review_catagory == "market":
                new_review.resub_comments = comment
            else:
                pass
            new_review.review_date = self.review_date
            new_review.reviewer = threadlocals.get_current_user()
            new_review.save()
            self.resubmitted = True

        elif update_type == "dismiss":
            # Dismiss a review that was rejected. This was requested for
            # items that were rejected and then abandoned.
            # We're going to cheat a bit here. dismissed items will work exactly
            # like resubmitted items but a new item review object won't be
            # created.
            self.resubmitted = True
            self.resub_comments = comment + " *Review dismissed*"

        return super(ItemReview, self).save()

    def expires(self):
        """Calculates when a review will expire based on allowing three business
        days. Mostly this is just to help skip weekends.
        """
        start_date = self.review_initiated_date
        if start_date.isoweekday() == 6:
            # If it's Saturday skip Sunday.
            exp_date = start_date + timedelta(4)
        elif start_date.isoweekday() >= 3 and start_date.isoweekday() <= 5:
            # If it's between Wednesday and Friday skip the whole weekend.
            exp_date = start_date + timedelta(5)
        else:
            # Otherwise just go forward days back.
            exp_date = start_date + timedelta(3)

        return exp_date


class Revision(models.Model):
    """Proof revision tracking."""

    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    creation_date = models.DateTimeField("Date Entered", auto_now_add=True)
    due_date = models.DateField("Due Date")
    complete_date = models.DateField("Complete Date", blank=True, null=True)
    comments = models.TextField()
    entered_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        editable=False,
        related_name="rev_entered_by",
    )

    class Meta:
        app_label = "workflow"
        get_latest_by = "creation_date"

    def complete_revision(self):
        self.complete_date = date.today()
        return self.save()

    def __str__(self):
        return str(self.item) + " - " + str(self.creation_date.date())


def revision_post_save(sender, instance, created, *args, **kwargs):
    """Things to do after a Revision object is saved."""
    # Save job to trigger keyword generation.
    instance.item.job.save()


"""
--- Dispatchers
"""
signals.post_save.connect(revision_post_save, sender=Revision)
signals.post_save.connect(itemcolor_post_save, sender=ItemColor)
signals.post_save.connect(jobaddress_post_save, sender=JobAddress)
