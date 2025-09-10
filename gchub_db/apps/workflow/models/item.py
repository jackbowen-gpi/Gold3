import os
import re
import shutil
from datetime import date, timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.db.models import Q, signals
from django.template import loader
from django.urls import reverse
from django.utils import timezone

from gchub_db.apps.auto_ftp.models import (
    DESTINATION_CYBER_GRAPHICS,
    DESTINATION_FUSION_FLEXO,
    DESTINATION_PHOTOTYPE,
    DESTINATION_SOUTHERN_GRAPHIC,
)

from gchub_db.apps.joblog.app_defs import (
    JOBLOG_TYPE_ITEM_9DIGIT,
    JOBLOG_TYPE_ITEM_ADDED,
    JOBLOG_TYPE_ITEM_APPROVED,
    JOBLOG_TYPE_ITEM_DELETED,
    JOBLOG_TYPE_ITEM_FILED_OUT,
    JOBLOG_TYPE_ITEM_FORECAST,
    JOBLOG_TYPE_ITEM_PREFLIGHT,
    JOBLOG_TYPE_ITEM_PROOFED_OUT,
    JOBLOG_TYPE_ITEM_REVISION,
    JOBLOG_TYPE_ITEM_SAVED,
    JOBLOG_TYPE_JOBLOG_DELETED,
    JOBLOG_TYPE_NOTE,
    JOBLOG_TYPE_PRODUCTION_EDITED,
)
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.qad_data import qad
from gchub_db.apps.queues.models import ColorKeyQueue
from gchub_db.apps.workflow import fsb_template_maker, workflow_funcs
from gchub_db.apps.workflow.app_defs import (
    COMPLEXITY_OPTIONS,
    GDD_ORIGINS,
    INKBOOKS,
    KD_PRESSES,
    PANTONE,
    PLATE_TYPE_RUBBER_FLEXO,
    PROOF_TYPES,
    SITUATION_OPTIONS,
)
from gchub_db.apps.workflow.managers import ItemManager
from gchub_db.apps.workflow.models.general import (
    BevItemColorCodes,
    Charge,
    ChargeType,
    ItemCatalog,
    ItemSpec,
    PlateOrder,
    PlateOrderItem,
    Revision,
    StepSpec,
)
from gchub_db.apps.workflow.models import ItemTracker
from gchub_db.apps.xml_io.jdf_writer import ItemJDF
from gchub_db.apps.xml_io.jmf import JMFSubmitQueueEntry
from gchub_db.includes import fs_api, general_funcs
from gchub_db.includes.fs_api import InvalidPath
from gchub_db.middleware import threadlocals

if TYPE_CHECKING:
    from .general import ItemColor, ItemReview


