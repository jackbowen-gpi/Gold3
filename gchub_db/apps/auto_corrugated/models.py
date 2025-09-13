"""Automatic Corrugated Generation System"""

import os
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import signals

from gchub_db.apps.auto_corrugated.documents.fsb_box import FSBBox, FSBLabel
from gchub_db.apps.joblog.app_defs import JOBLOG_TYPE_NOTE
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models import (
    Charge,
    ChargeType,
    Item,
    ItemCatalog,
    Job,
    PrintLocation,
    Revision,
)
from gchub_db.includes import general_funcs
from gchub_db.includes.model_fields import BigIntegerField
from gchub_db.middleware import threadlocals


class BoxItem(models.Model):
    """Link to items that can be used in the automated corrugated system"""

    item_name = models.CharField(max_length=64, unique=True)
    item = models.ForeignKey(
        "workflow.ItemCatalog",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={"workflow__name": "Foodservice"},
    )
    box_art = models.FileField(upload_to="autocorrugated_art", blank=True)
    # Description of item.
    english_description = models.CharField(max_length=255, blank=True)
    spanish_description = models.CharField(max_length=255, blank=True)
    french_description = models.CharField(max_length=255, blank=True)
    # Lid usage.
    english_lid_description = models.CharField(max_length=255, blank=True)
    spanish_lid_description = models.CharField(max_length=255, blank=True)
    french_lid_description = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["item_name"]

    def __str__(self):
        return self.item_name


def boxitem_pre_save(sender, instance, *args, **kwargs):
    """Things to do prior to a BoxItem being saved."""
    # If 'item' has a value, pull its name and store it in item_name on
    # the BoxItem for the sake of transparency. Not all BoxItem objects have
    # the 'item' FK populated, and instead rely on item_name. If we just
    # always get the item name from item_name, we'll have consistency.
    if instance.item:
        instance.item_name = instance.item.size


signals.post_save.connect(boxitem_pre_save, sender=BoxItem)


class BoxItemSpec(models.Model):
    """
    Different variants for FSB corrugated. Each BoxItem may have several
    combinations of dimensions and case/sleeve counts.
    """

    boxitem = models.ForeignKey(BoxItem, on_delete=models.CASCADE)
    plant = models.ForeignKey(
        "workflow.Plant",
        on_delete=models.CASCADE,
        limit_choices_to={"is_in_acs": "True"},
        blank=True,
        null=True,
    )
    length = models.FloatField(blank=True, null=True)
    width = models.FloatField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    case_count = models.IntegerField()
    sleeve_count = models.IntegerField(blank=True, null=True)
    is_first = models.BooleanField(default=False)

    class Meta:
        ordering = ["boxitem__item_name"]

    def __str__(self):
        return "%s -- %d/case" % (self.boxitem.item_name, self.case_count)


# Specify types of PDF box formats available.
ART_LABEL = 0
ART_NO_LABEL = 1
NO_ART_LABEL = 2
NO_ART_NO_LABEL = 3
PDF_ART_CHOICES = (
    (ART_LABEL, "Art with Label"),
    (ART_NO_LABEL, "Art with Blank Label"),
    (NO_ART_LABEL, "No Art with Label"),
    (NO_ART_NO_LABEL, "No Art with Blank Label"),
)

# Specify types of box formats available.
BOX_FORMAT_LEFT = 0
BOX_FORMAT_RIGHT = 1
BOX_FORMAT_CHOICES = (
    (BOX_FORMAT_LEFT, "Left"),
    (BOX_FORMAT_RIGHT, "Right"),
)


