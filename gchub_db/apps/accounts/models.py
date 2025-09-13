"""Contains account and user-related models."""

from datetime import date

from includes.notification_manager import send_user_notification
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Sum, signals

# Make these easy to reach for other things.
GROWL_STATUS_DISABLED = 0
GROWL_STATUS_ENABLED = 1
GROWL_STATUS_STICKY = 2

# Define the choices menu for all of the Growl fields.
GROWL_STATUS_TYPES = (
    (GROWL_STATUS_DISABLED, "Disabled"),
    (GROWL_STATUS_ENABLED, "Enabled"),
    (GROWL_STATUS_STICKY, "Enabled - Sticky"),
)


class UserProfile(models.Model):
    """
    The UserProfile model acts as an extension of Django's User class. Code
    can get to this model by using a User object's profile attribute.
    For more information on this, see:
    http://www.djangoproject.com/documentation/authentication/#storing-additional-information-about-users
    """

    # Points back to the User object this profile is associated with.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    # Their office phone number.
    phone_number = models.CharField(max_length=50, blank=True)
    # This is the most recently tracked IP address.
    ip_address = models.CharField(max_length=50, blank=True)
    # When the user last visited a page on GOLD.
    last_page_request = models.DateTimeField(blank=True, null=True)
    # The name of the user's workstation.
    machine_name = models.CharField(max_length=100, blank=True)

    total_vacation = models.IntegerField(default=0, editable=False, verbose_name="Total Vacation")
    total_sick = models.IntegerField(default=5, editable=False, verbose_name="Total Sick")

    """
    Growl preferences
    """
    # Master toggle for all notifications
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name="Enable All Notifications",
        help_text="Master switch to enable/disable all desktop notifications",
    )

    # Theme preferences
    THEME_CHOICES = [
        ("default", "Default Theme"),
        ("dark", "Dark Theme"),
        ("light", "Light Theme"),
    ]

    preferred_theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default="default",
        verbose_name="Preferred Theme",
        help_text="Choose your preferred color theme for the interface",
    )

    enable_animations = models.BooleanField(
        default=True,
        verbose_name="Enable Animations",
        help_text="Enable smooth transitions and animations in the interface",
    )

    custom_primary_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Custom Primary Color",
        help_text="Custom hex color code for primary theme color (e.g., #007bff)",
    )

    custom_accent_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Custom Accent Color",
        help_text="Custom hex color code for accent theme color (e.g., #28a745)",
    )

    growl_hear_approvals = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="Item Approvals",
    )
    growl_hear_jdf_processes = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="JDF Events",
    )
    growl_hear_new_beverage_jobs = models.IntegerField(
        default=GROWL_STATUS_DISABLED,
        choices=GROWL_STATUS_TYPES,
        verbose_name="New Beverage Jobs",
    )
    growl_hear_new_foodservice_jobs = models.IntegerField(
        default=GROWL_STATUS_DISABLED,
        choices=GROWL_STATUS_TYPES,
        verbose_name="New Foodservice Jobs",
    )
    growl_hear_new_carton_jobs = models.IntegerField(
        default=GROWL_STATUS_DISABLED,
        choices=GROWL_STATUS_TYPES,
        verbose_name="New Carton Jobs",
    )
    growl_hear_9digit_entry = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="9-Digit Number Entries",
    )
    growl_hear_whoops = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="Whoopsies!",
    )
    growl_hear_revisions = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="New Revisions",
    )
    growl_hear_plant_rejections = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="Plant Rejections",
    )
    growl_hear_demand_planning_rejections = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="Demand Planning Rejections",
    )
    growl_hear_job_db_uploads = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="Job Database Document Uploads",
    )
    # For press changes and item duplications
    growl_hear_item_duplication = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="Item Duplications/Press Changes",
    )
    growl_hear_gold_changes = models.IntegerField(
        default=GROWL_STATUS_ENABLED,
        choices=GROWL_STATUS_TYPES,
        verbose_name="GOLD Changes",
    )
    growl_hear_todays_events = models.IntegerField(
        default=GROWL_STATUS_STICKY,
        choices=GROWL_STATUS_TYPES,
        verbose_name="Today's Events",
    )

    # Search interface preferences
    use_legacy_search = models.BooleanField(
        default=True,
        verbose_name="Use Legacy Search Interface",
        help_text="When enabled, job and item search will use the original GOLD interface",
    )

    # Job search criteria preferences
    job_search_brand = models.BooleanField(
        default=True,
        verbose_name="Search Brand Field",
        help_text="Include brand field in job searches",
    )
    job_search_customer = models.BooleanField(
        default=True,
        verbose_name="Search Customer Field",
        help_text="Include customer field in job searches",
    )
    job_search_po_number = models.BooleanField(
        default=True,
        verbose_name="Search PO Number Field",
        help_text="Include PO number field in job searches",
    )
    job_search_comments = models.BooleanField(
        default=True,
        verbose_name="Search Comments Field",
        help_text="Include comments field in job searches",
    )
    job_search_instructions = models.BooleanField(
        default=True,
        verbose_name="Search Instructions Field",
        help_text="Include instructions field in job searches",
    )
    job_search_salesperson = models.BooleanField(
        default=True,
        verbose_name="Search Salesperson Field",
        help_text="Include salesperson field in job searches",
    )
    job_search_artist = models.BooleanField(
        default=True,
        verbose_name="Search Artist Field",
        help_text="Include artist field in job searches",
    )

    # Item search criteria preferences
    item_search_description = models.BooleanField(
        default=True,
        verbose_name="Search Item Description",
        help_text="Include item description field in item searches",
    )
    item_search_upc = models.BooleanField(
        default=True,
        verbose_name="Search UPC Field",
        help_text="Include UPC field in item searches",
    )
    item_search_brand = models.BooleanField(
        default=True,
        verbose_name="Search Brand Field",
        help_text="Include brand field in item searches",
    )
    item_search_customer = models.BooleanField(
        default=True,
        verbose_name="Search Customer Field",
        help_text="Include customer field in item searches",
    )
    item_search_comments = models.BooleanField(
        default=True,
        verbose_name="Search Comments Field",
        help_text="Include comments field in item searches",
    )
    item_search_specifications = models.BooleanField(
        default=True,
        verbose_name="Search Specifications Field",
        help_text="Include specifications field in item searches",
    )

    class Meta:
        permissions = (
            ("in_artist_pulldown", "In Artist Pulldown"),
            ("salesperson", "Salesperson/Analyst/CSR"),
            ("foodservice_access", "Foodservice Access"),
            ("beverage_access", "Beverage Access"),
            ("container_access", "Container Access"),
            ("carton_access", "Carton Access"),
            ("graphic_specialist", "Graphic Specialist"),
            ("pcss", "PCSS"),
            ("shelbyville_platemaking", "Shelbyville Platemaking"),
            ("kenton_platemaking", "Kenton Platemaking"),
            ("shelbyville_art_approval", "Shelbyville Art Approval"),
            ("kenton_art_approval", "Kenton Art Approval"),
            ("visalia_art_approval", "Visalia Art Approval"),
            ("pittston_art_approval", "Pittston Art Approval"),
            ("clarksville_art_approval", "Clarksville Art Approval"),
            ("clemson_employee", "Clemson Employee"),
            ("demand_planning", "Demand Planning"),
            ("is_fsb_csr", "Is FSB CSR"),
            ("is_carton_csr", "Is Carton CSR"),
            ("shelbyville_scheduling", "Shelbyville Scheduling"),
            ("kenton_scheduling", "Kenton Scheduling"),
            ("clemson_manager", "Clemson Manager"),
            ("clemson_supervisor", "Clemson Supervisor"),
            ("olmsted_falls_notification", "Olmsted Notification"),
            ("foodservice_marketing", "Foodservice Marketing"),
            ("accounting_access", "Accounting/Billing Access"),
            ("job_entry", "Job Entry"),
            ("job_general_edit", "Edit General Job Info"),
            ("rename_item_folders", "Rename Item Folders"),
        )

    def __str__(self):
        return self.user.username

    def number_qcs(self):
        QCResponseDoc = ContentType.objects.get(app_label="qc", model="qcresponsedoc").model_class()
        year_num = date.today().year
        num_qcs = QCResponseDoc.objects.filter(reviewer=self.user, parent=None, review_date__year=year_num)

        # get all qc items from a responseDOC and add them up
        total_num_qcs = 0
        for qc in num_qcs:
            total_num_qcs = total_num_qcs + qc.items.count()

        return total_num_qcs

    def number_qc_reviews(self):
        QCResponseDoc = ContentType.objects.get(app_label="qc", model="qcresponsedoc").model_class()
        year_num = date.today().year
        num_qc_reviews = QCResponseDoc.objects.filter(reviewer=self.user, parent__isnull=False, review_date__year=year_num)

        # get all qc review items from a responseDOC and add them up
        total_num_qcs_reviews = 0
        for reviews in num_qc_reviews:
            total_num_qcs_reviews = total_num_qcs_reviews + reviews.items.count()

        return total_num_qcs_reviews

    def vacation_used(self):
        """Returns the number of vacation days used for a given year."""
        Event = ContentType.objects.get(app_label="calendar", model="event").model_class()

        year_num = date.today().year

        # Query number of days used this year.
        vacation_used_full = Event.objects.filter(employee__username=self.user.username, type="VA", event_date__year=year_num).count()
        vacation_used_half = Event.objects.filter(employee__username=self.user.username, type="HV", event_date__year=year_num).count()
        vacation_used = vacation_used_full + (vacation_used_half / 2.0)

        return vacation_used

    def sick_days_taken(self):
        """Returns the number of sick days used for a given year."""
        Event = ContentType.objects.get(app_label="calendar", model="event").model_class()

        year_num = date.today().year

        # Query number of days used this year.
        sick_fulldays = Event.objects.filter(employee__username=self.user.username, type="SD", event_date__year=year_num).count()
        sick_halfdays = Event.objects.filter(employee__username=self.user.username, type="SH", event_date__year=year_num).count()
        sick_days = sick_fulldays + (sick_halfdays / 2.0)

        return sick_days

    def items_assigned(self):
        """Returns number of items assigned to the artist."""
        Item = ContentType.objects.get(app_label="workflow", model="item").model_class()
        year_num = date.today().year
        num_items = Item.objects.filter(creation_date__year=year_num, job__artist=self.user).count()
        return num_items

    def amount_charged(self):
        """Returns total dollars charges (regardless of file out status) for the year."""
        Charge = ContentType.objects.get(app_label="workflow", model="charge").model_class()
        year_num = date.today().year
        preAug2015_charges = (
            Charge.objects.filter(
                item__creation_date__year=year_num,
                item__job__is_deleted=False,
                item__job__artist=self.user,
            )
            .exclude(item__job__id=99999)
            .exclude(artist=self.user)
        )
        preAug2015_charges = preAug2015_charges.exclude(description__type="Plates").aggregate(Sum("amount"))
        if preAug2015_charges["amount__sum"] is None:
            preAug2015_charges["amount__sum"] = 0

        postAug2015_charges = Charge.objects.filter(
            item__creation_date__year=year_num,
            item__job__is_deleted=False,
            artist=self.user,
        ).exclude(item__job__id=99999)
        postAug2015_charges = postAug2015_charges.exclude(description__type="Plates").aggregate(Sum("amount"))
        if postAug2015_charges["amount__sum"] is None:
            postAug2015_charges["amount__sum"] = 0

        total_charges = preAug2015_charges["amount__sum"] + postAug2015_charges["amount__sum"]
        if total_charges:
            return total_charges
        else:
            return 0

    def amount_billed(self):
        """
        Returns total dollars billed (regardless of file out status) for the
        year. This function is different than amount_charged because it keys off
        the date the charge was applied and not the item creation date.
        """
        Charge = ContentType.objects.get(app_label="workflow", model="charge").model_class()
        year_num = date.today().year
        preAug2015_charges = (
            Charge.objects.filter(
                creation_date__year=year_num,
                item__job__is_deleted=False,
                item__job__artist=self.user,
            )
            .exclude(item__job__id=99999)
            .exclude(artist=self.user)
        )
        preAug2015_charges = preAug2015_charges.exclude(description__type="Plates").aggregate(Sum("amount"))
        if preAug2015_charges["amount__sum"] is None:
            preAug2015_charges["amount__sum"] = 0

        postAug2015_charges = Charge.objects.filter(
            creation_date__year=year_num, item__job__is_deleted=False, artist=self.user
        ).exclude(item__job__id=99999)
        postAug2015_charges = postAug2015_charges.exclude(description__type="Plates").aggregate(Sum("amount"))
        if postAug2015_charges["amount__sum"] is None:
            postAug2015_charges["amount__sum"] = 0

        total_charges = preAug2015_charges["amount__sum"] + postAug2015_charges["amount__sum"]

        if total_charges:
            return total_charges
        else:
            return 0

    def errors_committed(self):
        """Return the number of errors the user has logged."""
        Error = ContentType.objects.get(app_label="error_tracking", model="error").model_class()
        year_num = date.today().year
        num_errors = Error.objects.filter(reported_date__year=year_num, item__job__artist=self.user).count()

        return num_errors

    def on_time_percentage(self):
        """
        Return percentage of items that went out on-time for the given
        artist.
        """
        Item = ContentType.objects.get(app_label="workflow", model="item").model_class()
        year_num = date.today().year

        items = Item.objects.filter(
            creation_date__year=year_num,
            job__status__in=("Active", "Complete"),
            job__artist=self.user,
            job__is_deleted=False,
        ).exclude(overdue_exempt=True)
        # Set up overdue item list.
        overdue = []

        for i in items:
            proof = i.first_proof_date()
            # If it was never proofed, it was probably a cancelled item.
            if proof:
                # Foodservice jobs need to finish beofre the due date.
                if i.job.workflow.name == "Foodservice":
                    # Proofed on or after job due date, and added before due date.
                    if proof.date() >= i.job.due_date and i.creation_date.date() < i.job.due_date:
                        overdue.append(i)
                else:
                    # Proofed after job due date, and added before due date.
                    if proof.date() > i.job.due_date and i.creation_date.date() < i.job.due_date:
                        overdue.append(i)

        # Number overdue items / items assigned.
        total_user_items = self.items_assigned()
        if total_user_items:
            return (float(total_user_items - len(overdue)) / total_user_items) * 100.0
        else:
            return 100.0

    def growl_at(self, title, description, sticky=False, pref_field=None):
        """
        Sends a Windows notification to the user via win10toast

        title: (str) Title of the notification
        description: (str) The message to be displayed below the title.
        sticky: (bool) When True, the notification will be persistent.
        pref_field: (str) The name of one of the growl_ fields on the
                          UserPref model. If it evaluates to True, send
                          the notification.
        """
        try:
            # Use the modern Windows notification system
            send_user_notification(
                user_profile=self,
                title=title,
                description=description,
                sticky=sticky,
                pref_field=pref_field,
            )
        except Exception as error:
            print("Notification Error: %s" % str(error))


def user_post_save(sender, instance, created, *args, **kwargs):
    """This creates a UserProfile when a new User object is created."""
    if created:
        # Create a matching UserProfile when a User is created.
        profile = UserProfile(user=instance)
        profile.save()


signals.post_save.connect(user_post_save, sender=User)