class Item(models.Model):
    """Represents an Item, which is associated to a Job."""

    # Type annotations for Django reverse relationships
    if TYPE_CHECKING:
        itemcolor_set: models.Manager[ItemColor]
        itemreview_set: models.Manager[ItemReview]
        steps_with_item: models.Manager["Item"]

    # Workflow FK unused currently, but may be usefull down the road. ie, job
    # with FSB and Cont. work.
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)
    job = models.ForeignKey("Job", on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    # Very important field -- used to determine the ID of the job as it
    # will be accessed on the fileserver.
    # (ie job.id-item.num_in_job : 54321-2 XXX.pdf)
    num_in_job = models.IntegerField(blank=True, null=True, editable=False)
    size = models.ForeignKey("ItemCatalog", on_delete=models.CASCADE)
    creation_date = models.DateTimeField("Date Entered", auto_now_add=True)
    # lookup from Item Catalog ... replaces 'material' from container
    item_type = models.CharField(max_length=100, blank=True)
    printlocation = models.ForeignKey(
        "PrintLocation", on_delete=models.CASCADE, blank=True, null=True
    )
    platepackage = models.ForeignKey(
        "PlatePackage", on_delete=models.CASCADE, blank=True, null=True
    )
    special_mfg = models.ForeignKey(
        "SpecialMfgConfiguration", on_delete=models.CASCADE, blank=True, null=True
    )
    upc_number = models.CharField(max_length=255, blank=True)
    upc_ink_color = models.CharField(max_length=20, blank=True)
    ink_usage = models.ManyToManyField("ItemColor", related_name="ink_set", blank=True)
    # fsb: yes/no  bev: actual po number per job
    po_number = models.CharField(max_length=20, blank=True)
    path_to_file = models.CharField(max_length=255, blank=True)
    item_status = models.CharField(max_length=100, default="Pending")
    preflight_date = models.DateField("preflight date", blank=True, null=True)
    preflight_ok = models.BooleanField(default=False)
    electronic_proof_date = models.DateField(
        "electronic proof date", blank=True, null=True
    )
    file_delivery_date = models.DateField("file delivery date", blank=True, null=True)
    # fsb specific
    case_pack = models.IntegerField(blank=True, null=True)
    press_change = models.BooleanField(default=False)
    annual_use = models.IntegerField(blank=True, null=True)
    render = models.BooleanField(default=False)
    wrappable_proof = models.BooleanField(default=False)
    mock_up = models.BooleanField(default=False)
    label_color = models.CharField(max_length=255, blank=True)
    noise_filter = models.BooleanField(default=True)
    quality = models.CharField(max_length=1, choices=COMPLEXITY_OPTIONS, blank=True)
    fsb_nine_digit = models.CharField(max_length=25, blank=True, null=True)
    fsb_nine_digit_date = models.DateField(
        "fsb nine digit creation date", blank=True, null=True
    )
    wrin_number = models.CharField(max_length=255, blank=True)
    sap_number = models.CharField(max_length=25, blank=True)
    # bom_number is Beverage=specific but is being used by
    # Foodservice: labeled "SCC Number"
    bom_number = models.CharField(max_length=255, blank=True)
    floor_stock = models.BooleanField(default=False)  # fsb
    replaces = models.CharField(max_length=255, blank=True, null=True)
    overdue_exempt = models.BooleanField(default=False)
    overdue_exempt_reason = models.CharField(max_length=500, blank=True)
    file_out_exempt = models.BooleanField(default=False)
    file_out_exempt_reason = models.CharField(max_length=500, blank=True)
    # container specific
    length = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    width = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    height = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    ect = models.IntegerField(blank=True, null=True)
    last_modified = models.DateTimeField("Date Last Modified", auto_now=True)
    plant_comments = models.CharField(max_length=500, blank=True)
    plant_reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="plant_reviewer",
    )
    plant_review_date = models.DateField("Plant Review Date", blank=True, null=True)
    num_up = models.IntegerField(blank=True, null=True)
    # Beverage specific naming fields.
    # We'll use this to store the bev_nomenclature() for searching.
    bev_item_name = models.CharField(max_length=255, blank=True)
    bev_imported_item_name = models.CharField(max_length=255, blank=True)
    # Beverage carton specific.
    bev_center_code = models.ForeignKey(
        "BeverageCenterCode", on_delete=models.CASCADE, blank=True, null=True
    )
    bev_liquid_code = models.ForeignKey(
        "BeverageLiquidContents", on_delete=models.CASCADE, blank=True, null=True
    )
    # Beverage panel specific.
    bev_panel_center = models.CharField(max_length=255, blank=True)
    bev_panel_end = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    bev_alt_code = models.CharField(max_length=255, blank=True)
    num_colors_req = models.IntegerField(blank=True, null=True)
    material = models.CharField(max_length=255, blank=True)
    assignment_date = models.DateField(
        "Date Printlocation Assigned", blank=True, null=True
    )
    demand_plan_date = models.DateField("Demand Planning Date", blank=True, null=True)
    demand_plan_ok = models.BooleanField(default=False)
    demand_plan_comments = models.CharField(max_length=255, blank=True)
    # Booleans to override default JDF functionality. Originally for Beverage.
    jdf_no_dgc = models.BooleanField(default=False)
    jdf_no_step = models.BooleanField(default=False)
    inkbook = models.IntegerField(choices=INKBOOKS, default=PANTONE)
    # This is the time that the idle proof reminder email was sent.
    proof_reminder_email_sent = models.DateTimeField(
        "Proof Reminder Sent", blank=True, null=True
    )
    # Codes used for Evergreen's new nomenclature effective 10-19-2009.
    bev_brand_code = models.ForeignKey(
        "BeverageBrandCode", on_delete=models.CASCADE, blank=True, null=True
    )
    bev_end_code = models.CharField(max_length=255, blank=True)
    is_queued_for_thumbnailing = models.BooleanField(default=False)
    time_last_thumbnailed = models.DateTimeField(blank=True, null=True)
    disclaimer_text = models.TextField(max_length=5000, blank=True, null=True)
    mkt_review_date = models.DateField("Marketing Review Date", blank=True, null=True)
    mkt_review_ok = models.BooleanField(default=False)
    mkt_review_comments = models.CharField(max_length=500, blank=True)
    mkt_review_needed = models.BooleanField(default=False)
    mkt_review_instructions = models.CharField(max_length=500, blank=True)
    steps_with = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="steps_with_item",
        blank=True,
        null=True,
    )
    # Store Esko's SmartID to check comparison between proof and file out.
    # smartid = models.CharField(max_length=25, blank=True)
    # Status to reflect item situation with customer.
    item_situation = models.IntegerField(
        choices=SITUATION_OPTIONS, blank=True, null=True
    )
    # An error was found in a particular distortion factor. Some match plate
    # jobs will need to keep using this old incorrect distortion so we'll use
    # this to flag them. See legacy_distortion_check().
    uses_old_distortion = models.BooleanField(default=False)
    # Pre-distorted items need to be flagged so they can be routed through
    # their own automation engine workflow.
    uses_pre_distortion = models.BooleanField(default=False)
    kd_press = models.CharField(max_length=50, blank=True, choices=KD_PRESSES)

    # These are the new Carton/Marion project attributes
    one_up_die = models.CharField(max_length=255, blank=True)
    step_die = models.CharField(max_length=255, null=True, blank=True)
    graphic_req_number = models.CharField(max_length=255, null=True, blank=True)
    grn = models.CharField(max_length=255, null=True, blank=True)
    gdd_origin = models.CharField(
        max_length=255, null=True, blank=True, choices=GDD_ORIGINS
    )
    print_repeat = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    location = models.CharField(
        default="Outside", max_length=255, blank=True
    )  # Inside/Outside
    coating_pattern = models.CharField(max_length=255, null=True, blank=True)
    plate_thickness = models.CharField(max_length=255, null=True, blank=True)
    # This field is no longer used. To be removed later.
    process = models.CharField(max_length=255, blank=True)
    # This field is no longer used. To be removed later.
    profile = models.CharField(max_length=255, blank=True)
    upc = models.CharField(max_length=255, blank=True)
    product_group = models.CharField(max_length=255, null=True, blank=True)
    distortion = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    # No longer used. Check the job's workflow instead.
    is_carton = models.BooleanField(default=False)
    proof_type = models.CharField(
        max_length=50, null=True, blank=True, choices=PROOF_TYPES
    )
    proof_type_notes = models.CharField(max_length=500, null=True, blank=True)
    customer_code = models.CharField(max_length=255, null=True, blank=True)
    graphic_po = models.CharField(max_length=255, null=True, blank=True)
    # No longer used.
    sap_ship_to = models.CharField(max_length=255, null=True, blank=True)
    # No longer used.
    sap_sold_to = models.CharField(max_length=255, null=True, blank=True)
    substrate = models.ForeignKey(
        "Substrate", on_delete=models.CASCADE, blank=True, null=True
    )
    gcr = models.BooleanField(default=False)
    ecg = models.BooleanField(default=False)
    carton_workflow = models.ForeignKey(
        "CartonWorkflow", on_delete=models.CASCADE, blank=True, null=True
    )
    line_screen = models.ForeignKey(
        "LineScreen", on_delete=models.CASCADE, blank=True, null=True
    )
    ink_set = models.ForeignKey(
        "InkSet", on_delete=models.CASCADE, blank=True, null=True
    )
    print_condition = models.ForeignKey(
        "PrintCondition", on_delete=models.CASCADE, blank=True, null=True
    )
    trap = models.ForeignKey("Trap", on_delete=models.CASCADE, blank=True, null=True)
    carton_profile = models.ForeignKey(
        "CartonProfile", on_delete=models.CASCADE, blank=True, null=True
    )

    # Custom manager. Found in managers.py.
    objects = ItemManager()

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Items"
        ordering = ["job", "num_in_job"]
        # No duplicate num_in_jobs within a given job.
        # unique_together = (("job", "num_in_job"),)
        permissions = (
            ("can_proof_item", "Can Proof Item"),
            ("can_approve_item", "Can Approve Item"),
            ("can_forecast_item", "Can Forecast Item"),
            ("can_file_out_item", "Can FileOut Item"),
            ("can_edit_item_production", "Can Edit Item Production"),
        )

    def __str__(self):
        return self.get_item_designation()

    def __unicode__(self):
        return self.__str__()

    def get_item_designation(self):
        """Show the correct size/item name depending on the workflow."""
        if self.job.workflow.name == "Beverage":
            return self.bev_item_name
        else:
            return self.size.size

    def calculate_item_distortion(self):
        """This calculates the item distortion based off of the thickness and print repeat value of an item."""
        distortion_dict = {
            "0.045": "0.239",
            "0.067": "0.39",
            "0.107": "0.64089",
        }
        if self.plate_thickness and self.print_repeat:
            dist = 100 * (
                1
                - (
                    float(distortion_dict[self.plate_thickness])
                    / float(self.print_repeat)
                )
            )
            self.distortion = dist
            return super(Item, self).save()

    def get_fiber_tracker(self):
        """Returns any fiber trackers for this item and formats them for display on
        the beverage item nomenclature page.
        """
        try:
            fiber_tracker = ItemTracker.objects.get(
                item=self, type__category__name="Beverage Fiber"
            )
        except Exception:
            fiber_tracker = None
        return fiber_tracker

    def get_nutrition_facts(self):
        """Returns any nutrition facts for this item and formats them for display on
        the beverage item nomenclature page.
        """
        try:
            ItemTracker.objects.get(
                item=self, type__category__name="Beverage Nutrition"
            )
            nutrition_facts = True
        except Exception:
            nutrition_facts = False
        return nutrition_facts

    def get_num_colors_carton(self):
        """ "Coating" inks don't count towards billing for carton items. This
        returns the number of colors in an item minus any that say "coating" in
        the name.
        """
        colors = self.itemcolor_set.exclude(definition__name__icontains="coating")
        return colors.count()

    def get_label_tracker(self):
        """Returns any item trackers for this item and formats them for display on
        the beverage item nomenclature page.
        """
        try:
            label_tracker = ItemTracker.objects.get(
                item=self, type__category__name="Beverage Label"
            )
        except Exception:
            label_tracker = None
        return label_tracker

    def get_absolute_url(self):
        """Returns a URL to the item's display page."""
        return reverse("job_detail", args=[self.num_in_job])

    def delete(self, using=None, keep_parents=False):
        """Deleting Item objects causes a chain of deletions for all objects
        with Foreignkey fields pointing to Item. This results in a lot of data
        loss. Set an is_deleted flag on the item instead and filter out all
        "deleted" Item objects as needed.
        """
        self.is_deleted = True
        saved_item = super(Item, self).save()
        self.job.recalc_item_numbers()

        # Log Item saves.
        new_log = JobLog()
        new_log.job = self.job
        # Instance is a copy of the item being saved.
        new_log.item = self
        # Grab the user doing the saving from threadlocals.

        new_log.user = threadlocals.get_current_user()
        new_log.type = JOBLOG_TYPE_ITEM_DELETED
        new_log.log_text = "Item %s has been deleted." % (self.size.size)
        new_log.save()

        return saved_item

    def copy_new_die_tiff(self):
        """Determines and copies a standard die tiff to the 1_Bit_Tiffs folder for
        the item for proofing.
        """
        # Rubber and conventional plates have slightly different distortions.
        # Use different die tiffs based on plate types. These are sub-directories
        # under each platemaker/size directory.
        if self.platepackage.platetype == PLATE_TYPE_RUBBER_FLEXO:
            plate_type_dir = "Rubber"
        else:
            plate_type_dir = "Conventional"

        # Path to the die tiff that will replace the item's existing one
        # Panels are in a separate directory. Platemaker and num_up independent.
        if self.size.is_bev_panel():
            # A couple of the plants need goofy side panels.
            plantdesignation = ""
            if self.printlocation.plant.name in ("Clinton", "Olmsted Falls"):
                plantdesignation = "_%s" % self.printlocation.plant.name
            # Directory containing tiffs and viewer data
            new_die_tiff_parent = os.path.join(
                settings.TIFF_TO_PDF_DIES_DIR, "Panels", plate_type_dir
            )
            # Name of the tiff
            new_die_tiff_filename = "%s_%dup%s_die.tif" % (
                self.size.get_stripped_size(),
                self.num_up,
                plantdesignation,
            )
            # Path to tiff
            new_die_tiff_path = os.path.join(new_die_tiff_parent, new_die_tiff_filename)
            # Name of the meta file
            new_die_tiff_meta_filename = ".%s.info" % (new_die_tiff_filename)
            # Path to viewer data.
            new_die_view_parent = os.path.join(
                new_die_tiff_parent, ".view", new_die_tiff_filename
            )
            new_die_meta_parent = os.path.join(
                new_die_tiff_parent, ".metadata", new_die_tiff_meta_filename
            )
        else:
            # Cartons are filed by platemaker and number up.
            die_name = self.size.get_stripped_size()
            # Raleigh has a different pinhole configuration. Diff. master dies.
            # Only applies to 2ups, 4, 6 & 8 oz eco sizes.
            if self.num_up == 2:
                # Use die_name, cause it's already neat and tidy.
                if die_name in ("4oz-eco", "6oz-eco", "8oz-eco"):
                    if self.job.temp_printlocation.plant.name == "Raleigh":
                        die_name += "-raleigh"
            # Check if the item uses legacy distortion and point it to those dies.
            if self.uses_old_distortion:
                die_name += "-legacy"
            if self.special_mfg:
                die_name = die_name.replace("-eco", "")
                die_name += "-" + str(self.special_mfg.name).lower()
            # If the item is predistorted the die will be in a predistorted subfolder.
            if self.uses_pre_distortion:
                predist = "predistorted"
            else:
                predist = ""
            # Build the path to the master die.
            new_die_tiff_parent = os.path.join(
                settings.TIFF_TO_PDF_DIES_DIR,
                "%s_%s_%dup"
                % (
                    self.platepackage.platemaker.name,
                    self.printlocation.plant.name,
                    self.num_up,
                ),
                plate_type_dir,
                predist,
            )
            new_die_tiff_filename = "%s_die.tif" % (die_name)
            new_die_tiff_meta_filename = ".%s_die.tif.info" % (die_name)
            new_die_tiff_path = os.path.join(new_die_tiff_parent, new_die_tiff_filename)

            new_die_view_parent = os.path.join(
                new_die_tiff_parent, ".view", new_die_tiff_filename
            )
            new_die_meta_parent = os.path.join(
                new_die_tiff_parent, ".metadata", new_die_tiff_meta_filename
            )

        tiff_folder = fs_api.find_item_folder(
            self.job.id, self.num_in_job, search_dir="tiffs"
        )
        tiff_filename = "%d-%d %s_die.tif" % (
            self.job.id,
            self.num_in_job,
            self.bev_nomenclature(),
        )
        tiff_meta_filename = ".%d-%d %s_die.tif.info" % (
            self.job.id,
            self.num_in_job,
            self.bev_nomenclature(),
        )

        try:
            # Path to the item's existing die tiff
            item_die_tiff = fs_api.get_item_tiff_path(
                self.job.id, self.num_in_job, ".*die.tif"
            )
        except fs_api.NoResultsFound:
            item_die_tiff = os.path.join(tiff_folder, tiff_filename)

        item_die_tiff_view = os.path.join(tiff_folder, ".view", tiff_filename)
        item_die_tiff_meta = os.path.join(tiff_folder, ".metadata", tiff_meta_filename)

        # Copy the new die over the item's existing die tiff.
        if self.jdf_no_step:
            # Do not copy over the existing die if RIP only. (no step)
            pass
        else:
            try:
                print(("parent source %s" % (new_die_tiff_path)))
                print(("parent dest %s" % (item_die_tiff)))
                shutil.copy2(new_die_tiff_path, item_die_tiff)
            except Exception:
                pass
            # copy over the view folder
            print(("view source %s" % (new_die_view_parent)))
            print(("view dest %s" % (item_die_tiff_view)))
            try:
                if os.path.exists(item_die_tiff_view):
                    # If there's old view data in the destination folderremove
                    # it first.
                    print("Removing old view data first.")
                    shutil.rmtree(item_die_tiff_view)
                shutil.copytree(new_die_view_parent, item_die_tiff_view)
            except Exception:
                pass
            # copy over the metadata folder
            print(("meta source %s" % (new_die_meta_parent)))
            print(("meta dest %s" % (item_die_tiff_meta)))
            try:
                shutil.copy(new_die_meta_parent, item_die_tiff_meta)
            except Exception:
                pass

            print("Done")

    def create_folder(self):
        """Creates the item's folder and any other related folders (proofs, etc.)."""
        # For Beverage jobs, use their cheesy beverage
        # nomenclature for folders.
        if self.workflow.name == "Beverage":
            folder_name = self.bev_nomenclature()
        else:
            # Foodservice and Container are sane and use the size name.
            folder_name = self.size.size

        # Create folders.
        fs_api.create_item_folder(self.job.id, self.num_in_job, folder_name)

    def rename_folder(self):
        # For Beverage jobs, use their cheesy beverage
        # nomenclature for folders.
        if self.workflow.name == "Beverage":
            folder_name = self.bev_nomenclature()
        else:
            # Foodservice and Container are sane and use the size name.
            folder_name = self.size.size
        # rename item folders.
        message = fs_api.rename_item_folders(self.job.id, self.num_in_job, folder_name)
        return message

    def delete_folder(self):
        """Re-name the old folder to preserve the files. Give it a timestamp
        to avoid future over-writes if the same item number is deleted again.
        """
        renamed_name = "%s Deleted %s" % (
            self.size.size,
            timezone.now().strftime("%m-%d-%Y %H:%M"),
        )

        try:
            # The Final Files Item folder is important enough to be saved.
            fs_api.rename_item_folder(
                self.job.id, self.num_in_job, renamed_name, remove_itemnum_prefix=True
            )
        except fs_api.NoResultsFound:
            # Sometimes the folder gets deleted or re-named by the artist.
            pass
        except fs_api.InvalidPath:
            pass

        try:
            # Look through the Job folder and delete matching item folders.
            fs_api.delete_item_folders(self.job.id, self.num_in_job)
        except fs_api.InvalidPath:
            pass

    def get_folder(self):
        """Returns the path to the item's folder."""
        return fs_api.find_item_folder(self.job.id, self.num_in_job)

    def bev_nomenclature(self):
        """Return the field value for bev_item_name. Searchable!"""
        return self.bev_item_name

    def recalc_bev_nomenclature_ext(self):
        """Build the Evergreen nomenclature from size/color, center code, &
        end code. Using the external method in workflow_funcs.py -- this has
        been made external to facilitate the calculation of a nomenclature for
        Beverage work without actually having an item saved (ie. while the
        analyst is entering it).
        """
        num_colors = self.itemcolor_set.count()
        bev_itemcolorcode = BevItemColorCodes.objects.get(
            size=self.size, num_colors=num_colors
        )
        return workflow_funcs.recalc_bev_nomenclature(
            self.size,
            bev_itemcolorcode,
            self.printlocation,
            self.platepackage,
            self.bev_alt_code,
            self.bev_center_code,
            self.bev_liquid_code,
            self.job.prepress_supplier,
        )

    def recalc_bev_nomenclature(self):
        """Build the Evergreen nomenclature from size/color, center code,
        & end code.
        """
        num_colors = ItemColor.objects.filter(item=self).count()
        nomenclature = "NO PL"
        if self.printlocation:
            if self.size.is_bev_panel():
                if self.bev_alt_code:
                    # Optional code that analyst can enter for panels.
                    item_code = self.bev_alt_code
                else:
                    if self.platepackage.platemaker.name == "Shelbyville":
                        item_code = "SV"
                    elif self.platepackage.platemaker.name == "Fusion Flexo":
                        item_code = "FF"
                    elif self.platepackage.platemaker.name == "Cyber Graphics":
                        item_code = "CY"
                    elif self.platepackage.platemaker.name == "Southern Graphic":
                        item_code = "SG"
                    elif self.platepackage.platemaker.name == "Phototype":
                        item_code = "PT"
                    else:
                        item_code = "Panel"
                nomenclature = (
                    item_code
                    + "-"
                    + str(self.bev_center_code.code)
                    + "-"
                    + str(self.bev_liquid_code.code)
                )
            # Else, assume carton.
            else:
                if self.printlocation.plant.name in ("Plant City"):
                    # Items printing in Plant City & Raleigh have entirely
                    # different naming.
                    try:
                        item_code = self.bev_alt_code
                    except Exception:
                        item_code = "HE Carton"
                    nomenclature = item_code
                elif (
                    self.printlocation.plant.name in ("Raleigh")
                    and self.printlocation.press.name == "BHS"
                ):
                    # Use bev_alt_code as the default nomenclature.
                    try:
                        item_code = self.bev_alt_code
                    except Exception:
                        item_code = "HE Carton"
                    nomenclature = item_code
                    # Disabled 9-23-2010.
                    """
                    if self.job.prepress_supplier in ('Optihue', '', None,
                                                      'OPT'):
                        nomenclature = item_code + "CGH"
                    # Raleigh BHS, handled by Phototype
                    elif self.job.prepress_supplier in ('Phototype',
                                                        'PHT'):
                        nomenclature = item_code + "PT"
                    # Raleigh BHS, handled by Southern Graphics.
                    elif self.job.prepress_supplier in ('Southern Graphics',
                                                        'SGS',):
                        nomenclature = item_code + "SG"
                    # Raleigh BHS, handled by Schawk.
                    elif self.job.prepress_supplier in ('Schawk',
                                                        'SHK',):
                        nomenclature = item_code + "ST"
                    """

                else:
                    # This will be most items.
                    try:
                        lookup_code = BevItemColorCodes.objects.get(
                            size=self.size, num_colors=num_colors
                        )
                        item_code = lookup_code.code
                    except BevItemColorCodes.DoesNotExist:
                        item_code = "Carton"
                    nomenclature = item_code
                    if self.bev_center_code:
                        nomenclature = "%s-%s" % (
                            nomenclature,
                            self.bev_center_code.code,
                        )
                    if self.bev_liquid_code:
                        nomenclature = "%s-%s" % (
                            nomenclature,
                            self.bev_liquid_code.code,
                        )
        return nomenclature.replace(" ", "")

    def new_bev_nomenclature(self):
        """Build the new Evergreen nomenclature from size/color, center code,
        and end code. Effective 10/2009.
        """
        num_colors = ItemColor.objects.filter(item=self).count()
        if self.printlocation:
            if self.size.is_bev_panel():
                if self.bev_alt_code:
                    # Optional code that analyst can enter for panels.
                    item_code = self.bev_alt_code
                else:
                    if self.platepackage.platemaker.name == "Shelbyville":
                        item_code = "SV"
                    elif self.platepackage.platemaker.name == "Fusion Flexo":
                        item_code = "FF"
                    elif self.platepackage.platemaker.name == "Cyber Graphics":
                        item_code = "CY"
                    elif self.platepackage.platemaker.name == "Southern Graphic":
                        item_code = "SG"
                    elif self.platepackage.platemaker.name == "Phototype":
                        item_code = "PT"
                    else:
                        item_code = "Panel"
                nomenclature = (
                    item_code
                    + "-"
                    + str(self.bev_brand_code.code)
                    + "-"
                    + str(self.bev_end_code)
                )
            # Else, assume carton.
            else:
                if self.printlocation.plant.name in ("Plant City"):
                    # Items printing in Plant City have entirely
                    # different naming.
                    try:
                        item_code = self.bev_alt_code
                    except Exception:
                        item_code = "HE Carton"
                    nomenclature = item_code
                # Raleigh BHS work uses unique codes.
                elif (
                    self.printlocation.plant.name in ("Raleigh")
                    and self.printlocation.press.name == "BHS"
                ):
                    # Use bev_alt_code as the default nomenclature.
                    try:
                        item_code = self.bev_alt_code
                    except Exception:
                        item_code = "HE Carton"
                    nomenclature = item_code
                    # Disabling the supplier code per Kimble Weeks' request
                    # 9-23-2010.
                    # Append suffix depending on plate supplier.
                    # Raleigh BHS, handled by Optihue.
                    """
                    if self.job.prepress_supplier in ('Optihue', '', None,
                                                      'OPT'):
                        nomenclature = item_code + "CGH"
                    # Raleigh BHS, handled by Phototype
                    elif self.job.prepress_supplier in ('Phototype',
                                                        'PHT'):
                        nomenclature = item_code + "PT"
                    # Raleigh BHS, handled by Southern Graphics.
                    elif self.job.prepress_supplier in ('Southern Graphics',
                                                        'SGS',):
                        nomenclature = item_code + "SG"
                    # Raleigh BHS, handled by Schawk.
                    elif self.job.prepress_supplier in ('Schawk',
                                                        'SHK',):
                        nomenclature = item_code + "ST"
                    """
                # This will be the majority of items -- Flexo cartons.
                else:
                    try:
                        item_code = self.size.bev_size_code
                    except ItemCatalog.DoesNotExist:
                        item_code = "Carton"
                    nomenclature = "%s%d" % (item_code, num_colors)
                    # Add modifier to the end of the first bit of nomen.
                    # if the item is a straw or fitment item.
                    if "fitment" in self.size.size.lower():
                        nomenclature += "F"
                    if "straw" and "gable2" in self.size.size.lower():
                        nomenclature += "K"
                    elif "straw" and "gable4" in self.size.size.lower():
                        nomenclature += "R"
                    elif "straw" in self.size.size.lower():
                        nomenclature += "K"
                    # Second portion of nomenclature.
                    if self.bev_brand_code:
                        nomenclature = "%s-%s" % (
                            nomenclature,
                            self.bev_brand_code.code,
                        )
                    # Third portion of nomenclature.
                    if self.bev_end_code:
                        nomenclature = "%s-%s" % (nomenclature, self.bev_end_code)
        # End if printlocation
        else:
            # Set default nomenclature error.
            nomenclature = "No Printlocation!"
        return nomenclature.replace(" ", "")

    def update_item_status(self):
        """Update the status of an item. (item_status)"""
        # If it's been filed out, mark it complete
        if self.final_file_date():
            self.item_status = "Complete"
        # If the item is approved and has a 9 digit, it needs to be filed out.
        elif (
            self.job.workflow.name == "Foodservice"
            and self.approval_date()
            and self.fsb_nine_digit
        ):
            self.item_status = "File Out"
        elif self.job.workflow.name == "Container" and self.approval_date():
            self.item_status = "File Out"
        elif self.job.workflow.name == "Carton" and self.approval_date():
            self.item_status = "File Out"
        else:
            self.item_status = "Pending"

        self.save()

    def get_proof_joblogs(self):
        """Returns a queryset of proof out joblog entries."""
        return JobLog.objects.filter(
            item=self, type=JOBLOG_TYPE_ITEM_PROOFED_OUT
        ).order_by("event_time")

    def first_proof_date(self):
        """Returns date of last final file out job log entry for item"""
        try:
            getlog = self.get_proof_joblogs()[0]
            return getlog.event_time
        except IndexError:
            return None

    def current_proof_date(self):
        """Returns date of last final file out job log entry for item"""
        try:
            getlog = JobLog.objects.filter(
                item=self, type=JOBLOG_TYPE_ITEM_PROOFED_OUT
            ).order_by("-event_time")[0]
            return getlog.event_time
        except IndexError:
            return None

    def is_overdue(self):
        """Return True if the item is overdue."""
        # Catch for lack of due date.
        if self.job.due_date is None:
            return False

        # Catch early if it's marked as exempt.
        if self.overdue_exempt:
            return False

        today = date.today()
        # Set proof date so it's not called multiple times.
        item_proof_date = self.first_proof_date()

        if self.job.real_due_date < today:
            if item_proof_date:
                # If the proof date happened after the real due date, it's overdue.
                if item_proof_date.date() > self.job.real_due_date:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def current_revision(self):
        """Lookup information about the most current incomplete revision.
        This is mostly useful for displaying the due date of the revision in
        the item timeline summary.
        """
        try:
            cur_rev = Revision.objects.filter(
                item=self.id, complete_date__isnull=True
            ).latest()
            return cur_rev
        except Exception:
            return None

    def approval_date(self):
        """Returns date of last final file out job log entry for item.
        Critical for the interface to display if the item has been approved.
        """
        try:
            getlog = JobLog.objects.filter(
                item=self, type=JOBLOG_TYPE_ITEM_APPROVED
            ).order_by("-event_time")[0]
            return getlog.event_time
        except IndexError:
            return None

    def is_approved(self):
        """Returns True if the item is approved, False otherwise."""
        if self.approval_date():
            return True
        else:
            return False

    def final_file_date(self):
        """Returns date of last final file out job log entry for item
        Critical for the interface to display if the item has been filed out.
        """
        try:
            getlog = JobLog.objects.filter(
                item=self, type=JOBLOG_TYPE_ITEM_FILED_OUT
            ).order_by("-event_time")[0]
            return getlog.event_time
        except IndexError:
            return None

    def is_filed_out(self):
        """Returns True if the item has been filed out, False otherwise."""
        if self.final_file_date():
            return True
        else:
            return False

    def is_master_stepped_item(self):
        """Return True if other items refer to self as 'steps_with'"""
        if self.steps_with_item.all():
            return True
        else:
            return False

    def final_file_due_date(self):
        """Foodservice and Carton only. Calculate due date of the final file based
        on when the approval and item number were added. +3 days.
        """
        try:
            approval_date = JobLog.objects.filter(
                item=self, type=JOBLOG_TYPE_ITEM_APPROVED
            ).order_by("-event_time")[0]
            # Foodservice logic
            if self.job.workflow.name == "Foodservice":
                if (
                    self.fsb_nine_digit_date
                    and approval_date
                    and not self.is_filed_out()
                ):
                    if self.fsb_nine_digit_date > approval_date.event_time.date():
                        latest_day = self.fsb_nine_digit_date
                    else:
                        latest_day = approval_date.event_time.date()
                    # If Thursday or Friday, adjust for weekend.
                    if latest_day.isoweekday() == 4 or latest_day.isoweekday() == 5:
                        days_til_due = 5
                    else:
                        days_til_due = 3

                    # Make sure we don't land on a weekend
                    due_date = latest_day + timedelta(days=days_til_due)
                    if due_date.isoweekday() == 6:
                        days_til_due += 2
                    elif due_date.isoweekday() == 7:
                        days_til_due += 1

                    return latest_day + timedelta(days=days_til_due)

                else:
                    # Job has no Nine Digit, nothing due.
                    return None
            # Carton logic. No fsb nine digit date.
            elif self.job.workflow.name == "Carton":
                if approval_date and not self.is_filed_out():
                    latest_day = approval_date.event_time.date()
                    # If Thursday or Friday, adjust for weekend.
                    if latest_day.isoweekday() == 4 or latest_day.isoweekday() == 5:
                        days_til_due = 5
                    else:
                        days_til_due = 3

                    # Make sure we don't land on a weekend
                    due_date = latest_day + timedelta(days=days_til_due)
                    if due_date.isoweekday() == 6:
                        days_til_due += 2
                    elif due_date.isoweekday() == 7:
                        days_til_due += 1

                    return latest_day + timedelta(days=days_til_due)

                else:
                    # Nothing due.
                    return None
        except IndexError:
            # Job is not approved, nothing due.
            return None

    def do_bev_make_die(self):
        """Creates a PDF with the appropriate die lines for beverage items."""
        # Get the path to the master template pdf.
        template_dir = os.path.join(
            settings.ITEM_TEMPLATE_DIR, "beverage/AutomationEngineTemplates/"
        )
        # Yank spaces, convert to lower case. Keeps things consistent.
        template_name = self.size.size.replace(" ", "").lower() + ".pdf"
        source_path = os.path.join(template_dir, template_name)

        # Set the path to the item's final file folder.
        destination_file = "%s-%s %s" % (
            self.job.id,
            self.num_in_job,
            self.bev_nomenclature(),
        )
        destination_path = os.path.join(self.get_folder(), destination_file)
        # If the file already exists, don't overwrite it. Stick a suffix
        # on the end of the new file and preserve the original.
        if os.path.exists(destination_path + ".pdf"):
            # Add a date/timestamp suffix.
            suffix = timezone.now().strftime("%m_%d_%y-%H_%M")
            destination_file += "_%s.pdf" % suffix
        else:
            # No duplicate, proceed as normal.
            destination_file += ".pdf"
        # Final determination of destination path with suffix/extension.
        destination_path = os.path.join(self.get_folder(), destination_file)
        # Check source and destination.
        print(("Source: %s" % (source_path)))
        print(("Target: %s" % (destination_path)))
        # Attempt to copy template to item folder.
        try:
            print("Copying...")
            shutil.copy2(source_path, destination_path)
            print("...copy complete. Starting Automation Engine workflow...")
            # Format the path such that Automation Engine can get to the file.
            path = destination_path.replace(
                settings.WORKFLOW_ROOT_DIR, "file://" + settings.FS_SERVER_HOST
            )
            self.do_jdf_bev_die(path)
            print("...Automation Engine workflow started.")
        except Exception:
            print("Beverage template copy failed.")

    def do_fsb_make_rectangle(self):
        """Save a PDF into the item folder that is a rectangle of the appropriate
        dimensions for creating artwork on prior to warping to die.
        """
        folder = fs_api.find_item_folder(self.job.id, self.num_in_job)
        press_shortname = self.printlocation.press.short_name
        if self.printlocation.press.name == "Kidder":
            if self.special_mfg:
                if self.special_mfg.name == "Blank-Fed":
                    press_shortname = "KBF"
        elif self.printlocation.press.name == "Comco":
            if self.special_mfg:
                if self.special_mfg.name == "Blank-Fed":
                    press_shortname = "CBF"
        elif self.printlocation.press.name == "FK":
            if self.special_mfg:
                if self.special_mfg.name == "Roll-Fed":
                    press_shortname = "FKR"
                elif self.special_mfg.name == "Zerand":
                    press_shortname = "FKZerand"
        elif self.printlocation.press.name == "Uteco":
            if self.special_mfg:
                if self.special_mfg.name == "Zerand":
                    press_shortname = "UTZerand"

        # If the size ends in C or CB remove it.
        working_size = self.size.size.split("-")
        if ("C" in working_size[0]) or ("CB" in working_size[0]):
            print(("Looking up size exception for: %s" % self.size.size))
            if working_size[0].endswith("C"):
                size = working_size[0][:-1] + "-" + working_size[1]
            elif working_size[0].endswith("CB"):
                size = working_size[0][:-2] + "-" + working_size[1]
            else:
                size = str(self.size.size)
            print(("New size: %s" % size))
        else:
            print("No size exceptions found.")
            size = str(self.size.size)

        # eg: 59300-2 DMR-22-45FKs.pdf"
        pdf_name = "%s-%s %s-%s%ss" % (
            str(self.job.id),
            str(self.num_in_job),
            size,
            str(self.printlocation.plant.code),
            press_shortname,
        )
        cleaned_filename = fs_api.escape_string_for_regexp("%s%s" % (pdf_name, ".pdf"))
        pattern = re.compile(r"(?i)%s$" % cleaned_filename)

        # Append the timestamp if a file already exists with that name.
        try:
            fs_api._generic_item_file_search(folder, pattern)
            pdf_name += "%s%s" % (timezone.now().strftime("%m_%d_%y-%H_%M"), ".pdf")
        except fs_api.NoResultsFound:
            pdf_name += ".pdf"

        pdf_path = os.path.join(folder, pdf_name)
        fsb_template_maker.generate_fsb_rectangle(
            self.get_item_spec().horizontal, self.get_item_spec().vertical, pdf_path
        )

    def do_fsb_copy_die(self):
        """Copy the proper FSB die into the item subfolder."""
        # Note: product subcategory is a ManytoMany, just use the first one.
        # It's rate that an ItemCatalog is under 2 categories anyway.
        press_shortname = self.printlocation.press.short_name
        # Compensate for some weirdness in template differences between
        # Roll-fed and blank-fed.
        # TODO: Clean this crap up. Exceptions are the worst.
        if self.printlocation.press.name == "Kidder":
            if self.special_mfg:
                if self.special_mfg.name == "Blank-Fed":
                    press_shortname = "KBF"
        elif self.printlocation.press.name == "Comco":
            if self.special_mfg:
                if self.special_mfg.name == "Blank-Fed":
                    press_shortname = "CBF"
        elif self.printlocation.press.name == "FK":
            if self.special_mfg:
                if self.special_mfg.name == "Roll-Fed":
                    press_shortname = "FKR"
                elif self.special_mfg.name == "Zerand":
                    press_shortname = "FKZerand"
        elif self.printlocation.press.name == "Uteco":
            if self.special_mfg:
                if self.special_mfg.name == "Zerand":
                    press_shortname = "UTZerand"

        # If the size ends in C, CB, or CP remove it.
        working_size = self.size.size.split("-")
        if ("C" in working_size[0]) or ("CB" in working_size[0]):
            print(("Looking up size exception for: %s" % self.size.size))
            # Don't chop the C off PTRPC.
            if working_size[0].endswith("C") and "PTRPC" not in working_size[0]:
                size = working_size[0][:-1] + "-" + working_size[1]
            elif working_size[0].endswith("CB"):
                size = working_size[0][:-2] + "-" + working_size[1]
            elif working_size[0].endswith("CP"):
                size = working_size[0][:-2] + "-" + working_size[1]
            else:
                size = str(self.size.size)
            print(("New size: %s" % size))
        else:
            print("No size exceptions found.")
            size = str(self.size.size)

        fs_api.copy_fsb_production_template(
            size,
            self.size.productsubcategory.all()[0].get_main_category_display(),
            self.printlocation.plant.code,
            press_shortname,
            self.job.id,
            self.num_in_job,
        )

    def can_preflight(self):
        """Return True if item can be preflighted"""
        #        if self.job.workflow.name == "Beverage":
        #            if self.preflight_date:
        #                return False
        #            else:
        #                return True
        #        else:
        #            return False

        if self.job.workflow.name == "Beverage":
            if self.preflight_date:
                return False
            else:
                return True
        else:
            if self.preflight_date:
                return False
            else:  # Because we are adding preflight to all jobs, we have to consider old Foodservice jobs that didn't have this option
                if self.can_proof():
                    return True
                else:
                    return False

    def do_preflight(self, exception=""):
        """Method for preflighting an item & trigger associated events.
        Beverage specific method.
        """
        # Item is being proofed, so set the date. If this is the
        # first proof, set that, too.
        self.preflight_date = date.today()
        self.preflight_ok = 1
        # Log this event, along with the warnings and comments.
        log_text = "Item %s has been preflighted." % (self.num_in_job)
        log_text = log_text + " " + exception
        if self.job.workflow.name == "Beverage":
            self.do_create_joblog_entry(JOBLOG_TYPE_ITEM_SAVED, log_text)
        else:
            # Log this event as a Preflight so that it shows up in the Timeline Job Log.
            self.do_create_joblog_entry(JOBLOG_TYPE_ITEM_PREFLIGHT, log_text)

        # Save, so at least the preflight stuff gets taken care of.
        self.save()

        if self.job.workflow.name == "Beverage":
            if self.job.status == "Pending":
                self.job.status = "Active"
                self.job.save()
            # Create the folder, just in case it hasn't already been created.
            self.create_folder()
            self.do_bev_make_die()

        return self.save()

    def can_marketing_review(self):
        """Return True if item can be submitted for review to Marketing. This
        is a pre-proof step for Marketing approval of brand-specific logos such
        as Ecotainer, SFI, etc...
        """
        if self.job.workflow.name == "Foodservice":
            if self.is_approved() or self.is_filed_out():
                return False
            else:
                return True
        else:
            return False

    def create_marketing_review(self, logthis):
        """Creates a new item review object."""
        self.itemreview_set.create(review_catagory="market", entry_comments=logthis)
        log_text = "Item %s has been submitted to Marketing for review: %s" % (
            self.num_in_job,
            logthis,
        )
        self.do_create_joblog_entry(JOBLOG_TYPE_ITEM_SAVED, log_text)

    def review_status_mkt(self):
        """Return status of marketing review, along with display information for template."""
        status = {}
        # Set default status and icon.
        status["status"] = "Waiting"
        status["icon"] = "control_pause"

        try:
            mkt_review = self.itemreview_set.filter(review_catagory="market").order_by(
                "-id"
            )
            mkt_review = mkt_review[0]
        except Exception:
            pass

        if mkt_review:
            # Default if waiting on approval.
            if not mkt_review.review_ok and not mkt_review.review_date:
                status["status"] = "Pending"
                status["icon"] = "hourglass"
            # If it was Rejected...
            elif (
                not mkt_review.review_ok
                and mkt_review.review_date
                and mkt_review.comments != "Resubmitted"
            ):
                status["status"] = "Rejected"
                status["icon"] = "exclamation"
            # If it was resubmitted...
            elif (
                not mkt_review.review_ok
                and mkt_review.review_date
                and mkt_review.comments == "Resubmitted"
            ):
                status["status"] = "Pending"
                status["icon"] = "hourglass"
            # If item has been accepted...
            elif mkt_review.review_ok:
                status["status"] = "OK"
                status["icon"] = "accept"

        return status

    def mkt_review_check(self):
        """Checks to see if the item has any market review objects or not. Used to
        determine if a given item needs a market review.
        """
        reviews = self.itemreview_set.filter(review_catagory="market")

        if reviews:
            return True
        else:
            return False

    def plant_check_expired(self):
        """Check to see if the allotted time for the plant to check the job
        has expired. This is really for display purposes only in the Item
        Summary Timeline.
        """
        today = date.today()
        check_period = self.creation_date.date() + timedelta(days=2)
        if check_period < today:
            return True
        else:
            return False

    def review_check_expired(self):
        """Check to see if the allotted time for the plant to check the job
        has expired. This is really for display purposes only in the Item
        Summary Timeline.
        """
        start_date = general_funcs._utcnow_naive()

        # Grab the latest reviews if they exist.
        try:
            plant_review = self.itemreview_set.filter(review_catagory="plant").latest(
                "review_initiated_date"
            )
        except Exception:
            plant_review = False

        try:
            demand_review = self.itemreview_set.filter(review_catagory="demand").latest(
                "review_initiated_date"
            )
        except Exception:
            demand_review = False

        # If there are both use the oldest one.
        if plant_review and demand_review:
            if (
                plant_review.review_initiated_date
                <= demand_review.review_initiated_date
            ):
                start_date = plant_review.review_initiated_date
            else:
                start_date = demand_review.review_initiated_date
        elif plant_review:
            start_date = plant_review.review_initiated_date
        elif demand_review:
            start_date = demand_review.review_initiated_date

        # Convert start_date to naive if it's timezone-aware for comparison
        if timezone.is_aware(start_date):
            start_date = timezone.make_naive(start_date)

        # Calculate the date for three business days ago (UTC-naive now)
        now_dt = general_funcs._utcnow_naive()
        if now_dt.isoweekday() == 7:
            three_days_ago = now_dt - timedelta(4)
        elif 1 <= now_dt.isoweekday() <= 3:
            three_days_ago = now_dt - timedelta(5)
        else:
            three_days_ago = now_dt - timedelta(3)

        return start_date < three_days_ago

    def review_status(self):
        """Checks an items plant and demand plan reviews and returns the
        appropriate status.
        """
        # Set default status and icon.
        status = {}
        status["status"] = "Waiting"
        status["icon"] = "control_pause"

        # Grab the latest reviews if they exist. It would be unusual to have a
        # plant review without a demand review or vice-versa. We should still
        # account for that situation though.
        try:
            plant_review = self.itemreview_set.filter(review_catagory="plant").latest(
                "review_initiated_date"
            )
        except Exception:
            plant_review = False
        try:
            demand_review = self.itemreview_set.filter(review_catagory="demand").latest(
                "review_initiated_date"
            )
        except Exception:
            demand_review = False

        if self.job.workflow.name == "Foodservice":
            # If we have both a plant and demand review.
            if plant_review and demand_review:
                # If they're both approved then naturally the status is approved.
                if plant_review.review_ok and demand_review.review_ok:
                    status["status"] = "OK"
                    status["icon"] = "accept"
                # If either of them are rejected then the status is rejected.
                elif (not plant_review.review_ok and plant_review.review_date) or (
                    not demand_review.review_ok and demand_review.review_date
                ):
                    status["status"] = "Rejected"
                    status["icon"] = "exclamation"
                # If they haven't been OK'd or rejected then check to see
                # if time has expired.
                elif self.review_check_expired():
                    status["status"] = "Time Expired"
                    status["icon"] = "hourglass"

            # If we have just a plant review. Kind of unusual.
            elif plant_review:
                if plant_review.review_ok:
                    status["status"] = "OK"
                    status["icon"] = "accept"
                # If it was reviewed but not OK'd then it's rejected.
                elif plant_review.review_date:
                    status["status"] = "Rejected"
                    status["icon"] = "exclamation"
                # If none of the above are true and we're still waiting on reviews
                # to be completed then check to see if time has expired.
                elif self.review_check_expired():
                    status["status"] = "Time Expired"
                    status["icon"] = "hourglass"
            # If we have just a demand review. Kind of unusual.
            elif demand_review:
                if demand_review.review_ok:
                    status["status"] = "OK"
                    status["icon"] = "accept"
                # If it was reviewed but not OK'd then it's rejected.
                elif demand_review.review_date:
                    status["status"] = "Rejected"
                    status["icon"] = "exclamation"
                # If none of the above are true and we're still waiting on reviews
                # to be completed then check to see if time has expired.
                elif self.review_check_expired():
                    status["status"] = "Time Expired"
                    status["icon"] = "hourglass"

        else:
            # Handle Beverage - simple yes or no.
            if self.preflight_ok:
                status["status"] = "OK"
                status["icon"] = "accept"

        return status

    def needs_proof_reminder(self):
        """Method to return True/False based on if the item needs a proof
        reminder sent to the salesperson (email sent 15 days after first proof
        if no action has occurred since.) Reminder should only go out once, so
        don't send if proof_reminder_email_sent boolean is set to True already.
        """
        return False

    def is_proof_inactive(self):
        """Return True if the conditions have not been met that show further
        action after the proof reminder email has been sent.
        Active (True) would inidicate that nothing has happened recently.
        """
        # Return false if no reminder sent yet, this means first proof was out
        # in the last 15 days.
        if not self.proof_reminder_email_sent:
            return False
        else:
            # Reminder has gone out... calculate when it went out, and see if anything
            # has happened since.
            initial_proof = self.first_proof_date()
            reminder_date = initial_proof + timedelta(days=15)
            # If item has been approved, filed out or deleted, it is active.
            if JobLog.objects.filter(
                item=self,
                type__in=(
                    JOBLOG_TYPE_ITEM_APPROVED,
                    JOBLOG_TYPE_ITEM_FILED_OUT,
                    JOBLOG_TYPE_JOBLOG_DELETED,
                ),
            ):
                return False
            # Current proof went out after proof reminder.
            if self.current_proof_date() >= reminder_date:
                return False
            # Revision is pending.
            if self.current_revision():
                return False
            # Not approved, file out or deleted, no proofs since reminder, no pending
            # revisions. This is inactive, report back!
            return True

    def item_situation_status(self):
        """Overrides item_situation if activity has taken place since."""
        if self.item_situation:
            # Nothing has happened, return item_situation
            if self.is_proof_inactive():
                return self.item_situation
            else:
                # This means that something of interest has happened to the item.
                # Override the item_situation in this case.
                return None
        else:
            return None

    def overdue_status(self):
        """Return Overdue state and display info. to the template"""
        status = {}
        if self.overdue_exempt:
            status["status"] = "Exempted"
            status["icon"] = "flag_orange"
        else:
            if self.job.overdue():
                status["status"] = "Overdue"
                status["icon"] = "exclamation"
            else:
                status["status"] = ""
                status["icon"] = "control_pause"

        return status

    def do_production_edit(self, logchanges):
        """Marking an item as having it's production data changed."""
        log_text = "The following production data for item %s has been changed: " % (
            self.num_in_job
        )
        log_text = log_text + " " + logchanges
        self.do_create_joblog_entry(JOBLOG_TYPE_PRODUCTION_EDITED, log_text)

        self.is_queued_for_thumbnailing = True

        return self.save()

    def set_assignement_date(self):
        """Set the assignment date for an item.
        This field will control display on the plant & demand planning review.
        """
        self.assignment_date = date.today()
        return self.save()

    def can_proof(self):
        """Determines if the item can be proofed.
        No filed out, No approved.
        """
        if self.final_file_date():
            return False
        else:
            if self.approval_date():
                return False
            else:
                return True

    def do_proof(self, exception="", date_override=None):
        """Method for proofing an item & trigger associated events.
        Most critical is creating the JobLog entry, which is essential for
        tracking when the proof went out.
        """
        # Log this event, along with the warnings and comments.
        log_text = "Item %s has been proofed." % (self.num_in_job)
        log_text = log_text + " " + exception
        joblog = self.do_create_joblog_entry(
            JOBLOG_TYPE_ITEM_PROOFED_OUT, log_text, date_override=date_override
        )
        # Resolve any incomplete revisions.
        pending_revisions = Revision.objects.filter(
            item=self.id, complete_date__isnull=True
        )
        number_of_revisions = pending_revisions.count()
        if number_of_revisions > 0:
            for revision in pending_revisions:
                revision.complete_revision()
        try:
            # Send out Emails.
            if (
                not self.job.carton_type == "Imposition"
            ):  # but not for carton imposion jobs
                mail_subject = "GOLD Proof Notice: %s" % self.job
                mail_send_to = []
                if self.job.salesperson:
                    mail_send_to.append(self.job.salesperson.email)
                if mail_send_to:
                    internal_recipients = []
                    external_recipients = []

                    # Sort addresses based on internal vs. external (everpack).
                    for address in mail_send_to:
                        if address.lower().endswith("everpack.com"):
                            external_recipients.append(address)
                        else:
                            internal_recipients.append(address)

                    internal_url = "gchub.graphicpkg.com"
                    external_url = "gchub"

                    # Render the body text differently for everpack.com emails,
                    # as they are coming through the VPN at a different address.
                    if internal_recipients:
                        mail_body = loader.get_template("emails/on_do_proof.txt")
                        mail_context = {"item": self, "url": internal_url}
                        general_funcs.send_info_mail(
                            mail_subject, mail_body.render(mail_context), mail_send_to
                        )
                    if external_recipients:
                        mail_body = loader.get_template("emails/on_do_proof.txt")
                        mail_context = {"item": self, "url": external_url}
                        general_funcs.send_info_mail(
                            mail_subject, mail_body.render(mail_context), mail_send_to
                        )
        except Exception:
            # Email failed, sad. Probably a bad or nonexistent address.
            pass

        self.is_queued_for_thumbnailing = True
        self.save()

        # Run status updates, etools push, etc...
        self.job.do_status_update()

        # Attempt to move around the proof files so that a revision history
        # is maintained.
        try:
            fs_api.copy_item_proof_folder(self.job.id, self.num_in_job, joblog.id)
        except Exception:
            pass

        return self

    def is_linked_proof(self):
        """Return True if there is a proof to link to."""
        try:
            fs_api.get_item_proof(self.job.id, self.num_in_job)
            return True
        except Exception:
            return False

    def do_tiff_to_pdf(self):
        """Starts tiff-PDF generation."""
        self.copy_new_die_tiff()
        self.do_jdf_tiff_to_pdf()

    def can_approve(self):
        """Determines if the item can be approved. Proofed, no revisions.
        Yes proofed, No revisions, No already approved.
        """
        if self.first_proof_date():
            if self.current_revision():
                return False
            else:
                if self.approval_date():
                    return False
                else:
                    return True
        else:
            return False

    def do_approve(self, exception="", date_override=None, scripted_user=None):
        """Method to approve an item & trigger associated events.
        Most critical is creating the JobLog entry, which is essential for
        tracking when the approval occured.
        """
        # Log this event, along with the warnings and comments.
        log_text = "Item %s has been approved." % (self.num_in_job)
        log_text = log_text + " " + exception
        self.do_create_joblog_entry(
            JOBLOG_TYPE_ITEM_APPROVED,
            log_text,
            user_override=scripted_user,
            date_override=date_override,
        )

        # Send a growl notification to the artist.
        self.job.growl_at_artist(
            "Approval Notice",
            "The customer has approved %s, %s-%s %s."
            % (self.job.name, str(self.job.id), str(self.num_in_job), str(self)),
            pref_field="growl_hear_approvals",
        )

        # Email notifcations
        mail_subject = "GOLD Approval Notice: %s" % self.job
        mail_send_to = []
        if self.job.salesperson:
            mail_send_to.append(self.job.salesperson.email)

        # If an item is being approved, and there is already a nine digit number,
        # the demand planning folks need to hear about it.
        # Don't send if it's a press change.
        if self.fsb_nine_digit and not self.job.duplicated_from:
            group = Group.objects.get(name="FSB Demand Planning")
            for user in group.user_set.all():
                mail_send_to.append(user.email)

        if self.printlocation:
            if (
                self.printlocation.plant.name == "Plant City"
                or self.printlocation.press.name == "BHS"
            ):
                if self.job.artist:
                    mail_send_to.append(self.job.artist.email)

        # Don't send if nobody to send to.
        if mail_send_to:
            mail_body = loader.get_template("emails/on_do_approve.txt")
            mail_context = {"item": self}
            general_funcs.send_info_mail(
                mail_subject, mail_body.render(mail_context), mail_send_to
            )

        # Run status updates, etools push, etc...
        self.job.do_status_update()
        self.update_item_status()
        # Create a carton SAP entry if needed.
        if self.job.check_sap_carton():
            self.job.do_sap_notification()

        return self.save()

    def can_forecast(self):
        """Determines if the item can be forecasted.
        Yes, Nine Digit Number. No, if Forecast exists in JobLog.
        """
        forecast_exists = JobLog.objects.filter(job=self.job, item=self.id, type=25)
        if self.fsb_nine_digit:
            if forecast_exists:
                return False
            else:
                return True
        else:
            return False

    def do_forecast(self, text=""):
        """Method to mark item as forecasted.
        Most critical is creating the JobLog entry, which is essential for tracking
        when the forecast occured.
        """
        # Log this event, along with the warnings and comments.
        # Logging the event in JobLog is what actually makes the event occur.
        log_text = "Item %s has been forecasted." % (self.num_in_job)
        self.do_create_joblog_entry(JOBLOG_TYPE_ITEM_FORECAST, log_text)
        if text:
            forecast_text = "Item %s forecast set as " % (self.num_in_job)
            forecast_text = forecast_text + text
            self.do_create_joblog_entry(JOBLOG_TYPE_NOTE, forecast_text)

    def can_file_out(self):
        """Determines if the item can be filed out.
        Yes Proofed, Yes Approved, No Already File Out.
        """
        if self.first_proof_date():
            if self.approval_date():
                if self.final_file_date():
                    return False
                else:
                    if self.job.workflow.name == "Beverage":
                        # Lock Beverage from filing out if all charges
                        # have already been invoiced, if there even were charges.
                        # Lock file out if the platemaker is Shelbyville.
                        if (
                            self.bev_item_lock()
                            and self.job.temp_platepackage.platemaker.name
                            == "Shelbyville"
                        ):
                            return False
                        else:
                            return True
                    else:
                        return True
            else:
                return False
        else:
            return False

    def transfer_files_to_concord(self):
        """Triggers the "Transfer Files to Concord" Automation Engine workflow."""
        extra_vars = {
            "PreppedFileList": {"Status": "Unavailable"},
            "PLAFileList": {"Status": "Unavailable"},
            "TIFFList": {"Status": "Unavailable"},
        }

        head, mid, tail = self.path_to_file.partition("/Final_Files")
        path_to_file = (
            "file://"
            + settings.FS_SERVER_HOST
            + "/JobStorage/"
            + str(self.job.id)
            + mid
            + tail
        )

        file_set = []
        file_set.append(path_to_file)

        # Create ItemJDF object with input file list.
        sr_jdf = ItemJDF(self, {"SourceFileList": file_set}, extra_vars=extra_vars)

        # Use the Prepare Station task to resave the PDF prior to processing.
        # This will retrigger and update the SmartMarks used to populate plate codes.
        smartStepRIP_ticket = "/swft/Transfer Files to Concord"
        sr_jdf.add_task_node(
            "Workflow",
            node_id="n0001",
            task_id="ConcordTransfer",
            ticket_name=smartStepRIP_ticket,
            task_output_id="FSBConcordTransfer",
        )

        sr_jdf.send_jdf()

    def do_final_file(self, exception="", date_override=None):
        """Method to final file an item & trigger associated events.
        Most critical is creating the JobLog entry, which is essential for tracking
        when the file out occured.
        """
        # Log this event, along with the warnings and comments.
        # Logging the event in JobLog is what actually makes the event occur.
        log_text = "Item %s has been filed out." % (self.num_in_job)
        log_text = log_text + " " + exception
        self.do_create_joblog_entry(
            JOBLOG_TYPE_ITEM_FILED_OUT, log_text, date_override=date_override
        )

        # Sets the item status to Complete.
        self.item_status = "Complete"
        self.save()

        # Prepare an email notification.
        mail_subject = "GOLD File Out Notice: %s" % self.job

        mail_send_to = []
        if self.job.salesperson:
            mail_send_to.append(self.job.salesperson.email)

        # Some items won't have a platepackage (marketing work, etc...)
        if self.platepackage:
            for contact in self.platepackage.platemaker.contacts.all():
                mail_send_to.append(contact.email)

        # Copy users who are part of plante scheduling.
        if self.printlocation:
            if self.printlocation.plant.name == "Shelbyville":
                permission = Permission.objects.get(codename="shelbyville_scheduling")
                for user in permission.user_set.all():
                    mail_send_to.append(user.email)
            elif self.printlocation.plant.name == "Kenton":
                permission = Permission.objects.get(codename="kenton_scheduling")
                for user in permission.user_set.all():
                    mail_send_to.append(user.email)
            elif self.printlocation.plant.name == "Clarksville":
                for user in User.objects.filter(
                    groups__name="EmailClarksvilleScheduling", is_active=True
                ):
                    mail_send_to.append(user.email)
            elif self.printlocation.plant.name == "Pittston":
                for user in User.objects.filter(
                    groups__name="EmailPittstonScheduling", is_active=True
                ):
                    mail_send_to.append(user.email)
            elif self.printlocation.plant.name == "Olmsted Falls":
                permission = Permission.objects.get(
                    codename="olmsted_falls_notification"
                )
                for user in permission.user_set.all():
                    mail_send_to.append(user.email)
            elif self.printlocation.plant.name == "Marion":
                if (
                    self.job.workflow.name == "Carton"
                    and self.job.carton_type == "Imposition"
                ):
                    for user in User.objects.filter(
                        groups__name="EmailMarionScheduling", is_active=True
                    ):
                        mail_send_to.append(user.email)
            elif self.printlocation.plant.name == "Stone Mtn":
                for user in User.objects.filter(
                    groups__name="EmailStoneMtnScheduling", is_active=True
                ):
                    mail_send_to.append(user.email)
            elif self.printlocation.plant.name == "Visalia":
                for user in User.objects.filter(
                    groups__name="EmailVisaliaScheduling", is_active=True
                ):
                    mail_send_to.append(user.email)

        # Don't send if no receipients.
        if mail_send_to:
            mail_body = loader.get_template("emails/on_do_final_file.txt")
            mail_context = {"item": self}
            general_funcs.send_info_mail(
                mail_subject, mail_body.render(mail_context), mail_send_to
            )

        # Notify Donna & Madhura if item is filed out without forecast
        forecast_exists = JobLog.objects.filter(job=self.job, item=self.id, type=25)
        # Don't send notifications for sales and marketing items.
        ignore_plants = ["Sales", "Marketing"]
        # Let's check if this item has a print location and plant.
        try:
            item_plant = self.printlocation.plant.name
        except Exception:
            item_plant = "None"
        # Check if this item needs an email.
        if (
            self.workflow.name == "Foodservice"
            and not forecast_exists
            and not self.job.duplicated_from
            and item_plant not in ignore_plants
            and not str(self.size.size).endswith(" KD")
            and self.fsb_nine_digit
        ):
            # If it meets those conditions send a notification email.
            mail_send_to = []
            mail_send_to.append(settings.EMAIL_GCHUB)
            group_members = User.objects.filter(
                groups__name="EmailGCHubNewItems", is_active=True
            )
            for user in group_members:
                mail_send_to.append(user.email)
            mail_subject = "GOLD File Out: %s - No Forecast" % self.job
            mail_body = loader.get_template("emails/forecast_notice.txt")
            mail_context = {"item": self}
            general_funcs.send_info_mail(
                mail_subject, mail_body.render(mail_context), mail_send_to
            )

        # ######################################### #
        # Send email to Tracy Richmond-Harris if we are printing item.size SDR-## Base
        if ("wendy" in self.job.name.lower()) and ("sdr" in self.size.size.lower()):
            mail_send_to = []
            group_members = User.objects.filter(
                groups__name="EmailWendySDR", is_active=True
            )
            for user in group_members:
                mail_send_to.append(user.email)
            mail_subject = "GOLD File Out: %s" % self.job
            mail_body = loader.get_template("emails/wendy_sdr.txt")
            mail_context = {"item": self}
            general_funcs.send_info_mail(
                mail_subject, mail_body.render(mail_context), mail_send_to
            )

        # Automatically trigger tranfers files to concord for Carton Prepress items.
        if self.job.workflow.name == "Carton" and self.job.carton_type == "Prepress":
            self.transfer_files_to_concord()

        # Run status update on job. Will mark complete if all file out, etc...
        self.job.do_status_update()

        # This will apply to Beverage jobs only.
        # Create queue entry for the FTP to platemaking.
        if self.platepackage:
            if self.platepackage.platemaker.name.lower() == "fusion flexo":
                self.job.ftp_item_tiffs_to_platemaker(
                    [self.num_in_job], DESTINATION_FUSION_FLEXO
                )
            elif self.platepackage.platemaker.name.lower() == "cyber graphics":
                self.job.ftp_item_tiffs_to_platemaker(
                    [self.num_in_job], DESTINATION_CYBER_GRAPHICS
                )
            elif self.platepackage.platemaker.name.lower() == "southern graphic":
                self.job.ftp_item_tiffs_to_platemaker(
                    [self.num_in_job], DESTINATION_SOUTHERN_GRAPHIC
                )
            elif self.platepackage.platemaker.name.lower() == "phototype":
                self.job.ftp_item_tiffs_to_platemaker(
                    [self.num_in_job], DESTINATION_PHOTOTYPE
                )

        return self

    def do_plate_order(self, is_new_order=True):
        """Abstraction for creating plate orders for an item."""
        new_order = PlateOrder()
        # Reference to the job.
        new_order.item = self
        new_order.requested_by = threadlocals.get_current_user()
        new_order.new_order = is_new_order
        new_order.save()

        inks_for_item = ItemColor.objects.filter(item=self)
        for ink in inks_for_item:
            new_plate = PlateOrderItem()
            new_plate.order = new_order
            new_plate.color = ink
            # Beverage is the only one that will be using an the num plates field.
            if self.job.workflow.name != "Beverage":
                new_plate.quantity_needed = 1
            else:
                new_plate.quantity_needed = ink.num_plates
            new_plate.save()

        # Bill for this item, if Beverage.
        try:
            if self.job.workflow.name == "Beverage":
                self.do_bev_plate_billing()
        except Exception:
            pass

    def do_bev_plate_billing(self):
        """Add a plate billing charge to Beverage jobs. Only for Shelbyville."""
        if (
            self.job.workflow.name == "Beverage"
            and self.job.temp_platepackage.platemaker.name == "Shelbyville"
        ):
            if self.job.temp_printlocation.plant.name == "Athens":
                # When Athens is the plant we add a film charge.
                charge_type = ChargeType.objects.get(type="Films")
            else:
                # Add a plate charge in all other cases.
                charge_type = ChargeType.objects.get(type="Plates")
            if Charge.objects.filter(item=self, description=charge_type):
                # Charge is already in place, do nothing.
                pass
            else:
                try:
                    charge = Charge()
                    charge.item = self
                    charge.description = charge_type
                    # This will take into account colors and size.
                    charge.amount = charge_type.actual_charge(item=self)
                    charge.save()
                except Exception:
                    pass

    def do_item_color(self, color):
        """Add a color to a job."""
        new_color = ItemColor()
        new_color.item = self
        new_color.color = color
        new_color.save()

    def do_revision(self, note):
        """Method to log revision for an item into the job log."""
        # Log this event, along with the warnings and comments.
        log_text = "Revision entered for item %s:" % (self.num_in_job)
        log_text = log_text + " " + note
        self.do_create_joblog_entry(JOBLOG_TYPE_ITEM_REVISION, log_text)

        # Send a growl notification to the artist.
        self.job.growl_at_artist(
            "Revision Notice",
            "A revision has just been entered for %s, %s-%s %s."
            % (self.job.name, str(self.job.id), str(self.num_in_job), str(self)),
            pref_field="growl_hear_revisions",
        )

        # Send an email to the artist.
        mail_subject = "GOLD Revision Notice: %s" % self.job
        mail_send_to = []
        try:
            mail_send_to.append(self.job.artist.email)
            mail_body = loader.get_template("emails/on_do_revision.txt")
            mail_context = {"item": self, "note": note}
            general_funcs.send_info_mail(
                mail_subject, mail_body.render(mail_context), mail_send_to
            )
        except Exception:
            # Fail if no email reciepients.
            pass

    def can_enter_revision(self):
        """Return true if item can have a revision entered."""
        # If there is a current revision, it must be completed before another is made
        if self.current_revision():
            return False
        # A revision can be made as long as something has not been approved
        if self.approval_date():
            return False

        if self.job.workflow.name == "Beverage":
            if self.bev_item_lock():
                return False
            else:
                return True
        else:
            # Foodservice job.
            if self.is_filed_out():
                return False
            else:
                return True

    def do_fsb_nine_digit(self, date_override=None):
        """If the item number is new or changed, adjusted the date input."""
        # Set the date that the nine digit was entered.
        if date_override is None:
            self.fsb_nine_digit_date = date.today()
        else:
            self.fsb_nine_digit_date = date_override
        self.save()

        # Create a Job Log event that this happened. (Joblog not used to track)
        log_text = "Item %s - Item number has been added/updated. %s" % (
            self.num_in_job,
            self.fsb_nine_digit,
        )
        self.do_create_joblog_entry(
            JOBLOG_TYPE_ITEM_9DIGIT, log_text, date_override=date_override
        )

        # No plate codes for carton items
        if not self.workflow.name == "Carton":
            # Set the plate number of all itemcolors to be the nine digit number.
            # User will be able to override this later.
            for color in self.itemcolor_set.all():
                color.calculate_plate_code()

        # Run status updates, etools push, etc...
        self.job.do_status_update()
        self.update_item_status()

    def do_nine_digit_email(self):
        """Send out an email notification to sales and csr about the nine-digit
        number and SCC numbers being ready.
        """
        if self.printlocation:
            plant = self.printlocation.plant.name
            press = self.printlocation.press.name
        else:
            plant = "N/A"
            press = "N/A"

        """
        Sales has requested that we pull some additional info for them and
        include it in this email. We won't be storing this data, just passing
        it along from QAD.
        """
        # Get additional data from QAD tables.
        data = qad.get_email_data(self.fsb_nine_digit)
        casepack = data[0]
        sleevecount = data[1]
        weight = data[2]
        tihi = data[3]
        cube = data[4]
        length = data[5]
        width = data[6]
        height = data[7]

        # Prepare the email
        mail_subject = "GOLD Item Number Notice: %s" % self.job
        mail_send_to = []
        if self.job.salesperson:
            mail_send_to.append(self.job.salesperson.email)

        if self.job.csr:
            mail_send_to.append(self.job.csr.email)

        if mail_send_to:
            mail_body = loader.get_template("emails/on_do_fsb_nine_digit.txt")
            mail_context = {
                "item": self,
                "plant": plant,
                "press": press,
                "casepack": casepack,
                "sleevecount": sleevecount,
                "weight": weight,
                "tihi": tihi,
                "cube": cube,
                "length": length,
                "width": width,
                "height": height,
            }
            general_funcs.send_info_mail(
                mail_subject, mail_body.render(mail_context), mail_send_to
            )

    def import_qad_data(self):
        """Import QAD data into item record based on nine-digit."""
        try:
            # Get data from QAD tables.
            data = qad.get_nine_digit_data(self.fsb_nine_digit)
            # UPC number
            self.upc_number = data[0]
            # BOM/SCC number
            self.bom_number = data[1]
            self.save()
            # Email information to sales/csr.
            if self.bom_number and self.job.workflow.name == "Foodservice":
                self.do_nine_digit_email()
        except Exception:
            pass

    def do_new_item(self):
        """Log that a new item has been added to the job."""
        log_text = "Item has been added to the job."
        self.do_create_joblog_entry(JOBLOG_TYPE_ITEM_ADDED, log_text)

        # Send an email to the artist letting them know an item has been added.
        mail_subject = "GOLD Item Add Notice: %s" % self.job
        mail_send_to = [self.job.artist.email]
        for admin in settings.ADMINS:
            mail_send_to.append(admin[1])
        mail_body = loader.get_template("emails/on_do_new_item.txt")
        mail_context = {"item": self}
        general_funcs.send_info_mail(
            mail_subject, mail_body.render(mail_context), mail_send_to
        )

        return super(Item, self).save()

    def can_edit_itemcolor(self):
        """Determines if the item can have it's color edited."""
        if self.job.workflow.name != "Beverage":
            return False
        else:
            if self.job.prepress_supplier not in ("OPT", "Optihue"):
                return True
            else:
                # If the job is already completed, preflighted, or proofed.
                if (
                    self.job.status == "Complete"
                    or self.preflight_date
                    or self.first_proof_date()
                ):
                    return False
                else:
                    return True

    def can_alter_billing(self):
        """There may be some differences between how each workflow handles billing.
        Most jobs should not be able to add billing once the job is completed.
        """
        if self.job.status == "Complete":
            return False
        else:
            return True

    def get_active_plate_orders(self):
        """Return list of plate order ids not yet completed."""
        return PlateOrder.objects.filter(
            item=self, stage2_complete_date__isnull=True
        ).order_by("date_entered")

    def get_completed_plate_orders(self):
        """Return list of plate order ids not yet completed."""
        return PlateOrder.objects.filter(
            item=self, stage2_complete_date__isnull=False
        ).order_by("date_entered")

    def get_item_spec(self):
        """Lookup the information from Item Specs for item."""
        spec = ItemSpec.objects.get(
            Q(size=self.size), Q(printlocation=self.printlocation)
        )
        try:
            stepspec = StepSpec.objects.get(itemspec=spec, special_mfg=self.special_mfg)
            # The number of colors is now defined by the stepspec instead of
            # the itemspec.
            spec.num_colors_from_stepspec = stepspec.num_colors

            # The active status is now defined by the stepspec instead of the
            # itemspec.
            spec.active = stepspec.active

            # Check to make sure ink usage does not exceed specified ink limit
            spec.ink_use = ItemColor.objects.filter(item=self.id).count()
            if spec.ink_use > spec.num_colors_from_stepspec:
                spec.too_much_ink = "Yes"
        except Exception:
            pass

        if self.special_mfg:
            if self.special_mfg.name.lower() in (
                "small cylinder",
                "blank-fed_small cylinder",
            ):
                spec.num_colors_from_stepspec = 4

        return spec

    def get_master_template(self):
        """Copies the appropriate master template tiff to an item's tiff folder."""
        # Some sizes use the same master templates as other sizes. Here's a
        # dictionary of those sizes and the master templates they use.
        MASTER_TEMPLATE_SIZES = {
            "SMME": "SMM",
            "SMRE": "SMR",
            "SMRN": "SMR",
            "SMTE": "SMT",
            "SMRP": "SMR",
            "SDRA": "SDR",
            "SDRMA": "SDRM",
            "SWME": "SMM",
            "SWRE": "SMR",
            "LFRHM": "LFRH",
            "DFMCD": "DFM",
            "SWMM": "SMM",
            "DMRN": "DMR",
            "DMSN": "DMS",
            "DMSP": "DMS",
            "DFMP": "DFM",
            "DFRP": "DFR",
            "DFTP": "DFT",
            "DMRP": "DMR",
            "DMSLP": "DMSL",
            "DFRCP": "DFR",
            "DFTCP": "DFT",
            "DFMCP": "DFM",
            "DFSCP": "DFS",
            # Added this to keep from confusing with combo pack
            "PTRPC": "PTRPC",
        }

        # Confirm a size and print location.
        if self.size and self.printlocation:
            # Get the path to the item's tiff folder.
            job_folder = fs_api.get_job_folder(self.job.id)
            folder = os.path.join(job_folder, fs_api.JOBDIR["tiffs"])
            pattern = fs_api.get_jobnum_itemnum_finder_regexp(
                self.job.id, self.num_in_job
            )
            tiff_folder = fs_api._generic_item_subfolder_search(folder, pattern)
            # Get the path to the master template tiffs. McDonald's templates
            # come from a different folder so we check that first.
            if "MCD " in self.job.name:
                print("Getting McDonalds master templates.")
                master_templates = os.path.join(
                    settings.FSB_PROD_TEMPLATES, "Master Templates", "1_Bit_Tiffs_MCD"
                )
            else:
                master_templates = os.path.join(
                    settings.FSB_PROD_TEMPLATES, "Master Templates", "1_Bit_Tiffs"
                )
            # Templates are named for the press short name. We also have to
            # account for all the dumb naming differences between roll-fed and
            # blank-fed.
            press_shortname = self.printlocation.press.short_name
            if self.printlocation.press.name == "Kidder":
                if self.special_mfg:
                    if self.special_mfg.name.startswith("Blank-Fed"):
                        press_shortname = "KBF"
            elif self.printlocation.press.name == "Comco":
                if self.special_mfg:
                    if self.special_mfg.name == "Blank-Fed":
                        press_shortname = "CBF"
            elif self.printlocation.press.name == "FK":
                if self.special_mfg:
                    if self.special_mfg.name == "Roll-Fed":
                        press_shortname = "FKR"
                    elif self.special_mfg.name == "Zerand":
                        press_shortname = "FKZerand"
            elif self.printlocation.press.name == "Uteco":
                if self.special_mfg:
                    if self.special_mfg.name == "Zerand":
                        press_shortname = "UTZerand"
            # We also have some particular sizes that use identical templates
            # to other sizes. For example, smme-10 (an Ecotainer size) just
            # uses smm-10. We have to account for that kind of stuff too.

            # All of our exceptions affect the first half of the size so we
            # need to split the size at the '-' and work with the first half.
            working_size = self.size.size.split("-")
            # If the size is in our list of exceptions use the alt sizes instead.
            if working_size[0] in MASTER_TEMPLATE_SIZES:
                print(("Looking up size exception for: %s" % self.size.size))
                size = self.size.size.replace(
                    working_size[0], MASTER_TEMPLATE_SIZES[working_size[0]]
                )
                print(("New size: %s" % size))
            # If the size ends in C or CB remove it.
            elif ("C" in working_size[0]) or ("CB" in working_size[0]):
                print(("Looking up size exception for: %s" % self.size.size))
                if working_size[0].endswith("C"):
                    size = working_size[0][:-1] + "-" + working_size[1]
                elif working_size[0].endswith("CB"):
                    size = working_size[0][:-2] + "-" + working_size[1]
                else:
                    size = str(self.size.size)
                print(("New size: %s" % size))
            else:
                print("No size exceptions found.")
                size = str(self.size.size)
            # Now that we've figure out the short name let's add it to the path.
            template = (
                size
                + "-"
                + str(self.printlocation.plant.code)
                + press_shortname
                + "_DTemplate.tif"
            )
            template_dir = os.path.join(master_templates, template)
            # Copy the master template tiff to the job folder's tiff directory.
            try:
                print("Getting Master Template...")
                print(("Source: %s" % (template_dir)))
                print(("Target: %s" % (tiff_folder)))
                shutil.copy2(template_dir, tiff_folder)
                print("...done.")
            except Exception:
                print("Get Master Template: Copy failed.")
            # We also need to copy some meta data in order for the master
            # template to remain in a 'prepared for viewer' state in automation
            # engine.
            # Copy .view
            template = (
                size
                + "-"
                + str(self.printlocation.plant.code)
                + press_shortname
                + "_DTemplate.tif"
            )
            view_dir = os.path.join(master_templates, ".view")
            view_source = os.path.join(view_dir, template)
            view_dest = os.path.join(tiff_folder, ".view", template)
            try:
                print("Getting Master Template View...")
                print(("Source: %s" % (view_source)))
                print(("Target: %s" % (view_dest)))
                if os.path.exists(view_dest):
                    # If there's old view data in the destination folderremove
                    # it first.
                    print("Removing old view data first.")
                    shutil.rmtree(view_dest)
                shutil.copytree(view_source, view_dest)
                print("...done.")
            except Exception:
                print("Get Master Template View: Copy failed.")
            # Copy .meta
            meta_dir = os.path.join(master_templates, ".metadata")
            meta_name = "." + template + ".info"
            meta_source = os.path.join(meta_dir, meta_name)
            meta_dest = os.path.join(tiff_folder, ".metadata")
            try:
                print("Getting Master Template Meta...")
                print(("Source: %s" % (meta_source)))
                print(("Target: %s" % (meta_dest)))
                shutil.copy(meta_source, meta_dest)
                print("...done.")
            except Exception:
                print("Get Master Template Meta: Copy failed.")
        else:
            print("Get Master Template: Missing size or print location.")

    def bev_item_lock(self):
        """Determines if a Beverage item has been locked. Return True if locked.
        If there are charges, those charges have been invoiced, and the platemaker
        is Shelbyville. Allows changes to job otherwise.
        True = job locked, no changes can be made.
        False = job not locked, allow changes.
        """
        if self.get_uninvoiced_total() == 0 and self.get_total_charges() > 0:
            return True
        else:
            return False

    def get_specsheet_description(self):
        """Get the spec sheet description from QAD. Requires an nine digit number."""
        if self.fsb_nine_digit:
            description = qad.get_specsheet_description(self.fsb_nine_digit)
        else:
            description = None

        return description

    def get_total_charges(self):
        """Get billing summary information for item."""
        total = 0
        for single_charge in Charge.objects.filter(item=self.id):
            total = total + single_charge.amount

        return total

    def invoicing_complete(self):
        """Check to see if all charges have been invoiced."""
        if self.job.workflow.name == "Beverage":
            check_charges_uninvoiced = Charge.objects.filter(
                item=self.id, bev_invoice__isnull=True
            ).count()
        else:
            check_charges_uninvoiced = Charge.objects.filter(
                item=self.id, invoice_date=None
            ).count()
        if check_charges_uninvoiced > 0:
            complete = "Charges Uninvoiced"
        if check_charges_uninvoiced == 0:
            check_charges = Charge.objects.filter(item=self.id).count()
            if check_charges == 0:
                complete = "No Charges"
            if check_charges > 0:
                complete = "Invoicing Complete"

        return complete

    def get_uninvoiced_total(self):
        """Sum of all uninvoiced charges for an item."""
        if self.job.workflow.name == "Beverage":
            check_charges_uninvoiced = Charge.objects.filter(
                item=self.id, bev_invoice__isnull=True
            )
        else:
            check_charges_uninvoiced = Charge.objects.filter(
                item=self.id, invoice_date=None
            )
        total = 0
        for single_charge in check_charges_uninvoiced:
            total += single_charge.amount

        return total

    def check_too_few_charges(self):
        """Return the number of charges associated with this job."""
        charges = Charge.objects.filter(item=self.id)
        if charges:
            number = charges.count()
        else:
            number = 0
        if number <= 1:
            return True
        else:
            return False

    def check_too_few_revision_charges(self):
        """Compare the number of revisions for the item versus the number
        of revision charges applied to the item.
        """
        rev_charge_types = ChargeType.objects.filter(category__name="Revision")
        revisions = Revision.objects.filter(item=self).count()
        rev_charges = Charge.objects.filter(
            item=self, description__in=rev_charge_types
        ).count()
        # Flag as False if the number of revisions exceeds the charges for revisions.
        if revisions > rev_charges:
            return True
        else:
            return False

    def check_fileout_post_production(self):
        """Return true if there is a file out without a post production charge.
        Don't flag Kenton Corrugated item.
        """
        # Check if its a Kenton Corrugated item.
        kenton_corrugated_flag = False
        if self.printlocation:
            if (
                self.printlocation.plant.name == "Kenton"
                and self.printlocation.press.name == "Corrugated"
            ):
                kenton_corrugated_flag = True

        # Check everything else.
        if (
            Charge.objects.filter(
                item=self, description__type__startswith="Post Production"
            ).count()
            == 0
            and self.is_filed_out()
            and not kenton_corrugated_flag
            and not self.steps_with
        ):
            return True
        else:
            return False

    def check_prepress_charges(self):
        """Return True if there is no Prepress Package or Automated Corrugated
        charge, the item has been proofed, and the job is not a press change.
        """
        check_types = ["Prepress Package", "Automated Corrugated"]
        if (
            self.current_proof_date()
            and not self.job.duplicated_from
            and Charge.objects.filter(
                item=self, description__type__in=check_types
            ).count()
            == 0
        ):
            return True
        else:
            return False

    def check_color_keys(self):
        """Return True if the item is printing at Shelbyville, item has filed out,
        color keys have not been charged, and it's not a corrugated job.
        """
        if self.printlocation:
            if (
                self.is_filed_out()
                and self.printlocation.plant.name == "Shelbyville"
                and Charge.objects.filter(
                    item=self, description__type="Color Keys"
                ).count()
                == 0
                and not self.printlocation.press.name == "Corrugated"
            ):
                return True
            else:
                return False
        else:
            return False

    def get_invoiced_total(self):
        """Sum of all invoiced charges for an item."""
        if self.job.workflow.name == "Beverage":
            check_charges_invoiced = Charge.objects.filter(
                item=self.id, bev_invoice__isnull=False
            )
        else:
            check_charges_invoiced = Charge.objects.filter(
                item=self.id, invoice_date__isnull=False
            )
        total = 0
        for single_charge in check_charges_invoiced:
            total += single_charge.amount

        return total

    def billing_warning(self):
        """Flag item if it appears to be under-billed."""
        if self.check_too_few_charges():
            return True
        elif self.check_too_few_revision_charges():
            return True
        else:
            return False

    def do_create_joblog_entry(
        self, logtype, logtext, date_override=None, user_override=None
    ):
        """Abstraction for creating joblog entries for items."""
        # Can't use get_joblog_model(). It causes a really strange error in some
        # funky edge case that I can't track down.
        new_log = JobLog()
        # Reference to the item's job.
        new_log.job = self.job
        # Reference to the item being logged about.
        new_log.item = self

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
        new_log.log_text = logtext
        new_log.save()

        # Allow overriding of the log date.
        if date_override:
            new_log.event_time = date_override
            # Have to save again because of the auto_now_add on event_time.
            new_log.save()

        return new_log

    def submit_jmf_queue(self, genxml_func):
        """Submits a generic JMF Queue Entry given a ticket name."""
        jmf = JMFSubmitQueueEntry(
            reverse("jdf-gen-item", args=[self.job.id, self.num_in_job, genxml_func])
        )
        jmf.execute()

    def genxml_jdf_fsb_colorkeys(self):
        """Create JDF instruction to Rip Tiffs using self.jdf_fsb_colorkeys()"""
        # We generate the path to the file via JobStorage as item.path_to_file
        # can be incorrect when jobs get archived
        head, mid, tail = self.path_to_file.partition("/Final_Files")
        path_to_file = (
            "file://"
            + settings.FS_SERVER_HOST
            + "/JobStorage/"
            + str(self.job.id)
            + mid
            + tail
        )
        proof_jdf = ItemJDF(self, {"SourceFileList": [path_to_file]})
        # Calculate the Backstage ticket name.
        #        rip_ticket = "/fripfile_s.file_sModel1.grx/%s" % self.jdf_fsb_colorkeys()
        rip_ticket = "/swft/%s" % self.jdf_fsb_colorkeys()

        # Rip the one-up source PDF
        proof_jdf.add_task_node(
            descriptive_name="RIP1up",
            node_id="n0001",
            task_id="TaskParamLink",
            ticket_name=rip_ticket,
            task_output_id="TIFFList",
        )
        return proof_jdf

    def fsb_colorkeys_queue(self):
        """Creates a queue of colorkeys so that they are not all thrown into the jdf
        folder at once which causes issues. A cron grabs them from the queue and then
        they are processed at a rate automation engine likes
        """
        new_color_key = ColorKeyQueue()
        new_color_key.item = self
        new_color_key.save()

    def do_jdf_fsb_colorkeys(self):
        """Tells Backstage to execute the JDF generated by genxml_jdf_fsb_colorkeys()."""
        # self.submit_jmf_queue('fsb_proof')
        self.genxml_jdf_fsb_colorkeys().send_jdf()

        # Create a Job Log event that this happened. (Joblog not used to track)
        log_text = (
            "Color Keys sent to Shelbyville for Item #%s in job." % self.num_in_job
        )
        self.do_create_joblog_entry(JOBLOG_TYPE_NOTE, log_text)

    def do_jdf_bev_die(self, destination_path):
        """Tells Automatin Engine to execute the JDF generated by
        genxml_jdf_bev_die().
        """
        # self.submit_jmf_queue('fsb_proof')
        self.genxml_jdf_bev_die(destination_path).send_jdf()

    def genxml_jdf_bev_die(self, destination_path):
        """Create JDF instruction to create a PDF with the appropriate die lines
        for beverage items.
        """
        die_jdf = ItemJDF(self, {"SourceFileList": [destination_path]})

        # Automation Engine ticket name.
        rip_ticket = "/swft/BeverageTemplateWorkflow"

        # Rip the one-up source PDF
        die_jdf.add_task_node(
            descriptive_name="RGB PDF",
            node_id="n0001",
            task_id="PDFLink",
            ticket_name=rip_ticket,
            task_output_id="PDFFileList",
        )

        return die_jdf

    def genxml_jdf_fsb_proof(self):
        """Create JDF instruction to
        A) Rip Tiffs using self.jdf_fsb_proof()
        B) Common RGB PDF ticket (to Proof folder in job)
        C) Common RGB JPG ticket (for VRML renders)
        NOTE: A proof will be printed out unless the Manual rip_ticket is used.
        """
        proof_jdf = ItemJDF(self, {"SourceFileList": [self.path_to_file]})
        # Calculate the Backstage ticket name.
        rip_ticket = "/fripfile_s.file_sModel1.grx/%s" % self.jdf_fsb_proof()

        # Manual rip ticket may be used for JDF testing.
        # rip_ticket = "/fripfile_s.file_sModel1.grx/Manual"

        # print "TICKET", rip_ticket

        # Rip the one-up source PDF
        proof_jdf.add_task_node(
            descriptive_name="RIP1up",
            node_id="n0001",
            task_id="TaskParamLink",
            ticket_name=rip_ticket,
            task_output_id="TIFFList",
            smartmark_set="!QuickApproval-Master",
        )
        # Create a RGB PDF from the source PDF
        proof_jdf.add_task_node(
            descriptive_name="RGB PDF",
            node_id="n0002",
            task_id="PDFLink",
            ticket_name="/batchbrix.pdfout/AutosavePDF",
            task_output_id="PDFFileList",
        )
        # Create a RGB JPG for renders from the source PDF
        proof_jdf.add_task_node(
            descriptive_name="RGB PDF",
            node_id="n0003",
            task_id="JPGLink",
            ticket_name="/LINKEDGETASK/FSB_JPG for Rendering",
            task_output_id="JPGFileList",
        )
        return proof_jdf

    def genxml_jdf_flexproof_fsb_proof(self):
        """Create JDF instruction to
        A) Rip Tiffs using self.jdf_fsb_flexproof()
        NOTE: A proof will be printed out unless the Manual rip_ticket is used.
        """
        proof_jdf = ItemJDF(self, {"SourceFileList": [self.path_to_file]})
        # Calculate the Backstage ticket name.
        # If we switch to workflows, replace forktask with 'swft'

        # rip_ticket = "/swft/%s" % self.jdf_fsb_flexproof()
        rip_ticket = "/swft/%s" % "FSB Smart Contract Proofing"

        # Manual rip ticket may be used for JDF testing.
        # rip_ticket = "/fripfile_s.file_sModel1.grx/Manual"

        # Rip the one-up source PDF
        proof_jdf.add_task_node(
            descriptive_name="RIP1up",
            node_id="n0001",
            task_id="TaskParamLink",
            ticket_name=rip_ticket,
            task_output_id="TIFFList",
        )

        return proof_jdf

    def genxml_jdf_flexproof_fsb_proof_manual(self):
        """Create JDF instruction to
        A) Rip Tiffs using self.jdf_fsb_flexproof()
        NOTE: A proof will be printed out unless the Manual rip_ticket is used.
        """
        # We generate the path to the file via JobStorage as item.path_to_file
        # can be incorrect when jobs get archived
        head, mid, tail = self.path_to_file.partition("/Final_Files")
        path_to_file = (
            "file://"
            + settings.FS_SERVER_HOST
            + "/JobStorage/"
            + str(self.job.id)
            + mid
            + tail
        )
        proof_jdf = ItemJDF(self, {"SourceFileList": [path_to_file]})
        # Calculate the Backstage ticket name.
        # If we switch to workflows, replace forktask with 'swft'

        # rip_ticket = "/swft/%s" % self.jdf_fsb_flexproof_manual()
        rip_ticket = "/swft/%s" % "FSB Smart Manual Proofing"
        print(rip_ticket)

        # Manual rip ticket may be used for JDF testing.
        # rip_ticket = "/fripfile_s.file_sModel1.grx/Manual"

        # Rip the one-up source PDF
        proof_jdf.add_task_node(
            descriptive_name="RIP1up",
            node_id="n0001",
            task_id="TaskParamLink",
            ticket_name=rip_ticket,
            task_output_id="TIFFList",
        )

        return proof_jdf

    def genxml_jdf_carton_contract_proof(self):
        """Create JDF instruction to run the 1up through the Carton Smart Proofing
        workflow in Automation Engine.
        """
        # We generate the path to the file via JobStorage as item.path_to_file
        # can be incorrect when jobs get archived
        head, mid, tail = self.path_to_file.partition("/Final_Files")
        path_to_file = (
            "file://"
            + settings.FS_SERVER_HOST
            + "/JobStorage/"
            + str(self.job.id)
            + mid
            + tail
        )
        proof_jdf = ItemJDF(self, {"SourceFileList": [path_to_file]})
        # AutoEng ticket name.
        rip_ticket = "/swft/%s" % "Carton Smart Proofing"
        # Rip the one-up source PDF
        proof_jdf.add_task_node(
            descriptive_name="RIP1up",
            node_id="n0001",
            task_id="TaskParamLink",
            ticket_name=rip_ticket,
            task_output_id="TIFFList",
        )

        return proof_jdf

    def genxml_jdf_tiff_to_pdf(self):
        """Create JDF instruction to create a PDF proof with the appropriate die
        lines for beverage items from their tiffs.
        """
        # Get the file path for each tiff.
        tiff_paths = []

        # Get info about this item's tiffs from the fs_api.
        tiff_list = fs_api.list_item_tiffs(self.job.id, self.num_in_job)

        # Add each tiff's file path to the list.
        for tiff in tiff_list:
            head, mid, tail = tiff["file_path"].partition("/JobStorage")
            path_to_file = "file://" + settings.FS_SERVER_HOST + mid + tail
            tiff_paths.append(path_to_file)

        # Now the JDF
        tiff_jdf = ItemJDF(self, {"SourceFileList": tiff_paths})

        # Automation Engine ticket name.
        rip_ticket = "/swft/BeverageTiffToPDF"

        # Run the AE ticket
        tiff_jdf.add_task_node(
            descriptive_name="RGB PDF",
            node_id="n0001",
            task_id="TIFFLink",
            ticket_name=rip_ticket,
            task_output_id="PDFFileList",
        )

        return tiff_jdf

    def do_jdf_fsb_proof(self):
        """Tells Backstage to execute the JDF generated by genxml_jdf_fsb_proof()."""
        # self.submit_jmf_queue('fsb_proof')
        # self.genxml_jdf_fsb_proof().send_jdf()
        # As of Oct 7, 2010, use Flexproof workflow by default...
        self.do_jdf_fsb_proof_flexproof()

    def do_jdf_fsb_proof_flexproof(self):
        """Tells Backstage to execute the JDF generated by genxml_jdf_flexproof_fsb_proof()."""
        # self.submit_jmf_queue('fsb_proof')
        self.genxml_jdf_flexproof_fsb_proof().send_jdf()

    def do_jdf_fsb_proof_flexproof_manual(self):
        """Tells Backstage to execute the JDF generated by genxml_jdf_flexproof_fsb_proof_manual()."""
        # self.submit_jmf_queue('fsb_proof')
        self.genxml_jdf_flexproof_fsb_proof_manual().send_jdf()

    def do_jdf_carton_contract_proof(self):
        """Tells AutoEng to execute the JDF generated by genxml_jdf_carton_contract_proof()."""
        self.genxml_jdf_carton_contract_proof().send_jdf()

    def do_jdf_tiff_to_pdf(self):
        """Tells Automation Engine to execute the JDF generated by
        genxml_jdf_tiff_to_pdf().
        """
        self.genxml_jdf_tiff_to_pdf().send_jdf()

    def genxml_jdf_fsb_ffo(self):
        extra_vars = {
            "PreppedFileList": {"Status": "Unavailable"},
            "PLAFileList": {"Status": "Unavailable"},
            "TIFFList": {"Status": "Unavailable"},
        }

        file_set = []
        file_set.append(self.path_to_file)
        if self.is_master_stepped_item():
            # If this is a master item, append all it's children to the
            # file list.
            for item in self.steps_with_item.all():
                file_set.append(item.path_to_file)
        # Create ItemJDF object with input file list.
        sr_jdf = ItemJDF(self, {"SourceFileList": file_set}, extra_vars=extra_vars)

        """
        sr_jdf = ItemJDF(self, {'SourceFileList': [self.path_to_file]},
                         extra_vars=extra_vars)
        """
        # Use the Prepare Station task to resave the PDF prior to processing.
        # This will retrigger and update the SmartMarks used to populate plate codes.
        smartStepRIP_ticket = "/swft/FSB Smart Step and RIP"
        sr_jdf.add_task_node(
            "Workflow",
            node_id="n0001",
            task_id="SmartStepRIP",
            ticket_name=smartStepRIP_ticket,
            task_output_id="FSBSmartStepRIP",
        )
        return sr_jdf

    def do_jdf_fsb_ffo(self):
        """Tells Backstage to execute the JDF generated by genxml_jdf_fsb_ffo()."""
        # self.submit_jmf_queue('fsb_ffo')
        self.genxml_jdf_fsb_ffo().send_jdf()

    def genxml_jdf_bev_workflow(self):
        """Create a JDF to:
        A) Tabular Step & Repeat using self.jdf_bev_sr()
        B) Take resulting file from Step A and use self.jdf_bev_srrip()
        Backend script will take finished JDF and use to trigger creation
        of high and low res PDFs of the TIFFs.
        """
        # Create the tiff folder in advance (required for this to work).
        fs_api.create_tiff_folder(self.job.id, self.num_in_job, self.bev_nomenclature())
        # Extra Parameters passed with the ResourcePool.
        extra_vars = {
            "PLAFileList": {"Status": "Unavailable"},
            "TIFFList": {"Status": "Unavailable"},
        }
        sr_jdf = ItemJDF(
            self, {"SourceFileList": [self.path_to_file]}, extra_vars=extra_vars
        )

        if self.jdf_no_step:
            # Skip the stepping, just RIP the file.
            rip_ticket = "/swft/%s" % "Beverage Smart RIP"
            # print "RIP TICKET", rip_ticket
            # <!--NODE: RIP STEPPED FILE - VARIABLE XXXSTEPRIPTICKETXXX-->
            sr_jdf.add_task_node(
                "Beverage Smart RIP", "n0001", "PLALink", rip_ticket, "TIFFList"
            )
        # Cartons
        else:
            # Cartons will get stepped, then RIPped.
            sr_ticket = "/swft/%s" % "Beverage Smart Step and RIP"
            # print "SR TICKET", sr_ticket
            # <!--NODE: STEP AND REPEAT ONE-UP FILE - VARIABLE XXXSTEPTICKETXXX-->
            sr_jdf.add_task_node(
                "Beverage Smart StepRIP", "n0001", "uplink", sr_ticket, "PLAFileList"
            )

        return sr_jdf

    def do_jdf_bev_workflow(self):
        """Tells Backstage to execute the JDF generated by genxml_jdf_bev_workflow()."""
        # self.submit_jmf_queue('bev_workflow')
        self.genxml_jdf_bev_workflow().send_jdf()

    """
    JDF Calculations for Esko Backstage
    """

    def jdf_fsb_proof(self):
        """Calculation for jdf ticket name for proofing - foodservice"""
        if self.printlocation.press.short_name:
            press = self.printlocation.press.short_name
        else:
            press = self.printlocation.press.name
        jdfticket = (
            str(self.size.get_product_substrate_display())
            + "_"
            + str(press)
            + "_"
            + str(self.platepackage.platetype)
        )
        return jdfticket

    def jdf_fsb_flexproof(self):
        """Calculation for jdf ticket name for ripping for Esko FlexProof - Foodservice"""
        if self.printlocation:
            if self.printlocation.press.short_name:
                press = self.printlocation.press.short_name
            else:
                press = self.printlocation.press.name
        else:
            press = None
        if self.platepackage:
            plateType = self.platepackage.platetype
        else:
            plateType = None
        return "%s_%s_%s" % (
            self.size.get_product_substrate_display(),
            str(press),
            str(plateType),
        )

    def jdf_fsb_flexproof_manual(self):
        """Calculation for jdf ticket name for ripping for Esko FlexProof - Foodservice.
        Manual ticket -- no ink coverage, no approval box, no PDF.
        """
        return "%s_Manual" % self.jdf_fsb_flexproof()

    def jdf_fsb_sr(self):
        """Calculation for jdf ticket name for stepping - foodservice"""
        if self.printlocation:
            if self.printlocation.press.short_name:
                press_plus_mfg = str(self.printlocation.press.short_name)
            else:
                press_plus_mfg = str(self.printlocation.press.name)
        else:
            press_plus_mfg = str(None)

        if self.special_mfg:
            press_plus_mfg = press_plus_mfg + "-" + str(self.special_mfg.name)

        if self.size.acts_like:
            size = str(self.size.acts_like)
        else:
            size = str(self.size)

        if self.printlocation:
            jdfticket = (
                str(self.printlocation.plant) + "_" + press_plus_mfg + "_" + size
            )
        else:
            jdfticket = str(None) + "_" + press_plus_mfg + "_" + size
        return jdfticket

    def jdf_fsb_rip(self):
        """Calculation for jdf ticket name for ripping the s&r - foodservice"""
        if self.printlocation:
            if self.printlocation.press.short_name:
                press = self.printlocation.press.short_name
            else:
                press = self.printlocation.press.name
        else:
            press = None
        if self.platepackage:
            plateMaker = self.platepackage.platemaker
        else:
            plateMaker = None
        if self.platepackage:
            plateType = self.platepackage.platetype
        else:
            plateType = None
        jdfticket = (
            "SR "
            + str(plateMaker)
            + " - "
            + str(plateType)
            + "_"
            + str(self.size.get_product_substrate_display())
            + "_"
            + str(press)
        )
        return jdfticket

    def jdf_fsb_colorkeys(self):
        """JDF ticket name for ripping color keys to print
        in Shelbyville platemaking dept. - foodservice
        """
        jdfticket = "Color Keys to Shelbyville"
        return jdfticket

    def jdf_bev_sr(self):
        """Calculation for jdf ticket name for stepping - beverage
        End result should be something like Shelbyville_8oz-Meco_4up or Hughes_1Liter_2up
        """
        if self.jdf_no_step:
            return None
        else:
            if self.size.is_bev_panel():
                size = str(self.size).replace(" ", "")
                plantdesignation = ""
                if self.printlocation.plant.name in ("Clinton", "Olmsted Falls"):
                    plantdesignation = self.printlocation.plant.name
                jdfticket = (
                    size.replace(" ", "") + "_" + str(self.platepackage.platetype)
                )
                if plantdesignation:
                    jdfticket += "_%s" % plantdesignation
                jdfticket += "_%sup" % str(self.num_up)
            else:
                size = str(self.size).replace("- Fitment", "").replace(" ", "")
                # Special_mfg for Beverage will be Eco/Meco typically.
                # If the special_mfg is Meco, and the item name already contains Eco,
                # Replace Eco with Meco. (This prevents stuff like 8oz-eco-meco being sent)
                plant_designation = self.job.temp_printlocation.plant.name
                if self.special_mfg:
                    # Replace -Straw-Gable# with '' to allow JDF to make the correct step & repeat call.
                    # We can do this b/c the PDF die for these jobs match current PDFs.
                    # ie. the same step & repeat can be used...
                    size = (
                        size.replace("-Eco", "")
                        .replace("-Straw-Gable2", "")
                        .replace("-Straw-Gable4", "")
                    )
                    size += "-" + str(self.special_mfg.name)
                    # if self.special_mfg.name == "Meco":
                    #    if size.find("Eco") != -1:
                    #        size = size.replace("Eco", "Meco")
                    # Shouldn't need this anymore. At one point, 2up Raleigh Eco
                    # sizes were unique and needed the plant designation, now
                    # all step and repeats will need it.
                    # if self.special_mfg.name == "Eco" and self.job.temp_printlocation.plant.name == "Raleigh" and self.num_up == 2:
                    #    plant_designation = "Raleigh"
                platemaker = str(self.platepackage.platemaker)
                # 'Transfer' platemaker are for items that will be setup
                # like Shelbyville, but then transfered to another platemaker.
                if platemaker == "Transfer":
                    platemaker = "Shelbyville"
                jdfticket = (
                    platemaker
                    + "_"
                    + plant_designation
                    + "_"
                    + size
                    + "_"
                    + str(self.num_up)
                    + "up"
                    + "_"
                    + str(self.platepackage.platetype)
                )
                # Check to see if the item's been flagged for pre-distortion or
                # legacy distortion and name the ticket accordingly.
                if self.uses_old_distortion:
                    jdfticket += "_Legacy"
                if self.uses_pre_distortion:
                    jdfticket += "_Predistorted"

            return jdfticket

    def jdf_bev_srrip(self):
        """Calculation for jdf ticket name for ripping the s&r - beverage"""
        jdfticket = "Error"
        # No DGC override should take priority in selection.
        if self.jdf_no_dgc:
            jdfticket = "Beverage - 2400 No DGC"
        elif self.jdf_no_step:
            jdfticket = "Beverage - 2400 DGC RIP ONLY"
        # Carton or panel.
        else:
            if self.platepackage.platemaker.name == "Cyber Graphics":
                jdfticket = (
                    "Beverage - 2400 DGC - Cyber Graphics"
                    + " - "
                    + self.platepackage.platetype
                )
            else:
                jdfticket = (
                    "Beverage - 2400 DGC - "
                    + self.platepackage.platemaker.name
                    + " - "
                    + self.platepackage.platetype
                )
        return jdfticket

    def plant_reviews(self):
        """Retrieves and returns plant reviews for a given item."""
        reviews = self.itemreview_set.filter(review_catagory="plant")
        return reviews

    def demand_reviews(self):
        """Retrieves and returns demand reviews for a given item."""
        reviews = self.itemreview_set.filter(review_catagory="demand")
        return reviews

    def market_reviews(self):
        """Retrieves and returns plant reviews for a given item."""
        reviews = self.itemreview_set.filter(review_catagory="market")
        return reviews

    def review_check(self):
        """Checks to see if the item is ready for a plant or demand planning review. If so,
        it creates the appropriate review object using the Item Review model.
        """
        if self.printlocation:
            if (
                self.printlocation.plant.name
                in ("Visalia", "Shelbyville", "Kenton", "Clarksville", "Pittston")
                and self.printlocation.press.name not in ("Corrugated", "Other")
                and not self.press_change
            ):
                current_plant_reviews = self.itemreview_set.filter(
                    review_catagory="plant"
                )
                if not current_plant_reviews and self.printlocation:
                    self.itemreview_set.create(review_catagory="plant")
                    if self.printlocation.plant.name in ("Shelbyville"):
                        # sends email to the Shelbyville plant review group for shelby items.
                        mail_send_to = []
                        group_members = User.objects.filter(
                            groups__name="EmailShelbyPlantReview", is_active=True
                        )
                        for manager in group_members:
                            mail_send_to.append(manager.email)
                        mail_from = (
                            "Gold - Clemson Support <%s>" % settings.EMAIL_SUPPORT
                        )
                        mail_subject = "Plant review for job: %s" % str(self.job)
                        mail_body = loader.get_template("emails/plant_review_email.txt")
                        mail_context = {"job": self.job, "item": self.num_in_job}
                        # send the email
                        msg = EmailMultiAlternatives(
                            mail_subject,
                            mail_body.render(mail_context),
                            mail_from,
                            mail_send_to,
                        )
                        msg.content_subtype = "html"
                        msg.send()
                else:
                    print(
                        "Can't generate plant review because one already exists or there's no print location."
                    )

                current_demand_reviews = self.itemreview_set.filter(
                    review_catagory="demand"
                )
                if not current_demand_reviews and self.printlocation:
                    self.itemreview_set.create(review_catagory="demand")
                else:
                    print(
                        "Can't generate demand review because one already exists or there's no print location."
                    )
            else:
                print(
                    "Can't generate reviews due to plant, print location, or press change."
                )

    def legacy_distortion_check(self):
        """Return True if the item meets the criteria to use legacy distortion
        based on:

        -Clinton (plant) 4oz eco, 6oz eco, 8oz eco Rubber plates
        -Olmsted Falls (plant) 4oz eco, 6oz eco, 8oz eco Rubber plates
        -Plated prior to February 2012

        This is just to alert users that the item MIGHT need to use legacy
        distortion. A human still needs to make that call and mark
        uses_old_distortion as true.
        """
        if self.printlocation:
            if (
                self.printlocation.plant.name in ("Olmsted Falls", "Clinton")
                and self.size.size in ("8oz - Eco", "6oz - Eco", "4oz - Eco")
                and self.platepackage.platetype == "Rub"
            ):
                return True
        else:
            return False


