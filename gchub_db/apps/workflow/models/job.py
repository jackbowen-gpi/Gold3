"""
Module gchub_db\apps\\workflow\\models\\job.py
"""

import datetime as _dt
import os
from datetime import date, timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q, signals
from django.template import loader
from django.utils import timezone
from localflavor.us.models import USStateField

from gchub_db.apps.accounts.models import UserProfile
from gchub_db.apps.auto_ftp.models import AutoFTPTiff
from gchub_db.apps.carton_billing.models import CartonSapEntry
from gchub_db.apps.joblog.app_defs import JOBLOG_TYPE_JOB_CREATED, JOBLOG_TYPE_NOTE
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.manager_tools.manager_tool_funcs import get_item_average_hours

# Normally this would be a bad idea, but these variables are uniquely named.
from gchub_db.apps.qad_data.models import QAD_PrintGroups
from gchub_db.apps.workflow import gps_connect
from gchub_db.apps.workflow.app_defs import (
    ART_REC_TYPES,
    BILL_TO_TYPES,
    BUSINESS_TYPES,
    CARTON_JOB_TYPES,
    JOB_STATUSES,
    JOB_TYPES,
    PREPRESS_SUPPLIERS,
    TODO_LIST_MODE_DEFAULT,
    TODO_LIST_MODE_ICONS,
    TODO_LIST_MODE_TYPES,
)
from gchub_db.apps.workflow.managers import JobManager
from gchub_db.apps.workflow.models.general import (
    Charge,
    ItemTracker,
    JobAddress,
    JobComplexity,
    PlatePackage,
    PrintLocation,
    Revision,
    SalesServiceRep,
)
from gchub_db.apps.workflow.models.item import Item
from gchub_db.includes import fs_api, general_funcs
from gchub_db.middleware import threadlocals

if TYPE_CHECKING:
    from .item import Item