class GeneratedBox(models.Model):
    """Stored inputs from online form."""

    pdf_type = models.IntegerField(choices=PDF_ART_CHOICES, default=ART_LABEL, null=True)
    creation_date = models.DateTimeField("Date Info Entered", auto_now_add=True)
    six_digit_num = models.IntegerField()
    replaced_6digit = models.IntegerField(null=True)
    # nine_digit uses a code128 barcode
    # ***Don't show leading 0 in human readable form
    nine_digit_num = models.IntegerField()
    # fourteen_digit uses a i2of5 barcode
    fourteen_digit_num = BigIntegerField()
    item = models.ForeignKey(BoxItem, on_delete=models.CASCADE)
    spec = models.ForeignKey(BoxItemSpec, on_delete=models.CASCADE)
    text_line_1 = models.CharField(max_length=120)
    text_line_2 = models.CharField(max_length=120)
    sleeve_count = models.IntegerField()
    dim_width = models.FloatField("Box Width")
    dim_length = models.FloatField("Box Length")
    dim_height = models.FloatField("Box Height")
    plant = models.ForeignKey(
        "workflow.Plant",
        on_delete=models.CASCADE,
        limit_choices_to={"is_in_acs": "True"},
    )
    board_spec = models.CharField(max_length=50)
    case_color = models.CharField(max_length=75)
    sfi_stamp_box = models.BooleanField(default=True)
    sfi_stamp_cup = models.BooleanField("SFI Content Stamp", default=False)
    blank_label = models.BooleanField(default=False)
    box_format = models.IntegerField(choices=BOX_FORMAT_CHOICES, default=BOX_FORMAT_LEFT)
    pdf_output = models.FileField(upload_to="autocorrugated_output", blank=True)
    approved = models.BooleanField(default=False)

    # ADDING 1/2011
    entered_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="corrugated_created_by",
    )
    job = models.ForeignKey(
        "workflow.Job",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        limit_choices_to={"workflow__name": "Foodservice"},
        editable=False,
    )
    # True if the system should generate slugs for plates.
    make_slugs = models.BooleanField(default=False)
    # Ultimately, this will determine the size of the slugs to be made.
    # Right now, it's only Shelbyville making plates, so 14" is standard.
    platepackage = models.ForeignKey(
        "workflow.PlatePackage",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        limit_choices_to={"workflow__name": "Foodservice"},
    )
    plate_number = models.CharField(
        max_length=30,
        blank=True,
        null=True,
    )
    # The following 3 fields appear to be McDonalds-specific codes.
    # We probably won't need them, as they are used in 4 of 1873 entries
    # in old system.
    # wrin = models.CharField(max_length=120)
    # wsi = models.CharField(max_length=120)
    # mcdonalds_barcode = models.IntegerField()

    def generate_box_pdf(self, box_pdf, method, save_to_job=False, creator=None):
        """
        Generates a box PDF from the saved values.
        box_pdf: (file-like object) - also, the filename
        """
        # Set up save path. If save_to_job is True, override the given box_pdf (filename)
        # value with the full path to the job folder.

        if save_to_job and self.job:
            # filepath = self.job.get_folder()

            filepath = "%s/Final_Files" % self.job.get_folder()
            file_folder = "%s KD" % self.item.item_name
            final_file_folder = "%s/%s-1 %s" % (filepath, self.job.id, file_folder)

            #            filename = "%s-%s.pdf" % (self.nine_digit_num,
            #                                              datetime.now().strftime('%d_%m-%H_%M_%S'))

            filename = "%s-1 %s.pdf" % (self.job.id, file_folder)

            #            fullpath = os.path.join(filepath, filename)
            fullpath = os.path.join(final_file_folder, filename)
        else:
            # If not saving to the job, use the StringIO passed along from
            # the view to save through the browser.
            fullpath = box_pdf

        if self.box_format == BOX_FORMAT_LEFT:
            box_format = "left"
        else:
            box_format = "right"

        # TODO: These need to be stored somewhere.
        item_description_english = self.item.english_description
        item_description_spanish = self.item.spanish_description
        item_description_french = self.item.french_description
        lid_information_english = self.item.english_lid_description
        lid_information_spanish = self.item.spanish_lid_description
        lid_information_french = self.item.french_lid_description

        print_header = True

        # Create PDF in watermarked, locked state if not approved.
        if creator is None:
            # We pass the user into this function in all cases so that there should be a user if this is run in a thread
            # where threadlocals.get_user() will normally not work. In the off chance that a the code gets here without a
            # user then we can just grab a random one that will fail the permission check and display a non-water marked
            # PDF which is the safest outcome.
            current_user = User.objects.all()[0]
        else:
            current_user = creator

        print("Current User %r" % current_user)
        if self.approved and current_user.has_perm("accounts.clemson_employee"):
            watermark = False
            make_slugs = self.make_slugs
        else:
            watermark = True
            make_slugs = False

        if self.job:
            job_id = self.job.id
            if save_to_job or current_user.has_perm("accounts.clemson_employee"):
                watermark = False
            else:
                watermark = True
        else:
            job_id = None

        if self.job:
            artist = self.job.artist
        else:
            artist = None

        print("making the FSBBOX")
        gbox = FSBBox(
            fullpath,
            self.dim_height,
            self.dim_width,
            self.dim_length,
            box_format,
            self.six_digit_num,
            self.replaced_6digit,
            self.nine_digit_num,
            self.fourteen_digit_num,
            self.text_line_1,
            self.text_line_2,
            self.plant.name,
            self.spec.case_count,
            self.sleeve_count,
            self.item.item_name,
            item_description_english,
            item_description_spanish,
            item_description_french,
            lid_information_english,
            lid_information_spanish,
            lid_information_french,
            self.pdf_type,
            self.sfi_stamp_box,
            self.sfi_stamp_cup,
            print_header,
            self.board_spec,
            self.case_color,
            make_slugs,
            artist,
            self.plate_number,
            label_id=self.id,
            method=method,
            job_id=job_id,
            watermark=watermark,
        )

        gbox.save_to_pdf()
        return box_pdf

    def create_job_for_box(self, creation_type="PDF_Only", change_requested=""):
        """
        Creates a job in the workflow app that the box is linked to. The job will
        serve billing purposes, as well as allow for custom modifications by
        an artist to a automatically generated box.
        Three options for creation:
        1. "PDF_Only": User just wants the PDF as is, typically for use by
           an external plate supplier.
        2. "Tiffs": User wants plates to be made internally. Artist must
           create and QC 1-Bit-Tiffs before delivering to the platemaker.
        3. "Changes": User is almost happy with the graphic layout, but requires
           a few changes or customizations that the automated system is not
           capable of.
        """
        workflow = Site.objects.get(name="Foodservice")
        # Set arbitrary due date of 14 days from now (UTC-naive via helper).
        due_date = general_funcs._utcnow_naive() + timedelta(days=14)

        # Create master job record.
        job_name = "%s KD - %s" % (self.item.item_name, self.plant.name)

        # Create a new job if there isn't one already. However, this method should
        # really only be called once -- on approval of the ACS PDF.
        if not self.job:
            # Create a new job in GOLD with required information, then create
            # the folder.
            box_job = Job(
                name=job_name,
                workflow=workflow,
                customer_email=self.entered_by.email,
                due_date=due_date,
                salesperson=self.entered_by,
            )
            box_job.save()
            box_job.create_folder()
        else:
            box_job = self.job

        # Check to see if a KD item exists in the Item Catalog, if not, make it.
        catalog_name = "%s KD" % self.item.item_name

        try:
            catalog_link = ItemCatalog.objects.get(size=catalog_name)
        except ItemCatalog.DoesNotExist:
            new_item = ItemCatalog(size=catalog_name, mfg_name=catalog_name, workflow=workflow)
            new_item.save()
            catalog_link = new_item

        # Create item for the box.
        printlocation = PrintLocation.objects.get(press__name="Corrugated", plant=self.plant)
        box_item = Item(
            job=box_job,
            workflow=workflow,
            size=catalog_link,
            description=str(self.six_digit_num),
            printlocation=printlocation,
            platepackage=self.platepackage,
            case_pack=self.spec.case_count,
            fsb_nine_digit=self.nine_digit_num,
        )
        box_item.save()
        box_item.create_folder()
        box_item.do_fsb_nine_digit()
        # This call to import_qad_data() will automatically import the UPC & SCC numbers
        box_item.import_qad_data()

        # Set to recently saved box item.
        item = box_item
        # Apply billing for this item.
        charge_type = ChargeType.objects.get(type="Automated Corrugated")
        charge = Charge(item=item, description=charge_type, amount=charge_type.base_amount)
        charge.save()
        # Add billing for PDF Proof.
        charge_type = ChargeType.objects.get(type="PDF Proof")
        charge = Charge(item=item, description=charge_type, amount=charge_type.base_amount)
        charge.save()
        # TODO: Create ItemColor FK'd to Item using the GeneratedBox case_color field.

        # Automatically perform actions for proof out, etc... on this item.
        #        item.do_proof()
        if creation_type == "Changes":
            text = "Job was created by the Automated Corrugated System."
            log = JobLog(job=box_job, user=self.entered_by, type=JOBLOG_TYPE_NOTE, log_text=text)
            log.save()
            change_requested = "See Changes."
            rev = Revision(item=item, comments=change_requested, due_date=due_date)
            rev.save()
        else:
            # Create JobLog reflecting creation from the ACS.
            text = "Job was created and approved by the Automated Corrugated System."
            log = JobLog(job=box_job, user=self.entered_by, type=JOBLOG_TYPE_NOTE, log_text=text)
            log.save()

        # Save job link to model.
        self.job = box_job
        self.save()
        return box_job

    def __str__(self):
        """String representation."""
        return "%d" % self.nine_digit_num

    class Meta:
        verbose_name_plural = "Generated Boxes"

    def save(self):
        """Overriding the GeneratedBox's standard save() to capture user who created it."""
        current_user = threadlocals.get_current_user()
        if current_user and current_user.is_authenticated:
            if not self.entered_by:
                self.entered_by = current_user
                if current_user.has_perm("accounts.clemson_employee"):
                    self.approved = True

        return super(GeneratedBox, self).save()


class GeneratedLabel(models.Model):
    """Stored inputs from online form for building a label."""

    creation_date = models.DateTimeField("Date Info Entered", auto_now_add=True)
    nine_digit_num = models.IntegerField()
    fourteen_digit_num = BigIntegerField()
    text_line_1 = models.CharField(max_length=120)
    text_line_2 = models.CharField(max_length=120)
    pdf_type = 2

    def generate_label_pdf(self, label_pdf, label_id):
        """
        Generates a label PDF from the saved values.
        label_pdf: (file-like object)
        """
        glabel = FSBLabel(
            label_pdf,
            self.nine_digit_num,
            self.fourteen_digit_num,
            self.text_line_1,
            self.text_line_2,
            self.pdf_type,
            label_id,
        )

        glabel.save_to_pdf()
        return label_pdf

    def __str__(self):
        """String representation."""
        return "%d" % self.nine_digit_num