"""
--- Item Signals
"""


def item_pre_save(sender, instance, *args, **kwargs):
    """Things to happen in the point of saving an item before the actual save()
    call happens.
    """
    # If the Item has a Null or False value for its 'id' field, it's a new
    # item. Give it a new num_in_job.
    if not instance.id:
        # Count the number of items associated with the job.
        item_count = Item.objects.filter(job=instance.job).count()
        # Count + 1 is our new item number within the job.
        instance.num_in_job = item_count + 1
    if instance.job.workflow.name == "Beverage":
        # Use boolean on job to determine which nomenclature to use.
        # Switching 10/2009.
        if instance.job.use_new_bev_nomenclature:
            instance.bev_item_name = instance.new_bev_nomenclature()
        else:
            instance.bev_item_name = instance.recalc_bev_nomenclature()


def item_post_save(sender, instance, created, *args, **kwargs):
    """Things to happen after an item is saved."""
    if instance.job.workflow.name == "Foodservice":
        # Add Art Request charge.
        charge_type = ChargeType.objects.get(type="Art Request")
        if (
            Charge.objects.filter(item=instance, description=charge_type)
            or instance.job.id < 54000
        ):
            # Charge is already in place, do nothing.
            pass
        else:
            try:
                charge = Charge()
                charge.item = instance
                charge.description = charge_type
                charge.amount = charge_type.actual_charge()
                charge.save()
            except Exception:
                pass
        instance.review_check()
    # Call job save to regenerate keywords.
    instance.job.save()


def item_pre_delete(sender, instance, *args, **kwargs):
    """Things to happen before an item is deleted."""
    # Log Item saves.
    new_log = JobLog()
    new_log.job = instance.job
    # Instance is a copy of the item being saved.
    new_log.item = instance
    # Grab the user doing the saving from threadlocals.

    new_log.user = threadlocals.get_current_user()
    new_log.type = JOBLOG_TYPE_ITEM_DELETED
    new_log.log_text = "Item %s has been deleted." % (instance.num_in_job)
    new_log.save()
    """
    Re-name the old folder to preserve the files. Give it a timestamp
    to avoid future over-writes if the same item number is deleted again.
    """
    try:
        instance.delete_folder()
    except InvalidPath:
        # The folder could not be found, fail silently.
        pass


def item_post_delete(sender, instance, *args, **kwargs):
    """Things to happen after an item is deleted."""
    instance.job.recalc_item_numbers()


"""
--- Item Dispatchers
"""
signals.pre_save.connect(item_pre_save, sender=Item)
signals.post_save.connect(item_post_save, sender=Item)
signals.pre_delete.connect(item_pre_delete, sender=Item)
signals.post_delete.connect(item_post_delete, sender=Item)
"""
--- End Item Signals
"""