class Job(models.Model):
    """
    The main unit of workflow, represents an individual job with associated
    items.
    """

    # Type annotations for Django reverse relationships
    if TYPE_CHECKING:
        item_set: models.Manager[Item]

    name = models.CharField(max_length=255)
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    duplicated_from = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="duplicated_from_job",
        blank=True,
        null=True,
    )
    duplication_type = models.CharField(max_length=255, blank=True)
    artist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="assigned_jobs",
    )
    salesperson = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="salesperson",
    )
    brand_name = models.CharField(max_length=255, blank=True)  # BEV only
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=25, blank=True)
    vrml_password = models.CharField(max_length=255, blank=True)
    due_date = models.DateField("Due Date", blank=True, null=True)
    real_due_date = models.DateField("Real Due Date", blank=True, null=True)
    creation_date = models.DateTimeField("Date Entered", auto_now_add=True)
    e_tools_id = models.CharField(max_length=12, blank=True)
    bill_to_type = models.CharField(max_length=50, blank=True, choices=BILL_TO_TYPES)
    sales_service_rep = models.ForeignKey(
        SalesServiceRep,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Sales Rep.",
    )
    business_type = models.CharField(max_length=50, blank=True, choices=BUSINESS_TYPES)
    prepress_supplier = models.CharField("Prepress Sup.", max_length=50, blank=True, choices=PREPRESS_SUPPLIERS)
    archive_disc = models.CharField(max_length=12, blank=True)
    last_modified = models.DateTimeField("Date Last Modified", auto_now=True)
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        editable=False,
        related_name="modified_jobs",
    )
    status = models.CharField(max_length=100, default="Pending", choices=JOB_STATUSES)
    type = models.CharField(max_length=100, choices=JOB_TYPES, blank=True)
    carton_type = models.CharField(max_length=100, choices=CARTON_JOB_TYPES, blank=True)
    comments = models.TextField(max_length=5000, blank=True)
    instructions = models.TextField(max_length=5000, blank=True)
    po_number = models.CharField(max_length=100, blank=True)
    customer_po_number = models.CharField("Customer PO#", max_length=100, blank=True)
    # The following 2 fields are used so that items in Beverage/Container
    # can inherit the settings from the job.
    temp_printlocation = models.ForeignKey(PrintLocation, on_delete=models.CASCADE, blank=True, null=True)
    temp_platepackage = models.ForeignKey(PlatePackage, on_delete=models.CASCADE, blank=True, null=True)
    # This is only used for importing. If the value is yes, charges should be
    # marked as invoiced.
    temp_invoiced = models.CharField(max_length=50, blank=True)
    art_rec_type = models.IntegerField(blank=True, null=True, choices=ART_REC_TYPES)
    ship_to_state = USStateField(blank=True, null=True)
    needs_etools_update = models.BooleanField(default=False)
    # New etools crap:
    anticipated_plant = models.CharField(max_length=255, blank=True)
    keep_upc = models.BooleanField(default=False)
    plantpress_change = models.BooleanField(default=False)
    csr = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="csr_of_job_set",
    )
    # Temp. PO number for Evergreen's Olmsted Falls plant until they get
    # setup on SAP and use the normal PO numbers...
    olmsted_po_number = models.CharField(max_length=100, blank=True, verbose_name="PO#")
    purchase_request_number = models.CharField(max_length=100, blank=True, verbose_name="EVG Purchase Request Number")
    use_new_bev_nomenclature = models.BooleanField(default=True, verbose_name="New Nomenclature")
    todo_list_mode = models.IntegerField(choices=TODO_LIST_MODE_TYPES, default=TODO_LIST_MODE_DEFAULT)
    printgroup = models.ForeignKey(QAD_PrintGroups, on_delete=models.CASCADE, blank=True, null=True)
    user_keywords = models.CharField(max_length=500, blank=True)
    generated_keywords = models.TextField(max_length=20000, blank=True)

    # These are the new Carton/Marion project attributes
    graphic_supplier = models.CharField(max_length=255, blank=True)
    customer_identifier = models.CharField(max_length=255, blank=True)
    pcss = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="pcss_of_job_set",
    )
    graphic_specialist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="graphic_specialist_of_job_set",
    )

    # Custom manager. Found in managers.py.
    objects = JobManager()

    class Meta:
        app_label = "workflow"
        verbose_name_plural = "Jobs"
        permissions = (("duplicate_job", "Can duplicate or press change jobs"),)

    def __str__(self):
        if self.workflow.name == "Beverage":
            return str(self.id) + " " + self.name + " [" + self.brand_name + "]"
        else:
            return str(self.id) + " " + self.name

    def delete(self, using=None, keep_parents=False):
        """
        Deleting Job objects causes a chain of deletions for all objects
        with Foreignkey fields pointing to Job. This results in a lot of data
        loss. Set an is_deleted flag on the Job instead and filter out all
        "deleted" Job objects as needed.
        """
        self.is_deleted = True
        self.delete_folder()
        return super(Job, self).save()

    def delete_folder(self):
        """
        Deletes the job's folder and everything in it.

        WARNING: Deletions are un-recoverable, be careful with this!
        """
        try:
            self.delete_folder_symlink()
        except Exception:
            print("! Error removing symlink.")
        try:
            fs_api.delete_job_folder(self.id)
        except Exception:
            print("! Error removing job folder.")

    def delete_carton_items_subfolders(self):
        """
        Carton items have specific supfolders that need to be deleted in certain
        cases. Usually when the job has been archived.

        WARNING: Deletions are un-recoverable, be careful with this!
        """
        if self.workflow.name == "Carton":
            items = Item.objects.filter(job=self)
            for item in items:
                fs_api.delete_item_deleteonoutput_folder(self.id, item.num_in_job)
        else:
            pass

    def lock_folder(self):
        """Locks the job's folder from modification."""
        fs_api.lock_job_folder(self.id)

    def unlock_folder(self):
        """Unlocks the job's folder."""
        fs_api.unlock_job_folder(self.id)

    def reset_folder(self):
        """
        Tell the file server to reset the permissions of everything in the job
        folder.
        """
        print("Resetting the job folder permissions for %s" % self.id)
        # Trigger the file server to reset the job folder permissions with a text file.
        try:
            # Set up the path to the hotfolder.
            hotfolder = "gold_scripts/jobfolder_permissions/"
            path_to_hotfolder = os.path.join(settings.PRODUCTION_DIR, hotfolder, str(self.id).zfill(5) + ".txt")
            # Write a text file to the hotfolder with the symlink path.
            file = open(path_to_hotfolder, "w+")
            file.write(str(self.id).zfill(5))
            file.close()
            # Create a joblog entry.
            new_log = JobLog()
            new_log.job = self
            new_log.type = JOBLOG_TYPE_NOTE
            new_log.log_text = "Job folder permissions reset. (reset7652)"
            new_log.save()
        except Exception:
            print("Could not trigger job folder permission reset.")

    def is_completed_archived(self):
        """Returns True if the job is archived and completed."""
        if self.archive_disc:
            return True
        else:
            return False

    def sales_initials(self):
        """
        Return the initials of the analyst for a Beverage job
        for display in the todo list.
        """
        try:
            if self.workflow.name == "Beverage":
                first = self.salesperson.first_name[0]
                last = self.salesperson.last_name[0]
                return first + last
            else:
                return None
        except Exception:
            return None

    def todo_list_html(self, show_manager_tools=False, fileout=False):
        """Produces HTML for the todo list entry."""
        # Re-encode the job names to replace strange characters with a '?' so
        # they'll still display on the todo list.
        if self.workflow.name == "Beverage":
            jobname = str(self.id) + " " + self.name.encode("ascii", "replace").decode("ISO-8859-1") + " [" + self.brand_name + "]"
        else:
            jobname = str(self.id) + " " + self.name.encode("ascii", "replace").decode("ISO-8859-1")
        # Begin HTML work.
        if str(jobname).endswith(" KD"):
            html = '<a href="/workflow/job/%s/" class="kd_todo">' % str(self.id)
        elif " KD - " in str(jobname):
            html = '<a href="/workflow/job/%s/" class="kd_todo">' % str(self.id)
        #       These two conditionals look for Corrugated jobs and assigns a KD CSS class
        else:
            if self.workflow.name == "Carton":
                html = '<a href="/workflow/job/%s/" class="%s_todo">' % (
                    str(self.id),
                    "carton",
                )
            else:
                html = '<a href="/workflow/job/%s/" class="%s_todo">' % (
                    str(self.id),
                    self.workflow.name.lower(),
                )
        html += '<img src="%s" width="10px" height="10px" style="vertical-align: text-center" alt="%s" /> %s </a>' % (
            self.get_icon_url(),
            str(self.workflow.id),
            jobname,
        )
        html += '(%s) - <span class="smtext">(%s)' % (self.items_in_job(), self.artist)

        # Show the extra artist averages if managers tools are turned on.
        if show_manager_tools and self.workflow.name != "Beverage":
            # Item's that are final filing get a different average.
            if fileout:
                html += " [%s avg] " % self.avg_fileout_time()
            else:
                try:
                    # Look up the job complexity
                    job_complexity = JobComplexity.objects.get(job=self)

                    # Use the get_item_average_hours() function to calculate average.
                    artist_averages = get_item_average_hours(job_complexity.category, self.type, self.artist)
                    all_artists_averages = get_item_average_hours(job_complexity.category, self.type)
                    # Count the items
                    items = Item.objects.filter(job=self)
                    # get_item_average_hours() returns averages for each complexity.
                    # Pick out the one that matches this job.
                    for entry in artist_averages:
                        if entry[0] == job_complexity.complexity:
                            artist_average = entry[1] * items.count()
                            artist_average = round(artist_average, 2)
                    for entry in all_artists_averages:
                        if entry[0] == job_complexity.complexity:
                            all_artist_average = entry[1] * items.count()
                            all_artist_average = round(all_artist_average, 2)
                    # Add the averages to the HTML.
                    if artist_average == 0:
                        artist_average = "no"
                    html += " [%s hrs/%s avg] " % (artist_average, all_artist_average)
                except Exception:
                    html += " [no data] "

        if self.sales_initials():
            html += " [%s]" % self.sales_initials()
        html += "</span> <br />"
        return html

    def avg_fileout_time(self):
        """
        Returns and average of how long it should take an artist to final file
        a job. This is just how long we estimate it takes to final file an item
        times the number of items in the job. Used in the to-do list manager
        view.
        """
        # Esitmated ff time for one item. Fractions of an hour like timesheets.
        estimated_time = 0.5

        # Only count items with nine digit numbers.
        num_of_items = Item.objects.filter(job=self, fsb_nine_digit__isnull=False).count()

        return estimated_time * num_of_items

    def do_status_update(self):
        """Checks multiple things about the job, updates status if needed."""
        if self.all_items_complete():
            self.status = "Complete"

        # Mark as needing to update to etools.
        self.needs_etools_update = True
        self.save()

    def generate_keywords(self):
        """
        Generate a text blob of possible keywords that describe this job.
        Will be used to search jobs that may be related, but not named the same.

        THIS DOES NOT SAVE. HANDLED IN SAVE SIGNAL!!
        """
        keyword_list = []
        # Build list of keywords to use in the final string.
        keyword_list.append(self.name)
        keyword_list.append(str(self.id))
        if self.printgroup:
            keyword_list.append(self.printgroup.description)
        keyword_list.append(self.customer_email)

        # Item-specific text.
        for item in self.item_set.all():
            keyword_list.append(item.disclaimer_text)
            keyword_list.append(item.description)
            keyword_list.append(item.plant_comments)
            keyword_list.append(item.demand_plan_comments)
            keyword_list.append(item.replaces)
            if item.bev_brand_code:
                keyword_list.append(item.bev_brand_code.name)
            if item.bev_center_code:
                keyword_list.append(item.bev_center_code.name)
            # Color usage for each item.
            for color in item.itemcolor_set.all():
                keyword_list.append(color.color)
            # Revision instructions.
            for rev in Revision.objects.filter(item=item):
                keyword_list.append(rev.comments)

        # Job log data -- comments.
        for log in JobLog.objects.filter(job=self, type=JOBLOG_TYPE_NOTE):
            keyword_list.append(log.log_text)

        # Job address information.
        for address in JobAddress.objects.filter(job=self):
            keyword_list.append(address.company)

        # Add keyword entry from users.
        if self.user_keywords:
            keyword_list.append(self.user_keywords)

        # Clean out the NoneType entries.
        cleaned_list = []
        for word in keyword_list:
            if word:
                cleaned_list.append(word)

        # Join the list of keywords together into one string.
        keywords = " ".join(cleaned_list).lower()
        self.generated_keywords = keywords

    def growl_at_artist(self, *args, **kwargs):
        """
        Growls at the Job's artist. Arguments are the same as
        user.profile.growl_at()
        """
        if self.artist:
            artist_profile = self.artist.profile
            if artist_profile:
                artist_profile.growl_at(*args, **kwargs)

    def all_items_complete(self):
        """Returns True if all items for the job are filed out."""
        complete = True
        for item in self.item_set.all():
            # Once an item is not filed out, mark whole thing as incomplete.
            if complete:
                if item.final_file_date():
                    complete = True
                else:
                    # If any one item is not filed out,
                    # Then the job is not complete.
                    complete = False
        return complete

    def check_sap_carton(self):
        """
        Returns true only if a carton job meets all the criteria for an SAP
        entry. If any of the criteria are failed it returns false.
        - It must be 'prepress' carton type.
        - It can't be a "Carton Proof Dupes"
        - All the items must be approved.
        """
        # Don't even bother with the rest if it's not a carton job.
        if not self.workflow.name == "Carton":
            return False

        # Check the carton type.
        if not self.carton_type == "Prepress":
            return False

        # Make sure it's not a "Carton Proof Dupes" job.
        if "carton" in self.name.lower() and "proof" in self.name.lower() and "dupe" in self.name.lower():
            return False

        # Check that all items are approved.
        if not self.all_items_approved():
            return False

        # If we made it this far then the job meets all the critera for an SAP entry.
        return True

    def do_sap_notification(self):
        """
        Email the front desk to enter the job into SAP and create a carton
        billing entry.
        """
        # Create entry.
        entry = CartonSapEntry(job=self)
        entry.save()
        # Send notification email.
        mail_subject = "Carton SAP entry: %s" % self
        mail_send_to = []
        fd_group = Group.objects.get(name="EmailGCHubFrontDesk")
        for user in fd_group.user_set.all():
            mail_send_to.append(user.email)
        ni_group = Group.objects.get(name="EmailGCHubNewItems")
        for user in ni_group.user_set.all():
            mail_send_to.append(user.email)
        mail_body = loader.get_template("emails/carton_sap.txt")
        mail_context = {"job": self}
        general_funcs.send_info_mail(mail_subject, mail_body.render(mail_context), mail_send_to)

    def all_items_approved(self):
        """Returns True if all items for the job are approved (or canceled)."""
        complete = True
        for item in self.item_set.all():
            # Once an item is not approved, mark whole thing as incomplete.
            if complete:
                # Item situation 10 is cancelled.
                if item.approval_date() or item.item_situation == 10:
                    complete = True
                else:
                    # If any one item is not approved,
                    # Then the job is not complete.
                    complete = False
        return complete

    def _get_workflow_subfolder(self, force_archive=False):
        """
        Determines which sub-folder under the workflow's main folder the job's
        symlink resides under. This is either 'Active' or 'Archive'.
        """
        if not self.is_completed_archived() and not force_archive:
            return "Active"
        else:
            """
            For archived stuff, break up the folders into thousands, and
            further sub-divide those folders into hundreds.
            """
            job_id_str = str(self.id)
            if self.id < 1000:
                # Handles early jobs, want to provide a sane default that sorts
                # correctly in finder.
                thousands_path = "0000"
            else:
                # Grab the thousands and tack zeros on to it.
                thousands_path = job_id_str[:-3] + "000"

            if self.id < 100:
                hundreds_path = "000"
            else:
                # Third character from string's right is the hundreds place.
                hundreds_path = job_id_str[-3] + "00"
            return os.path.join("Archive", thousands_path, hundreds_path)

    def get_folder(self):
        """Returns the path to the Job folder."""
        return fs_api.get_job_folder(self.id)

    def create_folder(self):
        """Creates the Job's folder in the master JobStorage directory."""
        fs_api.create_job_folder(self.id)
        self.create_folder_symlink()

    def create_creative_folder_symlink(self):
        """
        Triggers the file server to create the symbolic link that resides in the
        creative design folder of the resources folder. This is done by placing a text file in the
        appropriate hot folder on the file server. The name of the text file
        is the job number and the contents of the file will be the path to the
        new symlink.
        """
        # Check that the job folder exists first.
        static_job_folder = fs_api.get_job_folder(self.id)
        if not os.path.exists(static_job_folder):
            print("Job folder doesn't exist.")
            return None

        # Clean the jobname up to something that is valid for a symlink.
        stripped_job_name = self.name.strip()
        stripped_job_name = fs_api.strip_for_valid_filename(stripped_job_name)
        new_symlink = "%s %s" % (self.id, stripped_job_name)

        # Create the path to the new symlink.
        symlink_path = os.path.join("Resources", "Design Bank", "Creative Design Work Jobs", new_symlink)
        # Format path for Windows
        symlink_path = symlink_path.replace("/", "\\")

        # Trigger the file server to make the symlink with a text file.
        try:
            # Set up the path to the symlink hotfolder.
            symlink_hotfolder = "gold_scripts/jpoints/"
            path_to_hotfolder = os.path.join(
                settings.PRODUCTION_DIR,
                symlink_hotfolder,
                str(self.id).zfill(5) + ".txt",
            )
            # Write a text file to the hotfolder with the symlink path.
            file = open(path_to_hotfolder, "w+")
            file.write(symlink_path)
            file.close()
            # Create a joblog entry. If we ever need to re-create these
            # symlinks just look for jobs with this joblog entry. The code
            # at the end is just there to make it distinct.
            new_log = JobLog()
            new_log.job = self
            new_log.type = JOBLOG_TYPE_NOTE
            new_log.log_text = "Creative shortcut has been created (creative8543)."
            new_log.save()
        except Exception:
            print("Could not trigger symlink.")
        return symlink_path

    def create_folder_symlink(self, force_archive=False):
        """
        Triggers the file server to create the symbolic link that resides in the
        user-visible shares. This is done by placing a text file in the
        appropriate hot folder on the file server. The name of the text file
        is the job number and the contents of the file will be the path to the
        new symlink.
        """
        # Check that the job folder exists first.
        static_job_folder = fs_api.get_job_folder(self.id)
        if not os.path.exists(static_job_folder):
            print("Job folder doesn't exist.")
            return None

        # See if the symlink needs to go in Active or Archive.
        workflow_subfolder = self._get_workflow_subfolder(force_archive=force_archive)

        # If archived, create the archive subfolders if they don't exist yet.
        if self.is_completed_archived():
            try:
                workflow_folder = fs_api.WORKFLOW_PATHS[self.workflow.name]
                os.makedirs(os.path.join(workflow_folder, workflow_subfolder))
            except OSError:
                # The directory already exists, ignore.
                pass

        # Clean the jobname up to something that is valid for a symlink.
        stripped_job_name = self.name.strip()
        stripped_job_name = fs_api.strip_for_valid_filename(stripped_job_name)
        new_symlink = "%s %s" % (self.id, stripped_job_name)

        # Create the path to the new symlink.
        symlink_path = os.path.join(self.workflow.name, workflow_subfolder, new_symlink)
        # Format path for Windows
        symlink_path = symlink_path.replace("/", "\\")

        # Trigger the file server to make the symlink with a text file.
        try:
            # Set up the path to the symlink hotfolder.
            symlink_hotfolder = "gold_scripts/jpoints/"
            path_to_hotfolder = os.path.join(
                settings.PRODUCTION_DIR,
                symlink_hotfolder,
                str(self.id).zfill(5) + ".txt",
            )
            # Write a text file to the hotfolder with the symlink path.
            file = open(path_to_hotfolder, "w+")
            file.write(symlink_path)
            file.close()
        except Exception:
            print("Could not trigger symlink.")
        return symlink_path

    #     def create_folder_symlink(self, force_archive=False):
    #         """
    #         Creates the symbolic link that resides in the user-visible shares.
    #         """
    #         static_job_folder = fs_api.get_job_folder(self.id)
    #         if not os.path.exists(static_job_folder):
    #             return None
    #         workflow_folder = fs_api.WORKFLOW_PATHS[self.workflow.name]
    #         workflow_subfolder = self._get_workflow_subfolder(force_archive=force_archive)
    #         if self.is_completed_archived():
    #             try:
    #                 os.makedirs(os.path.join(workflow_folder, workflow_subfolder))
    #             except OSError:
    #                 # The directory already exists, ignore.
    #                 pass
    #
    #         # Clean the jobname up to something that is valid for a path.
    #         stripped_job_name = self.name.strip()
    #         stripped_job_name = fs_api.strip_for_valid_filename(stripped_job_name)
    #         new_job_folder = "%s %s" % (self.id, stripped_job_name)
    #
    #         symlink_name = os.path.join(workflow_folder,
    #                                     workflow_subfolder,
    #                                     new_job_folder)
    #         try:
    #             os.symlink(static_job_folder, symlink_name)
    #         except OSError, inst:
    #             if inst.errno == 17:
    #                 # Symlink already exists, fail silently.
    #                 pass
    #         return symlink_name

    def delete_folder_symlink(self):
        """
        Deletes the junction point that resides in Active/Archive. I know the
        function says symlink but it's actually a junction point. They used to
        be symlinks long ago.
        """
        # Find the junction point.
        workflow_folder = fs_api.WORKFLOW_PATHS[self.workflow.name]
        workflow_subfolder = self._get_workflow_subfolder()
        search_path = os.path.join(workflow_folder, workflow_subfolder)
        jpoint_path = fs_api.find_job_folder(search_path, self.id)

        # Format path for Windows
        jpoint_path = jpoint_path.replace(settings.WORKFLOW_ROOT_DIR, "")
        jpoint_path = jpoint_path.replace("/", "\\")

        # Trigger the file server to remove the jpoint with a text file.
        try:
            # Set up the path to the remove jpoint hotfolder.
            jpoint_hotfolder = "gold_scripts/remove_jpoints/"
            path_to_hotfolder = os.path.join(
                settings.PRODUCTION_DIR,
                jpoint_hotfolder,
                str(self.id).zfill(5) + ".txt",
            )
            # Write a text file to the hotfolder with the jpoint path.
            file = open(path_to_hotfolder, "w+")
            file.write(jpoint_path)
            file.close()
        except Exception:
            print("Could not trigger remove jpoint.")
        return jpoint_path

    def recalc_item_numbers(self):
        """
        After an item is deleted, all Items in the job may need to have their
        num_in_job updated.
        """
        items = self.get_item_qset().order_by("id")

        inum_counter = 1
        for item in items:
            item.num_in_job = inum_counter
            item.save()
            inum_counter += 1

    def replaces_etools_design(self):
        """
        Checks the eTools database to see if this job replaced a previous
        design. If so it returns true.
        """
        from gchub_db.apps.workflow import etools

        # Check to see if the job was duplicated to make sure we get the original.
        if self.duplicated_from:
            etools_id = self.duplicated_from.e_tools_id
        else:
            etools_id = self.e_tools_id
        if etools_id:
            cursor = etools.get_job_by_request_id(etools_id)
            ejob = cursor.fetchone()
            edict = {}
            for column in cursor.description:
                key_name = column[0]
                edict[key_name] = getattr(ejob, key_name, None)

            if edict["replaces_previous_design"] or edict["replaces_previous_design_name"]:
                return True
            else:
                return False
        else:
            return False

    def calculate_real_due_date(self):
        # Give a real due date based on the workflow and the day of the
        # week that the job was requested.
        assigned_date = self.due_date
        try:
            day_of_week = assigned_date.isoweekday()
            real_date = assigned_date
            if self.workflow.name == "Foodservice":
                # If Friday, due Thursday
                if day_of_week == 5:
                    real_date = assigned_date + timedelta(days=-1)
                # If Saturday, due Thursday
                if day_of_week == 6:
                    real_date = assigned_date + timedelta(days=-2)
                # If Sunday, due Thursday
                if day_of_week == 7:
                    real_date = assigned_date + timedelta(days=-3)
                # IF Monday, due Friday
                if day_of_week == 1:
                    real_date = assigned_date + timedelta(days=-3)
                # IF date hasn't changed... you'll need to send out the Fedex the day before
                if real_date == assigned_date:
                    real_date = assigned_date + timedelta(days=-1)
            else:
                # If Saturday, due Friday
                if day_of_week == 6:
                    real_date = assigned_date + timedelta(days=-1)
                # If Sunday, due Friday
                if day_of_week == 7:
                    real_date = assigned_date + timedelta(days=-2)
            self.real_due_date = real_date
        except Exception:
            pass

    def filter_user_association(self, qset, usertype):
        """Takes queryset, filters based on job workflow assignment, returns new queryset."""
        if self.workflow.name == "Foodservice":
            permission = Permission.objects.get(codename="foodservice_access")
        if self.workflow.name == "Beverage":
            permission = Permission.objects.get(codename="beverage_access")
        if self.workflow.name == "Container":
            permission = Permission.objects.get(codename="container_access")
        if self.workflow.name == "Carton":
            permission = Permission.objects.get(codename="carton_access")
        if usertype == "Artist" and self.artist:
            qset = qset.filter(
                Q(groups__in=permission.group_set.all()),
                Q(is_active=True) | Q(id=self.artist.id),
            )
        elif usertype == "Salesperson" and self.salesperson:
            qset = qset.filter(
                Q(groups__in=permission.group_set.all()),
                Q(is_active=True) | Q(id=self.salesperson.id),
            )
        else:
            qset = qset.filter(Q(groups__in=permission.group_set.all()), Q(is_active=True))
        return qset

    def get_icon_url(self):
        """
        Returns the appropriate icon for the workflow type.
        This will predominately be used on the ToDo list page.
        """
        retval = "page_black.png"
        if self.workflow.name == "Foodservice":
            retval = "bullet_red.png"
        elif self.workflow.name == "Beverage":
            retval = "bullet_green.png"
        elif self.workflow.name == "Container":
            retval = "bullet_purple.png"
        elif self.workflow.name == "Carton":
            retval = "bullet_purple.png"
        return "%simg/icons/%s" % (settings.MEDIA_URL, retval)

    def get_todo_list_mode_icon_url(self):
        """Returns the URL for the icon for the job's todo_list_mode value."""
        return "%simg/icons/%s" % (
            settings.MEDIA_URL,
            TODO_LIST_MODE_ICONS[self.todo_list_mode],
        )

    def do_artist_assignment_email(self):
        """Send out an email to the salesperson letting them know who the artist is."""
        try:
            mail_subject = "GOLD Artist Assignment: %s" % self
            mail_send_to = []
            if self.salesperson:
                mail_send_to.append(self.salesperson.email)

            mail_body = loader.get_template("emails/on_do_artist_assignment.txt")
            mail_context = {"job": self}
            general_funcs.send_info_mail(mail_subject, mail_body.render(mail_context), mail_send_to)
        except Exception:
            # Fail if no email reciepients.
            pass

    def do_create_joblog_entry(self, logtype, logtext, date_override=None, user_override=None, is_editable=True):
        """Abstraction for creating joblog entries for jobs."""
        new_log = JobLog()
        # Reference to the job.
        new_log.job = self
        # Allow overriding of who shows up as the joblog originator.
        if user_override:
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
        new_log.is_editable = is_editable
        new_log.save()

        # Allow overriding of the log date.
        if date_override:
            # Convert date objects to datetimes at midnight, then ensure timezone-aware.
            if isinstance(date_override, date) and not isinstance(date_override, _dt.datetime):
                # Create a datetime at midnight for the given date and make it timezone-aware
                date_override = timezone.make_aware(
                    _dt.datetime.combine(date_override, _dt.time.min),
                    timezone.get_current_timezone(),
                )
            elif timezone.is_naive(date_override):
                # If a datetime was provided but is naive, make it timezone-aware
                date_override = timezone.make_aware(date_override, timezone.get_current_timezone())
            new_log.event_time = date_override
            # Have to save again because of the auto_now_add on event_time.
            new_log.save()

        return new_log

    def can_be_duplicated(self):
        """Return True if job is part of a workflow where jobs can be duplicated."""
        if self.workflow.name in [
            "Foodservice",
            "Beverage",
            "Carton",
        ]:
            return True
        else:
            return False

    def overdue(self):
        overdue = False
        # If the due_date field is None, assume it's not overdue to avoid
        # an un-caught exception for comparison against NoneTypes.
        if self.due_date is None:
            return overdue
        check_due = 0
        today = date.today()
        if self.real_due_date < today:
            for item in self.item_set.all():
                if check_due == 0:
                    if item.first_proof_date() or item.overdue_exempt:
                        overdue = False
                    else:
                        overdue = True
                        check_due = 1
        return overdue

    def workflow_status(self):
        # Returns status of job for artist purposes
        # Priority: Overdue, Revisions, Todo, Final File, Proofed, Complete
        today = date.today()
        status = ""
        items_in_job = self.get_item_qset()

        # Check for proof status.
        check_due = 0
        for item in items_in_job:
            if check_due == 0:
                if item.first_proof_date() or item.overdue_exempt:
                    status = "Proofs Out"
                else:
                    try:
                        if self.real_due_date < today:
                            # Return immediately. Highest priority.
                            return "Overdue"
                        else:
                            status = "To-Do"
                            check_due = 1
                    except Exception:
                        pass

        # Go ahead and return ToDo status.
        if status == "To-Do":
            return status

        # Check for final file status.
        check_due2 = 0
        for item in items_in_job:
            if self.workflow.name != "Foodservice":
                if self.workflow.name == "Carton":
                    # Carton jobs have similar logic to FSB jobs, minus the fsb_nine_digit_number.
                    if check_due2 == 0:
                        if item.approval_date():
                            if item.final_file_date():
                                status = "Complete"
                                check_due2 = 0
                            else:
                                status = "Final File"
                                check_due2 = 1
                else:
                    if check_due2 == 0:
                        if item.final_file_date():
                            status = "Complete"
                            check_due2 = 0
                        else:
                            pass
            elif item.fsb_nine_digit:
                if check_due2 == 0:
                    if item.approval_date():
                        if item.final_file_date():
                            status = "Complete"
                            check_due2 = 0
                        else:
                            status = "Final File"
                            check_due2 = 1

        # Check revisions last, they should override anything else (except overdue).
        if (
            Revision.objects.filter(
                item__job__id=self.id,
                item__is_deleted=False,
                complete_date__isnull=True,
            ).count()
            > 0
        ):
            status = "Revisions"
        return status

    def revision_earliest_due_date(self):
        """Return the date of the revision due earliest."""
        try:
            return Revision.objects.filter(item__job__id=self.id, complete_date__isnull=True).order_by("due_date")[0].due_date
        except Exception:
            return None

    def old_workflow_status(self):
        # Returns status of job for artist purposes (Todo, overdue, revisions needed, final file needed)
        # Check for overdueness
        # TODO: Let's store this for easier searching. Script runs at midnight and on item save?
        today = date.today()
        status = ""
        items_in_job = self.get_item_qset()

        # Check for proof status.
        check_due = 0
        for item in items_in_job:
            if check_due == 0:
                if item.first_proof_date():
                    status = "Proofs Out"
                else:
                    try:
                        if self.due_date <= today:
                            status = "Overdue"
                            check_due = 1
                        else:
                            status = "To-Do"
                            check_due = 1
                    except Exception:
                        pass

        # Check for final file status.
        check_due2 = 0
        for item in items_in_job:
            if self.workflow.name != "Foodservice":
                if check_due2 == 0:
                    if item.final_file_date():
                        status = "Complete"
                        check_due2 = 0
                    else:
                        pass
            elif item.fsb_nine_digit:
                if check_due2 == 0:
                    if item.approval_date():
                        if item.final_file_date():
                            status = "Complete"
                            check_due2 = 0
                        else:
                            status = "Final File"
                            check_due2 = 1

        # Check revisions last, they should override anything else.
        if Revision.objects.filter(item__job__id=self.id, complete_date__isnull=True).count() > 0:
            status = "Revisions"

        return status

    def bev_job_lock(self):
        """
        Lock entire job if all items have been locked.
        Will be used to prevent new items from being entered (multiple POs).
        """
        if self.workflow.name == "Beverage" and self.item_set.all():
            lock = True
            for item in self.item_set.all():
                # Once set to False, cannot become True again.
                # All items must be locked to lock entire job.
                if lock:
                    if item.bev_item_lock():
                        lock = True
                    else:
                        lock = False
            return lock
        else:
            return False

    def final_file_due_date(self):
        """
        Foodservice Only. Look at all items in the job, return the date of the
        one due soonest.
        """
        dates = []
        for item in self.get_item_qset():
            if item.final_file_due_date():
                dates.append(item.final_file_due_date())

        if dates:
            return min(dates)
        else:
            return None

    def latest_final_file_date(self):
        """Determine date of last file out."""
        dates = []
        for item in self.get_item_qset():
            if item.final_file_date():
                dates.append(item.final_file_date())
        return max(dates)

    def latest_approval_date(self):
        """Determine date of last item approved."""
        dates = []
        for item in self.get_item_qset():
            if item.approval_date():
                dates.append(item.approval_date())
        return max(dates)

    def latest_approval_no_ninedigit_date(self):
        """Determine date of last item approved."""
        dates = []
        for item in self.get_item_qset():
            # Only include dates without nine digit.
            if item.approval_date() and not item.fsb_nine_digit:
                dates.append(item.approval_date())
        if dates:
            return max(dates)
        else:
            return None

    def items_in_job(self):
        """Returns the number of items in the job."""
        return self.get_item_qset().count()

    def get_item_qset(self, include_deleted=False):
        """Returns a QuerySet with the Job's active items in it."""
        base = self.item_set.all()
        if not include_deleted:
            base = base.filter(is_deleted=False)
        return base

    def job_billing_charges(self):
        """Get billing summary information for job."""
        jobtotal = 0
        for item in self.item_set.all():
            jobtotal = jobtotal + item.get_total_charges()

        return jobtotal

    def job_billable_charges_exist(self):
        """
        Return True if any of the charges associated with this job
        have not been invoiced.
        """
        billable_charges = Charge.objects.filter(item__job=self, bev_invoice__isnull=True, item__is_deleted=False)
        if billable_charges:
            return True
        else:
            return False

    def save(self, *args, **kwargs):
        """
        Overriding the Job's standard save() so we can do some tracking for the
        JobLog.
        """
        current_user = threadlocals.get_current_user()
        if current_user and current_user.is_authenticated:
            self.last_modified_by = current_user
        self.calculate_real_due_date()
        if self.workflow.name == "Beverage":
            if self.temp_printlocation:
                self.po_number = str(self.olmsted_po_number)
                # Reformat to be the job's PO# and update the field at top of job
                # PO# shouldnt not be affected by the purchase_request_number
            # if self.purchase_request_number:
            #     self.po_number = self.purchase_request_number
            else:
                self.po_number = ""

        return super(Job, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Returns a URL to the job's display page."""
        return "/workflow/job/%i/" % self.id

    def get_item_num(self, item_num):
        """Returns the specified item out of the job's item list."""
        return self.item_set.all()[int(item_num) - 1]

    def ftp_item_tiffs_to_platemaker(self, item_num_list, platemaker):
        """
        Adds the specified items to the fusion flexo ftp queue.

        item_num_list: (list of ints) Item numbers to be uploaded.

        Example:
        somejob.hughes_ftp_item_tiffs_to_platemaker([1,3,5], DESTINATION_HUGHES)

        """
        # Grab the desired item objects
        items = self.item_set.filter(num_in_job__in=item_num_list)
        # Create an ftp queue entry
        upload = AutoFTPTiff.objects.create(job=self, destination=platemaker)
        # Have to save before we can add items to the 'items' M2M field
        upload.save()
        # Add the specified items to it
        for item in items:
            upload.items.add(item)

    def get_finalized_qcs(self):
        """Returns a QuerySet of finalized parent QCResponseDoc objects."""
        return self.qcresponsedoc_set.filter(review_date__isnull=False, parent__isnull=True)

    def get_customer_name(self):
        """
        Get the name of the customer from GPS Connect using
        job.customer_identifier.
        """
        data = gps_connect._get_customer_data(self.customer_identifier)
        if data == "Can't reach GPS connect.":
            return data
        if data:
            return data["Customer_Name"][0]
        else:
            return "Name not found"

    def get_customer_data(self):
        """
        Get a dictionary of customer data from GPS Connect using
        job.customer_identifier.
        """
        data = gps_connect._get_customer_data(self.customer_identifier)
        return data

    def is_length_check(self):
        """Returns True if length of the job name is over 50 characters."""
        if len(self.name) > 50:
            return True
        else:
            return False

    def proof_status(self):
        """Returns true if all items in a job are proofed out."""
        items = Item.objects.filter(job=self.id)

        for item in items:
            # If we find one that isn't proofed return False and then stop.
            if not item.current_proof_date():
                return False
        # If we made it this far then all the items had proofs. Return true.
        return True

    def has_promo_items(self):
        """
        This functions checks to see specific ItemTrackers (Promos) that are related to this job and if there
        are some, displays a warning for the artists so that extra QC measure can be done.
        """
        message = None
        trackerTypes = ["Ink Jet Code", "Labels"]
        items = Item.objects.filter(job_id=self.id)
        trackers = ItemTracker.objects.filter(removed_by=None, item__in=items, type__name__in=trackerTypes).order_by("item__num_in_job")
        if trackers:
            # counter keeps track of the , we need
            counter = 0
            # obj keeps track of duplicate items in the message
            obj = {}
            message = "Ink Jet and/or Label Promotions on item(s): "
            for tracker in trackers:
                try:
                    # if the item exists, we do nothing
                    obj[str(tracker.item.id)]
                except Exception:
                    # if item does not exist we add it to the check object and also the promo message
                    obj[str(tracker.item.id)] = 0
                    if counter > 0:
                        message += ", "
                    message += str(tracker.item.num_in_job)
                counter += 1

        return message

    def has_bottom_print(self):
        """
        Checks if the job has KFC items which require bottom print and adds
        a warning to the job info if so.
        """
        message = None
        # These are the sizes that get bottom pprints.
        bp_sizes = ["DFM-85", "DMM-130", "DFM-170"]

        if self.printgroup:
            if self.printgroup.name == "KFC" and self.printgroup.description == "KFC":
                items = Item.objects.filter(job=self, size__size__in=bp_sizes)
                if items:
                    message = "Add bottom print to spec sheet for item(s): "
                    counter = 0
                    for item in items:
                        counter += 1
                        message += str(item.num_in_job)
                        if counter < len(items):
                            message += ", "

        return message


"""
--- Job Signals
"""


def job_pre_save(sender, instance, *args, **kwargs):
    """Things do to before a Job object is saved."""
    # If this is a new instance (no PK yet), related lookups like
    # instance.item_set will raise ValueError. Skip keyword generation
    # on initial save; it will run on subsequent saves.
    if instance.pk is None:
        return
    instance.generate_keywords()


def job_post_save(sender, instance, created, *args, **kwargs):
    """Things to do after a Job object is saved."""
    new_log = JobLog()
    # Instance is a copy of the Job object being saved.
    new_log.job = instance
    # Get the user who is doing the saving.
    log_user = threadlocals.get_current_user()
    if not log_user:
        # Prevent the is_authenticated from happening on a None.
        pass
    elif not log_user.is_authenticated:
        # This should catch AnonymousUser objects
        pass
    else:
        new_log.user = log_user

    # If there are no existing log entries for the job, it must be new.
    existing_logs = JobLog.objects.filter(job=instance).count()
    if existing_logs == 0:
        new_log.type = JOBLOG_TYPE_JOB_CREATED
        new_log.log_text = "Job has been created."
        new_log.save()
        # determine which users to notify; be defensive if workflow/name not present
        growled_users = []
        try:
            wname = getattr(instance, "workflow", None) and getattr(instance.workflow, "name", None)
            if wname == "Beverage":
                growled_users = UserProfile.objects.filter(growl_hear_new_beverage_jobs=True)
            elif wname == "Foodservice":
                growled_users = UserProfile.objects.filter(growl_hear_new_foodservice_jobs=True)
            elif wname == "Carton":
                growled_users = UserProfile.objects.filter(growl_hear_new_carton_jobs=True)
        except Exception:
            growled_users = []

        for user in growled_users:
            try:
                user.growl_at(
                    "New %s Job" % (getattr(instance.workflow, "name", "Job"),),
                    "A new job, %s %s, has been entered." % (getattr(instance, "id", "?"), getattr(instance, "name", "?")),
                )
            except Exception:
                # ensure notification failures don't break saves
                continue


def job_pre_delete(sender, instance, *args, **kwargs):
    """Clean up misc. stuff before a job is deleted."""
    fs_api.delete_job_folder(instance.id)


"""
--- Dispatchers
"""
signals.pre_save.connect(job_pre_save, sender=Job)
signals.post_save.connect(job_post_save, sender=Job)
signals.pre_delete.connect(job_pre_delete, sender=Job)
"""
--- End Job Signals
"""
