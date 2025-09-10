"""Job Views"""

import json
import os
from abc import abstractstaticmethod
from datetime import date, datetime, timedelta
from gchub_db.includes import general_funcs
from django.utils import timezone
from io import BytesIO

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission, User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.models import Site
from django.core import serializers
from django.db.models import Q
from django.forms import ModelChoiceField, ModelForm, ModelMultipleChoiceField
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.urls import reverse
from django.views.generic.list import ListView
from gchub_db.apps.art_req.models import AdditionalInfo, ArtReq
from gchub_db.apps.color_mgt.models import ColorDefinition
from gchub_db.apps.joblog.app_defs import (
    JOBLOG_TYPE_CRITICAL,
    JOBLOG_TYPE_JOB_CREATED,
    JOBLOG_TYPE_NOTE,
)
from gchub_db.apps.timesheet.models import TimeSheet
from gchub_db.apps.workflow.carton_invoice_maker import generate_carton_invoice
from gchub_db.apps.workflow.models import (
    BeverageBrandCode,
    BeverageCenterCode,
    BeverageLiquidContents,
    CartonProfile,
    CartonWorkflow,
    Charge,
    ChargeType,
    InkSet,
    Item,
    ItemCatalog,
    ItemColor,
    ItemReview,
    ItemTracker,
    ItemTrackerType,
    Job,
    JobAddress,
    JobComplexity,
    LineScreen,
    PlatePackage,
    PrintCondition,
    PrintLocation,
    ProofTracker,
    SalesServiceRep,
    SpecialMfgConfiguration,
    Substrate,
    Trap,
)
from gchub_db.includes import fs_api
from gchub_db.includes.form_utils import JSONErrorForm
from gchub_db.includes.gold_json import JSMessage
from gchub_db.includes.widgets import GCH_SelectDateWidget
from gchub_db.middleware import threadlocals

from gchub_db.apps.workflow import app_defs, etools, gps_connect


def _safe_get_site(name):
    try:
        return Site.objects.get(name=name)
    except Exception:
        return None


# Lazy permission proxy to avoid hitting the DB at import time. Accessing
# attributes on these objects will resolve the real Permission on first use.
_PERM_CACHE = {}


class _LazyPermission:
    def __init__(self, codename):
        self._codename = codename
        self._obj = None

    def _resolve(self):
        if self._obj is None:
            try:
                self._obj = Permission.objects.get(codename=self._codename)
            except Exception:
                self._obj = None
        return self._obj

    def __getattr__(self, name):
        obj = self._resolve()
        if obj is None:
            raise AttributeError(f"Permission '{self._codename}' not available")
        return getattr(obj, name)

    def __bool__(self):
        return bool(self._resolve())


# These are lazy proxies; they won't access the DB until used at runtime.
ARTIST_PERMISSION = _LazyPermission("in_artist_pulldown")
SALES_PERMISSION = _LazyPermission("salesperson")
CSR_PERMISSION = _LazyPermission("is_fsb_csr")
FOODSERVICE_PERMISSION = _LazyPermission("foodservice_access")
BEVERAGE_PERMISSION = _LazyPermission("beverage_access")
CONTAINER_PERMISSION = _LazyPermission("container_access")
CARTON_PERMISSION = _LazyPermission("carton_access")
CARTON_CSR_PERMISSION = _LazyPermission("is_carton_csr")
GRAPHIC_SPECIALIST_PERMISSION = _LazyPermission("graphic_specialist")
PCSS_PERMISSION = _LazyPermission("pcss")


class JobForm(ModelForm, JSONErrorForm):
    """Main form for Job editing. Displayed in upper left corner of the job
    detail page.
    """

    # Don't populate these fields with querysets just yet, no need to
    # query here. Do it per-instance.
    artist = forms.ModelChoiceField(queryset=User.objects.none(), required=False)
    salesperson = forms.ModelChoiceField(queryset=User.objects.none(), required=False)
    purchase_request_number = forms.CharField(
        widget=forms.TextInput(attrs={"size": "25"}), required=False
    )
    customer_name = forms.CharField(
        widget=forms.TextInput(attrs={"size": "25"}), required=False
    )
    customer_email = forms.CharField(
        widget=forms.TextInput(attrs={"size": "25"}), required=False
    )
    due_date = forms.DateField(widget=GCH_SelectDateWidget)

    def __init__(self, request, *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            # Select users who are a member of the set of groups with the given permission.
            self.grouped_artist_users = User.objects.filter(
                groups__in=ARTIST_PERMISSION.group_set.all()
            ).order_by("username")
            self.grouped_sales_users = User.objects.filter(
                groups__in=SALES_PERMISSION.group_set.all()
            ).order_by("username")
            self.grouped_csr_users = User.objects.filter(
                groups__in=CSR_PERMISSION.group_set.all()
            ).order_by("username")
            self.grouped_pcss_users = User.objects.filter(
                groups__in=PCSS_PERMISSION.group_set.all()
            ).order_by("username")
            self.grouped_graphic_specialist_users = User.objects.filter(
                groups__in=GRAPHIC_SPECIALIST_PERMISSION.group_set.all()
            ).order_by("username")

            grouped_artist_users = self.instance.filter_user_association(
                self.grouped_artist_users, "Artist"
            )
            self.fields["artist"] = forms.ModelChoiceField(
                queryset=grouped_artist_users, required=False
            )
            grouped_sales_users = self.instance.filter_user_association(
                self.grouped_sales_users, "Salesperson"
            )
            self.fields["salesperson"] = forms.ModelChoiceField(
                queryset=grouped_sales_users.distinct(), required=False
            )
            grouped_csr_users = self.instance.filter_user_association(
                self.grouped_csr_users, "CSR"
            )
            self.fields["csr"] = forms.ModelChoiceField(
                queryset=grouped_csr_users, required=False
            )
            grouped_pcss_users = self.instance.filter_user_association(
                self.grouped_pcss_users, "PCSS"
            )
            self.fields["pcss"] = forms.ModelChoiceField(
                queryset=grouped_pcss_users, required=False
            )
            grouped_graphic_specialist_users = self.instance.filter_user_association(
                self.grouped_graphic_specialist_users, "Graphic Specialist"
            )
            self.fields["graphic_specialist"] = forms.ModelChoiceField(
                queryset=grouped_graphic_specialist_users, required=False
            )

    class Meta:
        # Inherit fields from the Job mode.
        model = Job
        fields = (
            "artist",
            "salesperson",
            "customer_name",
            "brand_name",
            "status",
            "due_date",
            "customer_phone",
            "customer_email",
            "olmsted_po_number",
            "purchase_request_number",
            "type",
            "pcss",
            "graphic_specialist",
            "carton_type",
        )


class JobComplexityForm(ModelForm, JSONErrorForm):
    """Form for adding and editing job complexities. Displayed in upper left corner
    of the job detail page in line with the JobForm.
    """

    class Meta:
        # Inherit fields from the Job mode.
        model = JobComplexity
        fields = ("category", "complexity")


class ItemForm(ModelForm, JSONErrorForm):
    """Item addition form."""

    class Meta:
        model = Item
        exclude = ("inkbook",)


class ItemFormFSB(ItemForm):
    """This form is used for entering new FSB items."""

    workflow = _safe_get_site("Foodservice")
    size = forms.ModelChoiceField(
        queryset=ItemCatalog.objects.filter(workflow=workflow, active=True).order_by(
            "size"
        )
    )


class ItemFormBEV(ItemForm):
    """This form is used for entering new beverage items."""

    SEQ_CHOICES = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
        (6, "6"),
    )

    PLATE_QTY_CHOICES = (
        (0, "0"),
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )

    workflow = _safe_get_site("Beverage")

    size = forms.ModelChoiceField(
        queryset=ItemCatalog.objects.filter(workflow=workflow, active=True).order_by(
            "size"
        ),
        required=True,
    )

    printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(plant__workflow=workflow).order_by(
            "plant__name"
        )
    )

    upc_ink_color = forms.ChoiceField(
        choices=[
            ("Plate 1", "Plate 1"),
            ("Plate 2", "Plate 2"),
            ("Plate 3", "Plate 3"),
            ("Plate 4", "Plate 4"),
            ("Plate 5", "Plate 5"),
        ]
    )
    special_mfg = forms.ModelChoiceField(
        queryset=SpecialMfgConfiguration.objects.filter(workflow=workflow),
        required=False,
    )

    num_up = forms.ChoiceField(choices=[(1, "1"), (2, "2"), (4, "4")])
    uses_old_distortion = forms.BooleanField(required=False)

    # Begin color form fields.
    seq1 = forms.ChoiceField(choices=SEQ_CHOICES)
    seq2 = forms.ChoiceField(choices=SEQ_CHOICES, initial=2)
    seq3 = forms.ChoiceField(choices=SEQ_CHOICES, initial=3)
    seq4 = forms.ChoiceField(choices=SEQ_CHOICES, initial=4)
    seq5 = forms.ChoiceField(choices=SEQ_CHOICES, initial=5)
    seq6 = forms.ChoiceField(choices=SEQ_CHOICES, initial=6)

    COLORDEF_QUERYSET = ColorDefinition.objects.filter(coating="C").order_by("name")
    color1 = forms.ModelChoiceField(queryset=COLORDEF_QUERYSET)
    color2 = forms.ModelChoiceField(queryset=COLORDEF_QUERYSET, required=False)
    color3 = forms.ModelChoiceField(queryset=COLORDEF_QUERYSET, required=False)
    color4 = forms.ModelChoiceField(queryset=COLORDEF_QUERYSET, required=False)
    color5 = forms.ModelChoiceField(queryset=COLORDEF_QUERYSET, required=False)
    color6 = forms.ModelChoiceField(queryset=COLORDEF_QUERYSET, required=False)

    PLATECODE_WIDGET = forms.TextInput(attrs={"size": "20"})
    plate1 = forms.CharField(widget=PLATECODE_WIDGET, required=False)
    plate2 = forms.CharField(widget=PLATECODE_WIDGET, required=False)
    plate3 = forms.CharField(widget=PLATECODE_WIDGET, required=False)
    plate4 = forms.CharField(widget=PLATECODE_WIDGET, required=False)
    plate5 = forms.CharField(widget=PLATECODE_WIDGET, required=False)
    plate6 = forms.CharField(widget=PLATECODE_WIDGET, required=False)

    num_plates1 = forms.ChoiceField(choices=PLATE_QTY_CHOICES, initial=1)
    num_plates2 = forms.ChoiceField(choices=PLATE_QTY_CHOICES, initial=1)
    num_plates3 = forms.ChoiceField(choices=PLATE_QTY_CHOICES, initial=1)
    num_plates4 = forms.ChoiceField(choices=PLATE_QTY_CHOICES, initial=1)
    num_plates5 = forms.ChoiceField(choices=PLATE_QTY_CHOICES, initial=1)
    num_plates6 = forms.ChoiceField(choices=PLATE_QTY_CHOICES, initial=1)

    screened1 = forms.BooleanField(required=False)
    screened2 = forms.BooleanField(required=False)
    screened3 = forms.BooleanField(required=False)
    screened4 = forms.BooleanField(required=False)
    screened5 = forms.BooleanField(required=False)
    screened6 = forms.BooleanField(required=False)

    # Begin billing fields.
    charge_types = ChargeType.objects.filter(workflow=workflow, active=True).order_by(
        "type"
    )
    type = forms.ModelChoiceField(queryset=charge_types, required=True)

    # Item tracker fields.
    label_tracker = forms.ModelChoiceField(
        ItemTrackerType.objects.filter(category__name="Beverage Label"), required=False
    )
    fiber_tracker = forms.ModelChoiceField(
        ItemTrackerType.objects.filter(category__name="Beverage Fiber"), required=False
    )
    nutrition_facts = forms.BooleanField(required=False)

    def __init__(self, request, job, *args, **kwargs):
        """Here we populate some of the fields based on certain conditions.
        Also, update some of the choice field querysets.
        """
        super(ItemFormBEV, self).__init__(*args, **kwargs)
        if job.temp_printlocation and (
            job.temp_printlocation.plant.name in ("Plant City")
            or job.temp_printlocation.press.name in ("BHS")
        ):
            self.fields["bev_alt_code"] = forms.CharField(
                widget=forms.TextInput(attrs={"size": "20"}), required=True
            )
        else:
            if job.use_new_bev_nomenclature:
                # New nomenclature would pull from a different list of
                # customer codes.
                self.fields["bev_brand_code"] = forms.ModelChoiceField(
                    queryset=BeverageBrandCode.objects.all().order_by("code"),
                    required=True,
                )
                self.fields["bev_end_code"] = forms.CharField(
                    widget=forms.TextInput(attrs={"size": "20"}), required=True
                )
            else:
                # Old nomenclature.
                self.fields["bev_center_code"] = forms.ModelChoiceField(
                    queryset=BeverageCenterCode.objects.all().order_by("code"),
                    required=True,
                )
                self.fields["bev_liquid_code"] = forms.ModelChoiceField(
                    queryset=BeverageLiquidContents.objects.all().order_by("code"),
                    required=True,
                )
            # This will be used for panel prefix codes.
            self.fields["bev_alt_code"] = forms.CharField(
                widget=forms.TextInput(attrs={"size": "20"}), required=False
            )

        # Plate quantities should default to 2 under these conditions.
        if job.temp_printlocation and job.temp_platepackage:
            if job.temp_printlocation.plant.name in (
                "Kalamazoo"
            ) and job.temp_platepackage.platemaker.name in ("Shelbyville"):
                self.fields["num_plates1"].initial = 2
                self.fields["num_plates2"].initial = 2
                self.fields["num_plates3"].initial = 2
                self.fields["num_plates4"].initial = 2
                self.fields["num_plates5"].initial = 2
                self.fields["num_plates6"].initial = 2

        # If this is being copied from a previous item,
        # set the plate fields (ItemColor) with initial values.
        if self.instance.id:
            cur_colors = self.instance.itemcolor_set.all().order_by("id")

            # This counter is used to form dictionary key strings.
            color_counter = 1
            # Update the list of colordefs.
            colordef_queryset = ColorDefinition.objects.filter(coating="C").order_by(
                "name"
            )
            for color in cur_colors:
                colorfield_str = "color%d" % color_counter

                seqfield_str = "seq%d" % color_counter
                self.fields[seqfield_str].initial = color.sequence

                self.fields[colorfield_str].queryset = colordef_queryset
                if color.definition:
                    # This ItemColor is backed by a definition.
                    # Populate the color pulldown with all available colors.
                    self.fields[colorfield_str].initial = color.definition.id
                else:
                    try:
                        # Try to find the Color Def. of the prev. color in the
                        # color library. If found, set as initial value.
                        col_def = ColorDefinition.objects.get(name=color.color)
                        self.fields[colorfield_str].initial = col_def.id
                    except ColorDefinition.DoesNotExist:
                        # No default selection. Discard.
                        pass

                # Set the screened boolean based on the color's name.
                if color.color.endswith(" Screened"):
                    screenedbool_str = "screened%d" % color_counter
                    self.fields[screenedbool_str].initial = True

                # Set the platecode text box to that of the prev. color platecode.
                platefield_str = "plate%d" % color_counter
                self.fields[platefield_str].initial = color.plate_code

                # Increment the counter used for forming field dict keys.
                color_counter += 1

    def clean(self):
        """Check all of the fields for general errors such as duplicate
        sequence ids. Validation happening in this method should not be
        specific to any one field, it should involve at leaast two fields.
        """
        # Alias for convenience.
        cleaned_data = self.cleaned_data
        # This dict has keys that correspond to eaach sequence number.
        dupe_counter = {}
        for seq_num in range(1, 7):
            # Determine the name of the field to check.
            seq_fieldname_str = "seq%d" % seq_num
            # Get the sequence value for the field.
            seq_val = cleaned_data.get(seq_fieldname_str)

            # If there isn't a value for the sequence ID counter, start it at 0.
            # In any case, this is where we count how many times each
            # sequence number has been selected in the form.
            dupe_counter[seq_val] = dupe_counter.get(seq_val, 0) + 1
            # The counter is greater than 1, we have a duplicate somewhere.
            if dupe_counter[seq_val] > 1:
                msg = (
                    "There is more than one color with a sequence value of %s."
                    % seq_val
                )
                # This gets thrown back to the view for handling.
                raise forms.ValidationError(msg)

        # All is well, return the same data we started with.
        return cleaned_data


@login_required
def job_detail(request, job_id):
    """Display an individual job entry's master display."""
    # Check to see if requesting user has access to this job.
    view_workflows = general_funcs.get_user_workflow_access(request)

    try:
        job = Job.objects.get(id=job_id, workflow__name__in=view_workflows)
    except Job.DoesNotExist:
        # Sends user to search page if job is not in a workflow they may access.
        return HttpResponseRedirect(reverse("job_search"))
    # Try to grab the art request that created this job if applicable.
    try:
        artreq = ArtReq.objects.get(job_num=job_id)
    except Exception:
        artreq = False
    try:
        corr_artreq = ArtReq.objects.get(corr_job_num=job_id)
    except Exception:
        corr_artreq = False
    jobform = JobForm(request, instance=job)
    # Check for an existing job complexity and display it if found.
    try:
        jobcomplex = JobComplexity.objects.get(job=job)
        jobcomplexform = JobComplexityForm(instance=jobcomplex)
    except Exception:
        jobcomplexform = JobComplexityForm()
    itemsinjob = job.item_set.order_by("num_in_job")
    ship_to_count = job.jobaddress_set.count()
    database_docs = fs_api.list_job_database_docs(job_id)

    # Check to see if due date has passed, and if any items have not been sent out.
    overdue = job.overdue()

    pagevars = {
        "page_title": "%d %s Job Details" % (job.id, job.name),
        "job": job,
        "jobform": jobform,
        "jobcomplexform": jobcomplexform,
        "itemsinjob": itemsinjob,
        "view": "timeline",
        "overdue": overdue,
        "ship_to_count": ship_to_count,
        "database_docs": database_docs,
        "artreq": artreq,
        "corr_artreq": corr_artreq,
    }

    return render(request, "workflow/job/job_detail/job_detail.html", context=pagevars)


def get_database_document(request, job_num, filepath):
    """Retrieve single file."""
    job = Job.objects.get(id=job_num)
    file = fs_api.get_job_database_doc(job.id, filepath)
    with open(file, "rb") as f:
        data = f.read()

    response = HttpResponse(data, content_type=fs_api.get_mimetype(filepath))
    response["Content-Disposition"] = 'attachment; filename="' + str(filepath) + '"'
    return response


def job_detail_main(request, job_id):
    """Main portion of job info - top left div."""
    job = Job.objects.get(id=job_id)
    jobform = JobForm(request, instance=job)
    # Check for an existing job complexity and display it if found.
    try:
        jobcomplex = JobComplexity.objects.get(job=job)
        jobcomplexform = JobComplexityForm(instance=jobcomplex)
    except Exception:
        jobcomplexform = JobComplexityForm()
    # Check to see if due date has passed, and if any items have not
    # been sent out.
    overdue = job.overdue()

    pagevars = {
        "page_title": "Job Details: %d %s" % (job.id, job.name),
        "job": job,
        "jobform": jobform,
        "jobcomplexform": jobcomplexform,
        "overdue": overdue,
    }
    return render(
        request,
        "workflow/job/job_detail/upper_left/job_info_block.html",
        context=pagevars,
    )


def create_job_creative_shortcut(request, job_id):
    job = Job.objects.get(id=job_id)
    job.create_creative_folder_symlink()
    return HttpResponseRedirect("/workflow/job/" + job_id + "/")


def sync_folders(request, job_id):
    """Rename item folders on the server - proof, final file, 1bit tiffs, to match the items
    that are listed in GOLD.
    """
    items = Item.objects.filter(job__id=job_id)
    final_message = ""
    for item in items:
        print("Syncing item: %d" % item.num_in_job)
        message = item.rename_folder()
        if message == "Error":
            final_message += "Error renaming item folder: %d, " % item.num_in_job

    if final_message == "":
        return HttpResponse(JSMessage("Folder names changed successfully"))
    else:
        return HttpResponse(JSMessage(final_message, is_error=True))


def get_zipfile_proof(request, job_id):
    """Download a zip file of all available PDF proofs."""
    job = Job.objects.get(id=job_id)
    send_name = str(job.id) + "_Proofs"
    # This contains the raw contents of the zip archive containing the tiffs.
    zip_contents = fs_api.get_zip_all_proofs(job.id, job.items_in_job())
    # Check to see if any proofs were actually returned.
    if zip_contents:
        # Set the response up to return the zip with the correct mime type.
        response = HttpResponse(zip_contents, content_type="application/zip")
        # Headers change the file name and how the browser handles the download.
        response["Content-Disposition"] = (
            'attachment; filename="' + send_name + ".zip" + '"'
        )
        return response
    else:
        return HttpResponse("No proofs found.")


def cycle_job_todo_list_mode(request, job_id):
    """Cycle the job's todo_list_mode."""
    last_type = app_defs.TODO_LIST_MODE_TYPES[-1][0]
    job = get_object_or_404(Job, id=job_id)

    if job.todo_list_mode < last_type:
        job.todo_list_mode += 1
    else:
        job.todo_list_mode = 0

    job.save()
    return HttpResponseRedirect(reverse("job_detail", args=[job.id]))


class JobFindRelated(ListView):
    """Do a quick search for all jobs related based on name."""

    paginate_by = 25
    template_name = "workflow/search/search_results.html"

    # Searching and filtering.
    def get_queryset(self):
        qset = Job.objects.all()
        job = Job.objects.get(id=self.kwargs["job_id"])
        s_job_name = job.name
        # Split search string on spaces and underscores, return results that
        # contain each word. ( q |= Q(... ) would return this word OR that word.
        split_a = s_job_name.split(" ")
        search_words = []
        # Now split all of those strings on underscore and recompile a search list.
        for word_a in split_a:
            split_b = word_a.split("_")
            for word_b in split_b:
                search_words.append(word_b)

        q = Q()
        for word in search_words:
            try:
                # Check to see if the 'word' is a number.
                # We want to not search for stuff like '2009', or '5'
                int(word)
            except Exception:
                # Word was not a number, include it in the search values.
                # Also exclude all these roman numerals. Who likes Romans, anyway?
                # Also exclude some special characters that might muck things up.
                if word not in (
                    "-",
                    "I",
                    "II",
                    "III",
                    "IV",
                    "V",
                    "VI",
                    "VII",
                    "VIII",
                    "IX",
                    "X",
                ):
                    q &= Q(name__icontains=word)
        qset = qset.filter(q)

        # Limit to jobs of same workflow, include current job.
        qset = qset.filter(workflow=job.workflow).order_by("-id")
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(JobFindRelated, self).get_context_data(**kwargs)
        context["page_title"] = "Job Search Results"
        context["type"] = "job"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


class JobFindPrintgroup(ListView):
    """Do a quick search for all jobs related based on name."""

    paginate_by = 25
    template_name = "workflow/search/search_results.html"

    # Searching and filtering.
    def get_queryset(self):
        qset = Job.objects.all()
        job = Job.objects.get(id=self.kwargs["job_id"])
        # Limit to jobs of same workflow, include current job.
        qset = qset.filter(printgroup=job.printgroup).order_by("-id")
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(JobFindPrintgroup, self).get_context_data(**kwargs)
        context["page_title"] = "Job Search Results"
        context["type"] = "job"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def job_specsheet_data(request, job_id):
    """Display all spec sheet related data for given job."""
    job = Job.objects.get(id=job_id)

    pagevars = {
        "page_title": "Job Spec Sheet Data: %d %s" % (job.id, job.name),
        "job": job,
    }
    return render(request, "workflow/job/job_specsheet_data.html", context=pagevars)


class JobFormNameChange(ModelForm, JSONErrorForm):
    """Form used for changing just the name of a job."""

    class Meta:
        model = Job
        fields = ("name",)


def change_job_name(request, job_id):
    """Change the name of a job."""
    job = Job.objects.get(id=job_id)
    old_name = job.name
    if request.POST:
        jobform = JobFormNameChange(request.POST, instance=job)
        # Capture old name for logging purposes.
        new_name = request.POST["name"]
        # Replaces foreign Unicode characters with a ?
        new_name = new_name.encode("ascii", "replace")
        # decode the byte literal from above to a string (removes the b')
        new_name = new_name.decode("utf-8")
        if jobform.is_valid():
            jobform.save()
            logchanges = (
                "<strong>Job name changed:</strong> ("
                + str(old_name)
                + " to "
                + str(new_name)
                + "). "
            )
            job.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, logchanges)
            return HttpResponse(JSMessage("Saved."))
        else:
            return jobform.serialize_errors()
    else:
        jobform = JobFormNameChange(instance=job)

        pagevars = {
            "page_title": "Change Job Name",
            "job": job,
            "jobform": jobform,
        }

        return render(
            request,
            "workflow/job/job_detail/upper_left/change_name.html",
            context=pagevars,
        )


class JobFormCSRChange(ModelForm, JSONErrorForm):
    """Form used for changing a job's CSR only."""

    csr = forms.ModelChoiceField(queryset=User.objects.none(), required=False)

    def __init__(self, request, *args, **kwargs):
        super(JobFormCSRChange, self).__init__(*args, **kwargs)
        if self.instance.id:
            # Select users who are a member of the set of groups with the given permission.
            self.grouped_csr_users = User.objects.filter(
                groups__in=CSR_PERMISSION.group_set.all()
            ).order_by("username")
            grouped_csr_users = self.instance.filter_user_association(
                self.grouped_csr_users, "CSR"
            )
            self.fields["csr"].queryset = grouped_csr_users

    class Meta:
        model = Job
        fields = ("csr",)


class JobFormCartonCSRChange(ModelForm, JSONErrorForm):
    """Form used for changing a carton job's CSR only."""

    csr = forms.ModelChoiceField(queryset=User.objects.none(), required=False)

    def __init__(self, request, *args, **kwargs):
        super(JobFormCartonCSRChange, self).__init__(*args, **kwargs)
        if self.instance.id:
            # Select users who are a member of the set of groups with the given permission.
            self.grouped_csr_users = User.objects.filter(
                groups__in=CARTON_CSR_PERMISSION.group_set.all()
            ).order_by("username")
            self.fields["csr"].queryset = self.grouped_csr_users

    class Meta:
        model = Job
        fields = ("csr",)


def change_job_csr(request, job_id):
    """Change the csr of a job."""
    job = Job.objects.get(id=job_id)
    old_name = job.csr

    if request.POST:
        # Checks to see if the CSR is set to a user or empty
        # If empty reset CSR to None
        if request.POST.get("csr", False):
            new_name = User.objects.get(id=int(request.POST["csr"])).username
        else:
            new_name = None
        if job.workflow.name == "Carton":
            jobform = JobFormCartonCSRChange(request, request.POST, instance=job)
        else:
            jobform = JobFormCSRChange(request, request.POST, instance=job)
        # Capture old name for logging purposes.

        # If no change & the save button is clicked just return to job-view page
        if str(new_name) == str(old_name):
            return HttpResponse(JSMessage("No Change."))

        if jobform.is_valid():
            jobform.save()
            logchanges = (
                "<strong>CSR changed:</strong> ("
                + str(old_name)
                + " to "
                + str(new_name)
                + "). "
            )
            job.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, logchanges)
            return HttpResponse(JSMessage("Saved."))
        else:
            return jobform.serialize_errors()
    else:
        if job.workflow.name == "Carton":
            jobform = JobFormCartonCSRChange(request, instance=job)
        else:
            jobform = JobFormCSRChange(request, instance=job)
        pagevars = {
            "page_title": "Change Job CSR",
            "job": job,
            "jobform": jobform,
        }

        return render(
            request,
            "workflow/job/job_detail/upper_left/change_csr.html",
            context=pagevars,
        )


class NewBevJobForm(ModelForm, JSONErrorForm):
    """Form used for adding a job - Beverage"""

    # Here we are checking to make sure that the due date is 5 days after today
    # to avoid a rush charge automatically, and making sure that day doesnt fall
    # on a weekend
    dueDay = general_funcs._utcnow_naive().date() + timedelta(days=5)
    day_check = dueDay.isoweekday()
    if day_check == 6:
        dueDay = dueDay + timedelta(days=2)
    if day_check == 7:
        dueDay = dueDay + timedelta(days=1)
    due_date = forms.DateField(widget=GCH_SelectDateWidget, initial=dueDay)
    # Name will be labeled as customer name.
    brand_name = forms.CharField(required=True)
    name = forms.CharField(required=True)
    workflow = _safe_get_site("Beverage")
    instructions = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "14"}), required=False
    )
    sales_service_rep = forms.ModelChoiceField(
        queryset=SalesServiceRep.objects.all().order_by("name"), required=False
    )
    prepress_supplier = forms.ChoiceField(choices=app_defs.PREPRESS_SUPPLIERS)
    # Select users who are a member of the set of groups with the given permission.
    sales_users = User.objects.filter(
        groups__in=SALES_PERMISSION.group_set.all()
    ).order_by("username")
    # group_set returns Group objects; ordering should apply to users, not groups.
    beverage_sales_users = sales_users.filter(
        groups__in=BEVERAGE_PERMISSION.group_set.all()
    ).distinct()
    salesperson = forms.ModelChoiceField(queryset=sales_users, required=False)
    temp_printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(
            plant__workflow=workflow, active=True
        ).order_by("plant__name")
    )
    # There's an old unused cyber graphics platemaker that we've been asked to
    # hide from this field.
    temp_platepackage = forms.ModelChoiceField(
        queryset=PlatePackage.objects.filter(workflow=workflow, active=True)
        .order_by("platemaker__name")
        .exclude(platemaker__id=18)
    )

    class Meta:
        model = Job
        fields = (
            "workflow",
            "status",
            "brand_name",
            "name",
            "customer_po_number",
            "due_date",
            "bill_to_type",
            "business_type",
            "salesperson",
            "sales_service_rep",
            "prepress_supplier",
            "temp_printlocation",
            "temp_platepackage",
            "olmsted_po_number",
            "purchase_request_number",
            "use_new_bev_nomenclature",
            "instructions",
        )

    def __init__(self, request, *args, **kwargs):
        super(NewBevJobForm, self).__init__(*args, **kwargs)
        # Try to set the current user as the initial value for Salesperson/Analyst.
        self.fields["salesperson"].initial = request.user.id
        # purchase_request_number may not be set as an attribute on the form
        # (bound data or instance may provide it). Use a safe lookup from
        # the instance or the initial dict to avoid AttributeError.
        self.fields["purchase_request_number"].initial = getattr(
            self.instance,
            "purchase_request_number",
            self.initial.get("purchase_request_number", ""),
        )
        # Hide some stuff from Evergreen.
        if request.user.groups.filter(name="Evergreen Analyst"):
            self.fields["temp_printlocation"].queryset = self.fields[
                "temp_printlocation"
            ].queryset.exclude(press__name="BHS")
            self.fields[
                "prepress_supplier"
            ].choices = app_defs.PREPRESS_SUPPLIERS_EVERGREEN


@login_required
def new_beverage_job(request):
    """Form and save function for creating a new Beverage job."""
    if request.POST:
        jobform = NewBevJobForm(request, request.POST)
        if jobform.is_valid():
            jobform.save()
            # Once saved, grab new job id for post-save activities.
            job_id = jobform.instance.id
            job = jobform.instance
            # Get rid of special characters like '/', causing folder creation problems.
            job.name = fs_api.strip_for_valid_filename(job.name)
            job.customer_name = job.name
            if "instructions" in request.POST:
                job.do_create_joblog_entry(
                    JOBLOG_TYPE_NOTE, request.POST["instructions"], is_editable=False
                )
            job.save()
            # Create folder after saving, must strip bad characters from job name.
            job.create_folder()
            return HttpResponse(JSMessage(job_id))
        else:
            return jobform.serialize_errors()
    else:
        jobform = NewBevJobForm(request)

        pagevars = {
            "page_title": "New Beverage Job",
            "jobform": jobform,
            "workflow": Site.objects.get(name="Beverage"),
        }

        return render(request, "workflow/job/beverage_new.html", context=pagevars)


def new_beverage_item(request, job_id, type, item_id=0):
    """Form and save function for creating a new Beverage item via the
    New Job Entry, not the job detail page.
    This will be used by analysts.
    """
    job = Job.objects.get(id=job_id)

    # Check to see if job qualifies as a rush.
    today = general_funcs._utcnow_naive().date()
    if today + timedelta(days=0) >= job.due_date:
        rush = "24 Hour"
    elif today + timedelta(days=4) > job.due_date:
        rush = "5 Day"
    else:
        rush = "No Rush"

    if request.method == "POST":
        itemform = ItemFormBEV(request, job, request.POST)
        if itemform.is_valid():
            itemform.save()
            item = Item.objects.get(id=itemform.instance.id)
            for ink_num in range(1, 7):
                if request.POST["color%s" % ink_num] != "":
                    ic = ItemColor(item=item)
                    color_id = ColorDefinition.objects.get(
                        id=request.POST["color%s" % ink_num]
                    )
                    ic.definition = color_id
                    ic.color = color_id.name
                    # Check if this is a "screened" ink
                    if itemform.cleaned_data["screened%s" % ink_num]:
                        # Add "Screened" to the color name.
                        ic.color += " Screened"
                    ic.hexvalue = color_id.hexvalue
                    ic.plate_code = request.POST["plate%s" % ink_num]
                    ic.sequence = request.POST["seq%s" % ink_num]
                    ic.num_plates = request.POST["num_plates%s" % ink_num]
                    ic.save()
            # Save the item so that the nomenclature calculates using colors.
            item.save()
            # Create folder after item colors are added, so that bev_nomenclature()
            # creates nomenclature properly.
            item.create_folder()
            # Apply rush billing charges if any.
            if rush != "No Rush":
                r_charge = Charge(item=item)
                if rush == "5 Day":
                    type = ChargeType.objects.get(type="Under 5 Day Rush")
                elif rush == "24 Hour":
                    type = ChargeType.objects.get(type="24 Hour Rush")
                r_charge.description = type
                r_charge.amount = type.base_amount
                r_charge.comments = (
                    "Charge applied during initial Beverage job request."
                )
                r_charge.save()
            # Apply required billing charge depending on type of art.
            charge = Charge(item=item)
            description = ChargeType.objects.get(id=request.POST["type"])
            charge.description = description
            # Create the item trackers starting with the label tracker.
            if request.POST["label_tracker"]:
                label_tracker = itemform.cleaned_data["label_tracker"]
                new_tracker = ItemTracker(item=item)
                new_tracker.type = ItemTrackerType.objects.get(id=label_tracker.id)
                new_tracker.addition_date = general_funcs._utcnow_naive().date()
                new_tracker.edited_by = threadlocals.get_current_user()
                new_tracker.save()
            # Now create the fiber tracker.
            if request.POST["fiber_tracker"]:
                fiber_tracker = itemform.cleaned_data["fiber_tracker"]
                new_tracker = ItemTracker(item=item)
                new_tracker.type = ItemTrackerType.objects.get(id=fiber_tracker.id)
                new_tracker.addition_date = general_funcs._utcnow_naive().date()
                new_tracker.edited_by = threadlocals.get_current_user()
                new_tracker.save()
            if request.POST.get("nutrition_facts"):
                new_tracker = ItemTracker(item=item)
                new_tracker.type = ItemTrackerType.objects.get(
                    id=31, name="Nutrition Facts"
                )
                new_tracker.addition_date = general_funcs._utcnow_naive().date()
                new_tracker.edited_by = threadlocals.get_current_user()
                new_tracker.save()
            # Count the number of colors in the item.
            num_colors = ItemColor.objects.filter(item=item).count()
            # Method to apply color adjustments, quality, rush, etc...
            charge.amount = description.actual_charge(num_colors=num_colors)
            charge.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            # Use the JSONErrorForm subclass to send any errors via JSON.
            return itemform.serialize_errors()
    else:
        if type == "new":
            itemform = ItemFormBEV(request, job)
        else:
            # The item is being duplicated from a previous item.
            # Populate with instance data.
            prev_item = Item.objects.get(id=item_id)
            # See if there are any existing item trackers for fiber or labels.
            try:
                label_tracker = prev_item.get_label_tracker().type.id
            except Exception:
                label_tracker = None
            try:
                fiber_tracker = prev_item.get_fiber_tracker().type.id
            except Exception:
                fiber_tracker = None
            try:
                nutrition_facts = prev_item.get_nutrition_facts()
            except Exception:
                nutrition_facts = False
            tracker_data = {
                "label_tracker": label_tracker,
                "fiber_tracker": fiber_tracker,
                "nutrition_facts": nutrition_facts,
            }
            # Render the form
            itemform = ItemFormBEV(
                request, job, instance=prev_item, initial=tracker_data
            )

        pagevars = {
            "page_title": "Add Item to Beverage Job",
            "job": job,
            "rush": rush,
            "itemform": itemform,
            "workflow": _safe_get_site("Beverage"),
            "type": type,
        }

        return render(request, "workflow/job/beverage_new_item.html", context=pagevars)


class ItemFormCart(ItemForm):
    """This form is used for entering new carton items."""

    size = forms.ModelChoiceField(
        queryset=ItemCatalog.objects.filter(workflow__name="Carton")
    )
    one_up_die = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=True
    )
    step_die = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=False
    )
    grn = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=False
    )
    gdd_origin = forms.ChoiceField(choices=app_defs.GDD_ORIGINS, required=False)
    customer_code = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=False
    )
    graphic_req_number = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=False
    )
    print_repeat = forms.DecimalField(max_digits=10, decimal_places=4, required=False)
    coating_pattern = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=False
    )
    proof_type = forms.ChoiceField(choices=app_defs.PROOF_TYPES, required=False)
    proof_type_notes = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeHolder": "Please explain the edits.",
                "rows": "3",
                "style": "display:none",
            }
        ),
        required=False,
    )
    upc = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=True
    )
    product_group = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=False
    )
    printlocation = forms.ModelChoiceField(
        queryset=None
    )  # queryset defined below in __init__
    location = forms.ChoiceField(choices=app_defs.LOCATION_OPTIONS)  # Inside/Outside
    plate_thickness = forms.ChoiceField(
        choices=app_defs.PLATE_THICKNESS, required=False
    )
    platepackage = forms.ModelChoiceField(
        queryset=PlatePackage.objects.filter(
            workflow=_safe_get_site("Foodservice")
        ).order_by("platemaker__name"),
        required=False,
    )
    substrate = forms.ModelChoiceField(
        queryset=Substrate.objects.filter(active=True), required=False
    )
    gcr = forms.BooleanField(required=False)
    ecg = forms.BooleanField(required=False)
    carton_workflow = forms.ModelChoiceField(
        queryset=CartonWorkflow.objects.filter(active=True), required=False
    )
    line_screen = forms.ModelChoiceField(
        queryset=LineScreen.objects.filter(active=True), required=False
    )
    ink_set = forms.ModelChoiceField(
        queryset=InkSet.objects.filter(active=True), required=False
    )
    print_condition = forms.ModelChoiceField(
        queryset=PrintCondition.objects.filter(active=True), required=False
    )
    trap = forms.ModelChoiceField(
        queryset=Trap.objects.filter(active=True), required=False
    )
    # A read-only field to show the user which carton profile has been selected.
    # The actual carton profile will be set via a hidden field.
    carton_profile_display = forms.CharField(
        widget=forms.TextInput(
            attrs={"size": "45", "maxsize": "255", "readonly": "True"}
        ),
        required=False,
    )

    sequence_1 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_2 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_3 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_4 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_5 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_6 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_7 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_8 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_9 = forms.IntegerField(min_value=1, max_value=10, required=False)
    sequence_10 = forms.IntegerField(min_value=1, max_value=10, required=False)

    color1 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color2 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color3 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color4 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color5 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color6 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color7 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color8 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color9 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)
    color10 = forms.IntegerField(min_value=00000000, max_value=99999999, required=False)

    colorDef1 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef2 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef3 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef4 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef5 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef6 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef7 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef8 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef9 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )
    colorDef10 = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=False,
    )

    def __init__(self, request, job, *args, **kwargs):
        """Here we populate some of the fields based on certain conditions.
        Also, update some of the choice field querysets.
        """
        super(ItemFormCart, self).__init__(*args, **kwargs)
        self.initial["location"] = "Outside"
        self.fields["customer_code"].widget.attrs["placeHolder"] = "(Not Required)"
        self.fields["product_group"].widget.attrs["placeHolder"] = "(Not Required)"
        self.fields["graphic_po"].widget.attrs["placeHolder"] = "(Not Required)"
        # Carton type specific labels
        if job.carton_type:
            if job.carton_type == "Imposition":
                self.fields["graphic_req_number"].widget.attrs["placeHolder"] = (
                    "(Portland Only)"
                )
            if job.carton_type == "Prepress":
                self.fields["grn"].widget.attrs["placeHolder"] = "(Not Required)"

        # Use the job's workflow to decide which print locations to show.
        self.fields["printlocation"].queryset = PrintLocation.objects.filter(
            plant__workflow=job.workflow
        ).order_by("plant__name")
        self.fields["color1"].widget.attrs["style"] = "width:80px"
        self.fields["color2"].widget.attrs["style"] = "width:80px"
        self.fields["color3"].widget.attrs["style"] = "width:80px"
        self.fields["color4"].widget.attrs["style"] = "width:80px"
        self.fields["color5"].widget.attrs["style"] = "width:80px"
        self.fields["color6"].widget.attrs["style"] = "width:80px"
        self.fields["color7"].widget.attrs["style"] = "width:80px"
        self.fields["color8"].widget.attrs["style"] = "width:80px"
        self.fields["color9"].widget.attrs["style"] = "width:80px"
        self.fields["color10"].widget.attrs["style"] = "width:80px"

        self.fields["colorDef1"].label_from_instance = self.label_from_instance
        self.fields["colorDef2"].label_from_instance = self.label_from_instance
        self.fields["colorDef3"].label_from_instance = self.label_from_instance
        self.fields["colorDef4"].label_from_instance = self.label_from_instance
        self.fields["colorDef5"].label_from_instance = self.label_from_instance
        self.fields["colorDef6"].label_from_instance = self.label_from_instance
        self.fields["colorDef7"].label_from_instance = self.label_from_instance
        self.fields["colorDef8"].label_from_instance = self.label_from_instance
        self.fields["colorDef9"].label_from_instance = self.label_from_instance
        self.fields["colorDef10"].label_from_instance = self.label_from_instance

    def clean(self):
        """Certain fields are required depending on the job's carton type."""
        cleaned_data = super().clean()
        check_job = cleaned_data.get("job")

        # Check fields required for all carton jobs.
        if not cleaned_data.get(
            "description"
        ):  # Bev items use this field too but it's optional there so we can't require it at the database level.
            raise forms.ValidationError("Description required for carton jobs.")
        if check_job.carton_type:
            # Check fields required for imposition jobs.
            if check_job.carton_type == "Imposition":
                if not cleaned_data.get("step_die"):
                    raise forms.ValidationError(
                        "Step Die required for imposition carton jobs."
                    )
                if not cleaned_data.get("coating_pattern"):
                    raise forms.ValidationError(
                        "Coating Pattern required for imposition carton jobs."
                    )
                if not cleaned_data.get("plate_thickness"):
                    raise forms.ValidationError(
                        "Plate Thickness required for imposition carton jobs."
                    )
                if not cleaned_data.get("print_repeat"):
                    raise forms.ValidationError(
                        "Print Repeat required for imposition carton jobs."
                    )
                if not cleaned_data.get("grn"):
                    raise forms.ValidationError(
                        "GDD required for imposition carton jobs."
                    )
                if not cleaned_data.get("platepackage"):
                    raise forms.ValidationError(
                        "Plate Package required for imposition carton jobs."
                    )
            # Check fields required for prepress jobs.
            if check_job.carton_type == "Prepress":
                if not cleaned_data.get("proof_type"):
                    raise forms.ValidationError(
                        "Proof Type required for prepress carton jobs."
                    )
                if not cleaned_data.get("graphic_req_number"):
                    raise forms.ValidationError(
                        "Graphic Req # required for prepress carton jobs."
                    )
                if not cleaned_data.get("substrate"):
                    raise forms.ValidationError(
                        "Substrate required for prepress carton jobs."
                    )
                if not cleaned_data.get("line_screen"):
                    raise forms.ValidationError(
                        "Line Screen required for prepress carton jobs."
                    )
                if not cleaned_data.get("ink_set"):
                    raise forms.ValidationError(
                        "Ink Set required for prepress carton jobs."
                    )

    @abstractstaticmethod
    def label_from_instance(self):
        return self.name


def new_carton_item(request, job_id, type, item_id=0):
    """Form and save function for creating a new Carton item via the
    New Job Entry, not the job detail page.
    """
    job = Job.objects.get(id=job_id)

    # Check to see if job qualifies as a rush.
    today = date.today()
    if today + timedelta(days=0) >= job.due_date:
        pass
    elif today + timedelta(days=4) > job.due_date:
        pass
    else:
        pass

    if request.method == "POST":
        itemform = ItemFormCart(request, job, request.POST)
        if itemform.is_valid():
            item = itemform.save()

            for ink_num in range(1, 11):
                if request.POST["color%s" % ink_num] != "":
                    ic = ItemColor(item=item)
                    ic.color = request.POST["color%s" % ink_num]

                    colorDef = ColorDefinition.objects.filter(
                        id=request.POST["colorDef%s" % ink_num]
                    )
                    if colorDef:
                        colorDef = colorDef[0]
                        if colorDef.name == "Match Color":
                            ic.hexvalue = request.POST["picker%s" % ink_num]
                            ic.definition = colorDef
                            ic.sequence = request.POST["sequence_%s" % ink_num]
                        else:
                            ic.hexvalue = colorDef.hexvalue
                            ic.definition = colorDef
                            ic.sequence = request.POST["sequence_%s" % ink_num]

                    ic.save()

            item.calculate_item_distortion()
            # Save the item so that the nomenclature calculates using colors.
            item.save()
            # Create folder after item colors are added, so that bev_nomenclature()
            # creates nomenclature properly.
            item.create_folder()
            return HttpResponse(
                JSMessage("Saved Item #" + str(item.num_in_job) + " successfully")
            )
        else:
            # Use the JSONErrorForm subclass to send any errors via JSON.
            return itemform.serialize_errors()
    else:
        itemform = ItemFormCart(request, job)

        pagevars = {
            "page_title": "Add Item to Carton Job",
            "job": job,
            "itemform": itemform,
            "workflow": Site.objects.get(name="Carton"),
            "type": type,
        }

        return render(request, "workflow/job/carton_new_item.html", context=pagevars)


class NewCartJobForm(ModelForm, JSONErrorForm):
    """Form used for adding a job - Carton"""

    dueDay = date.today() + timedelta(days=5)
    day_check = dueDay.isoweekday()
    if day_check == 6:
        dueDay = dueDay + timedelta(days=2)
    if day_check == 7:
        dueDay = dueDay + timedelta(days=1)
    due_date = forms.DateField(widget=GCH_SelectDateWidget, initial=dueDay)
    # Name will be labeled as customer name.
    name = forms.CharField(required=True)
    workflow = _safe_get_site("Carton")
    instructions = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "16"}), required=False
    )
    pcss = forms.ModelChoiceField(
        queryset=User.objects.filter(
            is_active=True, groups__in=PCSS_PERMISSION.group_set.all()
        ).order_by("username"),
        required=False,
    )
    # Just show carton salespeople.
    carton_users = User.objects.filter(groups__in=CARTON_PERMISSION.group_set.all())
    grouped_sales_users = (
        User.objects.filter(groups__in=SALES_PERMISSION.group_set.all())
        .order_by("username")
        .distinct()
    )
    salesperson = forms.ModelChoiceField(
        queryset=grouped_sales_users.distinct(), required=False
    )
    csr = forms.ModelChoiceField(
        User.objects.filter(
            is_active=True, groups__in=CARTON_CSR_PERMISSION.group_set.all()
        ).order_by("username"),
        required=False,
    )
    graphic_specialist = forms.ModelChoiceField(
        User.objects.filter(
            is_active=True, groups__in=GRAPHIC_SPECIALIST_PERMISSION.group_set.all()
        ).order_by("username"),
        required=False,
    )
    graphic_supplier = forms.CharField(required=True)
    customer_identifier = forms.CharField(required=True)
    customer_name = forms.CharField(required=True)

    class Meta:
        model = Job
        fields = (
            "workflow",
            "status",
            "graphic_supplier",
            "customer_identifier",
            "due_date",
            "name",
            "salesperson",
            "csr",
            "instructions",
            "customer_name",
            "graphic_specialist",
            "carton_type",
            "pcss",
        )

    def __init__(self, request, *args, **kwargs):
        super(NewCartJobForm, self).__init__(*args, **kwargs)
        # Try to set the current user as the initial value for PCSS.
        self.fields["pcss"].initial = request.user.id


@login_required
def new_carton_job(request):
    """Form and save function for creating a new Carton job."""
    if request.POST:
        jobform = NewCartJobForm(request, request.POST, prefix="job")
        jobaddressform = CartJobAddressForm(request.POST, prefix="address")
        if jobform.is_valid():
            if jobaddressform.is_valid():
                job = jobform.save()
                # Get rid of special characters like '/', causing folder creation problems.
                job.name = fs_api.strip_for_valid_filename(job.name)
                job.customer_name = request.POST["job-customer_name"]
                if "job-instructions" in request.POST:
                    job.do_create_joblog_entry(
                        JOBLOG_TYPE_NOTE,
                        request.POST["job-instructions"],
                        is_editable=False,
                    )
                # Save both forms.
                jobaddress = jobaddressform.save(commit=False)
                jobaddress.job = job
                jobaddress.save()
                job.save()
                # Create folder after saving, must strip bad characters from job name.
                job.create_folder()
                return HttpResponse(JSMessage(job.id))
            else:  # Errors in the job address form.
                return jobaddressform.serialize_errors()
        else:  # Errors in the job form.
            return jobform.serialize_errors()
    else:
        jobform = NewCartJobForm(request, prefix="job")
        jobaddressform = CartJobAddressForm(prefix="address")

        pagevars = {
            "page_title": "New Carton Job",
            "jobform": jobform,
            "jobaddressform": jobaddressform,
        }

        return render(request, "workflow/job/carton_new.html", context=pagevars)


class NewConJobForm(ModelForm, JSONErrorForm):
    """Form used for adding a job - Container"""

    # plant = forms.CharField(max_length=30, required=False)
    # TODO: Change salesperson field to foreign key to users in group salesperson
    due_date = forms.DateField(
        widget=GCH_SelectDateWidget,
        initial=general_funcs._utcnow_naive().date() + timedelta(days=1),
    )
    workflow = _safe_get_site("Container")
    instructions = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "16"}), required=False
    )
    # Select users who are a member of the set of groups with the given permission.
    grouped_sales_users = (
        User.objects.filter(groups__in=SALES_PERMISSION.group_set.all())
        .order_by("username")
        .distinct()
    )
    salesperson = forms.ModelChoiceField(
        queryset=grouped_sales_users.distinct(), required=False
    )
    temp_printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(
            plant__workflow=workflow, active=True
        ).order_by("plant__name")
    )
    temp_platepackage = forms.ModelChoiceField(
        queryset=PlatePackage.objects.filter(workflow=workflow, active=True).order_by(
            "platemaker__name"
        )
    )

    class Meta:
        model = Job
        fields = "__all__"


def new_container_job(request):
    """Form and save function for creating a new Beverage job."""
    if request.POST:
        jobform = NewConJobForm(request, request.POST)
        if jobform.is_valid():
            jobform.instance.name = fs_api.strip_for_valid_filename(
                jobform.instance.name
            )
            jobform.save()
            job_id = jobform.instance.id
            job = Job.objects.get(id=job_id)
            job.create_folder()
            if "instructions" in request.POST:
                job.do_create_joblog_entry(
                    JOBLOG_TYPE_NOTE, request.POST["instructions"]
                )
            return HttpResponse(JSMessage(job_id))
        else:
            return jobform.serialize_errors()
    else:
        jobform = NewConJobForm(request)

        pagevars = {
            "page_title": "New Container Job",
            "jobform": jobform,
            "workflow": _safe_get_site("Container"),
        }
        return render(request, "workflow/job/container_new.html", context=pagevars)


class ItemFormCON(forms.Form, JSONErrorForm):
    """Decoupled from the model form to allow new size input"""

    workflow = _safe_get_site("Container")
    die = forms.CharField(widget=forms.TextInput(attrs={"size": "50"}), required=True)
    description = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    upc_number = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    length = forms.DecimalField(required=True)
    width = forms.DecimalField(required=True)
    height = forms.DecimalField(required=True)
    num_up = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    material = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    ect = forms.CharField(widget=forms.TextInput(attrs={"size": "50"}), required=False)
    color1 = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=True
    )
    color2 = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    color3 = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    color4 = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )


def new_container_item(request, job_id):
    """Saves the data for a new item added to a container job."""
    job = Job.objects.get(id=job_id)
    workflow = _safe_get_site("Container")
    if request.POST:
        itemform = ItemFormCON(request.POST)
        # Lookup size, if not existing, make it so.
        if itemform.is_valid():
            item = Item()
            try:
                size = ItemCatalog.objects.get(size__iexact=request.POST["die"])
            except ItemCatalog.DoesNotExist:
                size = ItemCatalog(size=request.POST["die"])
                size.workflow = workflow
                size.save()
            item.size = size
            if request.POST["description"]:
                item.description = request.POST["description"]
            if request.POST["upc_number"]:
                item.upc_number = request.POST["upc_number"]
            if request.POST["length"]:
                item.length = request.POST["length"]
            if request.POST["width"]:
                item.width = request.POST["width"]
            if request.POST["height"]:
                item.height = request.POST["height"]
            if request.POST["num_up"]:
                item.num_up = request.POST["num_up"]
            if request.POST["material"]:
                item.material = request.POST["material"]
            if request.POST["ect"]:
                item.ect = request.POST["ect"]

            # Inherit some fields from parent job.
            item.printlocation = job.temp_printlocation
            item.platepackage = job.temp_platepackage
            item.workflow = workflow
            item.item_status = "Pending"
            item.job = job
            item.save()
            item.create_folder()

            # Setup inks from form.
            for ink_num in range(1, 5):
                if request.POST["color%s" % ink_num] != "":
                    ic = ItemColor(item=item)
                    ic.color = request.POST["color%s" % ink_num]
                    ic.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            return itemform.serialize_errors()
    else:
        itemform = ItemFormCON()

        pagevars = {
            "job": job,
            "itemform": itemform,
        }
        return render(request, "workflow/job/container_new_item.html", context=pagevars)


class ChargeTypeModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.menu_name()


class AddBillingAllItems(forms.Form, JSONErrorForm):
    """Form for adding billing charges to all items."""

    charge_type = ChargeTypeModelChoiceField(
        ChargeType.objects.all().order_by("-category", "type"), required=True
    )


@csrf_exempt
def edit_all_billing(request, job_id):
    """Make additions to billing to all qualified items at once."""
    job = Job.objects.get(id=job_id)
    items = Item.objects.filter(job=job)
    permission = Permission.objects.get(codename="in_artist_pulldown")
    artists = User.objects.filter(
        is_active=True, groups__in=permission.group_set.all()
    ).order_by("username")
    current_artist = threadlocals.get_current_user()

    form = AddBillingAllItems()
    charge_options = ChargeType.objects.filter(
        workflow=job.workflow, active=True
    ).order_by("-category", "type")
    form.fields["charge_type"].queryset = charge_options

    if request.POST:
        form = AddBillingAllItems(request.POST)
        if form.is_valid():
            # Pull the description based on the POST data.
            charge_type = ChargeType.objects.get(id=request.POST["charge_type"])
            try:
                rush_days = int(request.POST["rush_days"])
            except Exception:
                rush_days = None

            check_list_ids = []
            check_list_ids = request.POST.getlist("items_checked")
            artist = User.objects.get(id=request.POST["artist"])
            # Iterate over each item in the job, creating a new charge for each.
            # for item in items:
            # Only goes through items that have been checked...
            for item_id in check_list_ids:
                # Added this line to grab the Items that have been checked from the template page
                item = Item.objects.get(id=item_id)

                c = Charge()
                c.artist = artist
                c.item = item
                c.description = charge_type
                c.rush_days = rush_days
                c.amount = charge_type.actual_charge(
                    num_colors=item.itemcolor_set.count(),
                    quality=item.quality,
                    rush_days=rush_days,
                    item=item,
                )
                c.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            return form.serialize_errors()
    # Display options for updated all items.
    pagevars = {
        "page_title": "Update All Items - Billing",
        "job": job,
        "items": items,
        "artists": artists,
        "form": form,
        "current_artist": current_artist,
    }
    return render(request, "workflow/job/ajax/editall_billing.html", context=pagevars)


def item_tracker_mkt(request, job_id):
    """Flags items with marketing item trackers using the ItemTracker() model."""
    job = Job.objects.get(id=job_id)
    item_list = Item.objects.filter(job=job)
    mkttracklist = ItemTracker.objects.filter(
        item__in=item_list, type__category__name="Marketing", removal_date__isnull=True
    )

    viewer_list = []
    manager_members = User.objects.filter(
        groups__name="EmailGCHubManager", is_active=True
    )
    super_members = User.objects.filter(groups__name="GCHubSupervisor", is_active=True)
    for viewer in manager_members:
        viewer_list.append(viewer.username)
    for viewer in super_members:
        viewer_list.append(viewer.username)
    user = threadlocals.get_current_user()
    can_view = False
    if str(user) in viewer_list:
        can_view = True

    if request.POST:
        form = ItemTrackerMktForm(request.POST)
        if form.is_valid():
            # Grab the supplied art catagories and set up a quick counter.
            catagory = form.cleaned_data["catagory"]

            check_list_ids = []
            check_list_ids = request.POST.getlist("items_checked")
            for item_id in check_list_ids:
                # Use the counter to count through the supplied catagories
                # and create a new tracker for each of them.
                counter = len(catagory)
                review_comments = ""
                item = Item.objects.get(id=item_id)
                types = ""
                while counter > 0:
                    new_tracker = ItemTracker()
                    new_tracker.item = item
                    new_tracker.type = ItemTrackerType.objects.get(
                        id=catagory[counter - 1].id
                    )
                    types += str(new_tracker.type) + ", "
                    new_tracker.addition_comments = form.cleaned_data[
                        "addition_comments"
                    ]
                    new_tracker.addition_date = date.today()
                    new_tracker.edited_by = threadlocals.get_current_user()
                    new_tracker.save()
                    review_comments += "%s and " % (catagory[counter - 1])
                    counter -= 1
                # remove the comma and space from the end of the types
                types = types[:-2]
                # Let's chop of that last 'and ' to make it pretty.
                review_comments = review_comments[:-4]
                # Now that the items have been flagged we need to create a
                # marketing review for it.
                new_review = ItemReview(
                    item=item,
                    review_catagory="market",
                    entry_comments=review_comments,
                    comments=form.cleaned_data["addition_comments"],
                    reviewer=threadlocals.get_current_user(),
                    review_initiated_date=date.today(),
                )
                new_review.save()

                # notify via email the marketers that will accept / reject
                site_link = "http://gchub.graphicpkg.com/workflow/mkt_review/"
                mail_body = loader.get_template("emails/marketing_review_ready.txt")
                mail_subject = "GOLD Marketing approval required for Job: %s" % (
                    item.job.id
                )
                econtext = {
                    "job_name": item.job,
                    "item_num": item.num_in_job,
                    "type": types,
                    "item": item,
                    "job": item.job,
                    "comments": new_tracker.addition_comments,
                    "site_link": site_link,
                }
                mail_send_to = []
                # In an effort to just email Lena we have to hardcode cause there is no group
                # composed of just them
                # for contact in User.objects.filter(is_active=True, groups__name='FSB Marketing'):
                group_members = User.objects.filter(
                    groups__name="EmailItemTrackers", is_active=True
                )
                for user in group_members:
                    mail_send_to.append(user.email)

                if len(mail_send_to) > 0:
                    general_funcs.send_info_mail(
                        mail_subject, mail_body.render(econtext), mail_send_to
                    )

            # Done creating art trackers and reviews and sending email.
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:
        form = ItemTrackerMktForm()
        pagevars = {
            "job": job,
            "job_items": item_list,
            "view": "item_tracker_mkt",
            "form": form,
            "mkttracklist": mkttracklist,
            "can_view": can_view,
        }
        return render(
            request, "workflow/item/ajax/subview_tracked_mkt.html", context=pagevars
        )


def item_tracker_promo(request, job_id):
    """Flags items with promotional item trackers using the ItemTracker() model."""
    job = Job.objects.get(id=job_id)
    item_list = Item.objects.filter(job=job)
    promotracklist = ItemTracker.objects.filter(
        item__in=item_list,
        type__category__name="Promotional",
        removal_date__isnull=True,
    )

    viewer_list = []
    manager_members = User.objects.filter(
        groups__name="EmailGCHubManager", is_active=True
    )
    super_members = User.objects.filter(groups__name="GCHubSupervisor", is_active=True)
    for viewer in manager_members:
        viewer_list.append(viewer.username)
    for viewer in super_members:
        viewer_list.append(viewer.username)
    user = threadlocals.get_current_user()
    can_view = False
    if str(user) in viewer_list:
        can_view = True

    if request.POST:
        form = ItemTrackerPromoForm(request.POST)
        if form.is_valid():
            # Grab the supplied catagories and set up a quick counter.
            catagory = form.cleaned_data["catagory"]
            counter = len(catagory)
            check_list_ids = []
            check_list_ids = request.POST.getlist("items_checked")
            for item_id in check_list_ids:
                # Use the counter to count through the supplied catagories
                # and create a new tracker for each of them.
                counter = len(catagory)
                item = Item.objects.get(id=item_id)
                # Use the counter to count through the supplied catagories
                # and create a new tracker for each of them.
                while counter > 0:
                    new_tracker = ItemTracker()
                    new_tracker.item = item
                    new_tracker.type = ItemTrackerType.objects.get(
                        id=catagory[counter - 1].id
                    )
                    new_tracker.addition_comments = form.cleaned_data[
                        "addition_comments"
                    ]
                    new_tracker.addition_date = date.today()
                    new_tracker.edited_by = threadlocals.get_current_user()
                    new_tracker.save()
                    counter -= 1
            # Done creating trackers.
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:
        form = ItemTrackerPromoForm()
        pagevars = {
            "job": job,
            "form": form,
            "view": "item_tracker_promo",
            "job_items": item_list,
            "promotracklist": promotracklist,
            "can_view": can_view,
        }
        return render(
            request, "workflow/item/ajax/subview_promotrack.html", context=pagevars
        )


@csrf_exempt
def item_tracker_art(request, job_id):
    """Flags items with promotional item trackers using the ItemTracker() model."""
    job = Job.objects.get(id=job_id)
    item_list = Item.objects.filter(job=job)
    arttracklist = ItemTracker.objects.filter(
        item__in=item_list, type__category__name="Artwork", removal_date__isnull=True
    )

    viewer_list = []
    manager_members = User.objects.filter(
        groups__name="EmailGCHubManager", is_active=True
    )
    super_members = User.objects.filter(groups__name="GCHubSupervisor", is_active=True)
    for viewer in manager_members:
        viewer_list.append(viewer.username)
    for viewer in super_members:
        viewer_list.append(viewer.username)
    user = threadlocals.get_current_user()
    can_view = False
    if str(user) in viewer_list:
        can_view = True

    if request.POST:
        form = ItemTrackerArtForm(request.POST)
        if form.is_valid():
            # Grab the supplied art catagories and set up a quick counter.
            catagory = form.cleaned_data["catagory"]
            check_list_ids = []
            check_list_ids = request.POST.getlist("items_checked")
            for item_id in check_list_ids:
                # Use the counter to count through the supplied catagories
                # and create a new tracker for each of them.
                counter = len(catagory)
                item = Item.objects.get(id=item_id)
                while counter > 0:
                    new_tracker = ItemTracker()
                    new_tracker.item = item
                    new_tracker.type = ItemTrackerType.objects.get(
                        id=catagory[counter - 1].id
                    )
                    new_tracker.addition_comments = form.cleaned_data[
                        "addition_comments"
                    ]
                    new_tracker.addition_date = date.today()
                    new_tracker.edited_by = threadlocals.get_current_user()
                    new_tracker.save()
                    counter -= 1
            # Done creating trackers.
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:
        form = ItemTrackerArtForm()
        pagevars = {
            "job": job,
            "form": form,
            "view": "item_tracker_art",
            "job_items": item_list,
            "arttracklist": arttracklist,
            "can_view": can_view,
        }
    return render(
        request, "workflow/item/ajax/subview_tracked_art.html", context=pagevars
    )


class ItemTrackerMktForm(forms.Form):
    """The form at the bottom of an item's marketing review page. Used to track
    elements that marketing needs to keep up with like SFI logos. Uses the
    ItemTracker() model to flag items for tracking.
    """

    addition_comments = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )
    catagory = ModelMultipleChoiceField(
        ItemTrackerType.objects.filter(category__name="Marketing").order_by("name")
    )


class ItemTrackerPromoForm(forms.Form):
    """The form at the bottom of an item's promo review page. Used to track
    promotional work. Uses the ItemTracker() model to flag items for tracking.
    """

    addition_comments = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )
    catagory = ModelMultipleChoiceField(
        ItemTrackerType.objects.filter(category__name="Promotional").order_by("name")
    )


class ItemTrackerArtForm(forms.Form):
    """The form at the bottom of an item's promo review page. Used to track
    promotional work. Uses the ItemTracker() model to flag items for tracking.
    """

    addition_comments = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )
    catagory = ModelMultipleChoiceField(
        ItemTrackerType.objects.filter(category__name="Artwork").order_by("name")
    )


@csrf_exempt
def timesheets(request, job_id):
    """Timesheets for this job. Now also displays materials."""
    job = Job.objects.get(id=job_id)
    timesheets = TimeSheet.objects.filter(job=job).order_by("id")

    # Timesheet hour cost in dollars
    hours_cost = 150

    # Calculate the total hours per activity from this job's timesheet entries.
    totals = {}

    for entry in timesheets:
        if entry.category in totals:
            totals[entry.category] += entry.hours
        else:
            totals[entry.category] = entry.hours

    # Calculate the total hours from this job's timesheets.
    total_hours = 0
    for sheet in timesheets:
        total_hours += sheet.hours

    # Assemble a string that shows num of hours x cost = total
    hours_grand_total = "%s hours x $%s / hr = $%s" % (
        "%.2f" % total_hours,
        hours_cost,
        "%.2f" % (total_hours * hours_cost),
    )

    # Dictionary for storing materials used.
    materials = {}

    # Calculate the total number of proofs printed for this job.
    proofs = ProofTracker.objects.filter(item__job=job)

    # Proof cost in dollars
    proof_cost = 90

    # Count to proofs
    total_proofs = 0
    for proof in proofs:
        total_proofs += proof.copies

    # Assemble a string that shows num of proofs x cost = total
    proofs_grand_total = "%s proofs x $%s = $%s" % (
        total_proofs,
        proof_cost,
        total_proofs * proof_cost,
    )

    # Add proof total total string to materials dictionary
    materials["Proofs"] = proofs_grand_total

    # Display options for updated all items.
    pagevars = {
        "page_title": "Job Timesheets",
        "timesheets": timesheets,
        "hours_grand_total": hours_grand_total,
        "totals": totals,
        "materials": materials,
    }

    return render(request, "workflow/job/ajax/timesheets.html", context=pagevars)


class ForecastAllForm(forms.Form):
    """Forecast All form."""

    text = forms.CharField(required=False)


@csrf_exempt
def edit_all_timeline_pageload(request, job_id, event, action):
    """Make updates to all qualified items at once."""
    job = Job.objects.get(id=job_id)
    all_items = Item.objects.filter(job=job)

    if action == "View":
        pagevars = {
            "page_title": "Update All Items - Timeline",
            "job": job,
            "items": all_items,
            "event": event,
        }

        return render(
            request,
            "workflow/job/ajax/editall_timeline_pageload.html",
            context=pagevars,
        )
    else:
        values = request.POST.getlist("items_checked")
        if event == "Preflight":
            for item in all_items:
                if item.can_preflight() and str(item.id) in values:
                    item.do_preflight()
        elif event == "Proof":
            for item in all_items:
                if item.can_proof() and str(item.id) in values:
                    item.do_proof()
        elif event == "Approve":
            for item in all_items:
                if item.can_approve() and str(item.id) in values:
                    item.do_approve()
        elif event == "Forecast":
            if all_items:
                forecast_arr = []
                for item in all_items:
                    if item.can_forecast() and str(item.id) in values:
                        forecast_text = request.POST.getlist("items_forecast")
                        forecast_text = forecast_text[0]
                        item.do_forecast()
                        forecast_arr.append(item.num_in_job)
                pre_forecast_text = (
                    "Item(s) " + str(forecast_arr)[1:-1] + " forecast set as "
                )
                job.do_create_joblog_entry(
                    JOBLOG_TYPE_NOTE, pre_forecast_text + request.POST["items_forecast"]
                )
        elif event == "File Out":
            for item in all_items:
                if item.can_file_out() and str(item.id) in values:
                    item.do_final_file()
                    item.do_plate_order()
        elif event == "Remake PDFs":
            for item in all_items:
                if str(item.id) in values:
                    item.do_tiff_to_pdf()

    return HttpResponse(JSMessage("Updated All."))


@csrf_exempt
def edit_all_timeline(request, job_id, event="View"):
    """Make updates to all qualified items at once."""
    job = Job.objects.get(id=job_id)
    all_items = Item.objects.filter(job=job)

    if request.POST and event == "Forecast":
        forecastform = ForecastAllForm(request.POST)
        if forecastform.is_valid() and forecastform.cleaned_data["text"]:
            forecast_text = "All items forecast as " + forecastform.cleaned_data["text"]
            job.do_create_joblog_entry(JOBLOG_TYPE_NOTE, forecast_text)
    else:
        forecastform = ForecastAllForm()

    # Make list of all items that cannot be preflighted.
    items_no_preflight = []
    for item in all_items:
        if not item.can_preflight():
            items_no_preflight.append(item)
    # Make list of all items that cannot be proofed.
    items_no_proof = []
    for item in all_items:
        if not item.can_proof():
            items_no_proof.append(item)
    # Make list of all items that cannot be approved.
    items_no_approve = []
    for item in all_items:
        if not item.can_approve():
            items_no_approve.append(item)
    # Make list of all items that cannot be forecasted.
    items_no_forecast = []
    for item in all_items:
        if not item.can_forecast():
            items_no_forecast.append(item)
    # Make list of all items that cannot be filed out.
    items_no_file_out = []
    for item in all_items:
        if not item.can_file_out():
            items_no_file_out.append(item)

    # Event determines display or action.
    if event == "View":
        # Display options for updated all items.

        pagevars = {
            "page_title": "Update All Items - Timeline",
            "job": job,
            "items_no_preflight": items_no_preflight,
            "items_no_proof": items_no_proof,
            "items_no_approve": items_no_approve,
            "items_no_forecast": items_no_forecast,
            "items_no_file_out": items_no_file_out,
            "forecastform": forecastform,
        }

        return render(
            request, "workflow/job/ajax/editall_timeline.html", context=pagevars
        )
    else:
        print(event)


def ajax_job_save(request, job_id):
    """AJAX request for saving a job item."""
    job = Job.objects.get(id=job_id)
    jobform = JobForm(request, request.POST, instance=job)
    # See if there's an existing job complexity to edit.
    try:
        jobcomplex = JobComplexity.objects.get(job=job)
        jobcomplexform = JobComplexityForm(request.POST, instance=jobcomplex)
    except Exception:
        jobcomplex = None  # We'll want to check this later.
        jobcomplexform = JobComplexityForm(request.POST)
    if jobform.is_valid() and jobcomplexform.is_valid():
        # form.is_valid() will overwrite model instance, so we requery for old item
        job = Job.objects.get(id=job_id)
        if "due_date" in request.POST:
            new_due_date_pull = request.POST["due_date"]
            new_due_date_strtodate = datetime.strptime(new_due_date_pull, "%Y-%m-%d")
            new_due_date = new_due_date_strtodate.strftime("%Y-%m-%d")
            old_due_date = str(job.due_date)
            if new_due_date != old_due_date:
                logchanges = (
                    "<strong>Due date changed:</strong> ("
                    + str(old_due_date)
                    + " to "
                    + str(new_due_date)
                    + "). "
                )
                job.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, logchanges)

        if "status" in request.POST:
            new_status = request.POST["status"]
            old_status = job.status
            if new_status != old_status:
                if old_status != "Pending":
                    logchanges = (
                        "<strong>The status of the job has changed:</strong> ("
                        + str(old_status)
                        + " to "
                        + str(new_status)
                        + "). "
                    )
                    job.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, logchanges)
                else:
                    for item in job.item_set.all():
                        item.is_queued_for_thumbnailing = True
                        item.save()

        if "artist" in request.POST:
            new_artist_id = request.POST["artist"]
            try:
                new_artist = User.objects.get(id=new_artist_id)
            except ValueError:
                new_artist = None
            except User.DoesNotExist:
                new_artist = None
            old_artist = job.artist
            if new_artist != old_artist:
                logchanges = (
                    "<strong>The assigned artist has changed:</strong> ("
                    + str(old_artist)
                    + " to "
                    + str(new_artist)
                    + "). "
                )
                job.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, logchanges)
                change_artist = True
            else:
                change_artist = False

        if "csr" in request.POST:
            new_csr_id = request.POST["csr"]
            try:
                new_csr = User.objects.get(id=new_csr_id)
            except ValueError:
                new_csr = None
            except User.DoesNotExist:
                new_csr = None
            old_csr = job.csr
            if new_csr != old_csr:
                logchanges = (
                    "<strong>The assigned CSR has changed:</strong> ("
                    + str(old_csr)
                    + " to "
                    + str(new_csr)
                    + "). "
                )
                job.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, logchanges)
                job.csr = new_csr

        jobform.save()

        # Now take care of any job complexities associated with this job.
        if jobcomplex:  # We're updating an existing job complexity.
            jobcomplexform.save()
        else:  # We're saving a new job complexity.
            # Make sure the user actually selected something.
            if (
                jobcomplexform.cleaned_data["category"]
                or jobcomplexform.cleaned_data["complexity"]
            ):
                # Set the job for the job complexity before saving.
                jobcomplexform = jobcomplexform.save(commit=False)
                jobcomplexform.job = job
                jobcomplexform.save()

        if change_artist:
            job.do_artist_assignment_email()

        return HttpResponse(JSMessage("Saved."))
    else:
        return {jobform.serialize_errors(), jobcomplexform.serialize_errors()}


class PrintLocationForm(ModelForm, JSONErrorForm):
    """Form with only the printlocation in it.
    This will be used for plant/press changes in Beverage.
    """

    workflow = _safe_get_site("Beverage")
    temp_printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(plant__workflow=workflow, active=True)
        .distinct()
        .order_by("plant__name")
    )

    class Meta:
        model = Job
        fields = ("temp_printlocation",)


def change_printlocation(request, job_id):
    """Change the PrintLocation of the Job (if Beverage) and all items on the job."""
    job = Job.objects.get(id=job_id)
    current_printlocation = job.temp_printlocation
    if request.POST:
        form = PrintLocationForm(request.POST, instance=job)
        if form.is_valid():
            data = form
            data.save()
            for item in job.item_set.all():
                item.printlocation = job.temp_printlocation
                item.save()
            logchanges = (
                "<strong>The print location has changed:</strong> ("
                + str(current_printlocation)
                + " to "
                + str(job.temp_printlocation)
                + "). "
            )
            job.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, logchanges)
            return HttpResponse(JSMessage("Saved."))
        else:
            return form.serialize_errors()
    else:
        form = PrintLocationForm(instance=job)

        pagevars = {
            "form": form,
            "job": job,
        }

    return render(
        request, "workflow/job/ajax/change_printlocation.html", context=pagevars
    )


class PlatePackageForm(ModelForm, JSONErrorForm):
    """Form with only the platepackage in it.
    This will be used for platemaker/platetype changes in Beverage.
    """

    workflow = _safe_get_site("Beverage")
    # There's an old unused cyber graphics platemaker that we've been asked to
    # hide from this field.
    temp_platepackage = forms.ModelChoiceField(
        queryset=PlatePackage.objects.filter(workflow=workflow, active=True)
        .distinct()
        .order_by("platemaker__name")
        .exclude(platemaker__id=18)
    )

    class Meta:
        model = Job
        fields = ("temp_platepackage",)


def change_platepackage(request, job_id):
    """Change the PlatePackage of the Job (if Beverage) and all items on the job."""
    job = Job.objects.get(id=job_id)
    # Save this for use in the log entry.
    current_platepackage = job.temp_platepackage
    if request.POST:
        form = PlatePackageForm(request.POST, instance=job)
        if form.is_valid():
            data = form
            data.save()
            for item in job.item_set.all():
                item.platepackage = job.temp_platepackage
                item.save()
            # Log changes as critical -- could effect artwork.
            logchanges = (
                "<strong>The plate package has changed:</strong> ("
                + str(current_platepackage)
                + " to "
                + str(job.temp_platepackage)
                + "). "
            )
            job.do_create_joblog_entry(JOBLOG_TYPE_CRITICAL, logchanges)
            return HttpResponse(JSMessage("Saved."))
        else:
            return form.serialize_errors()
    else:
        form = PlatePackageForm(instance=job)

        pagevars = {
            "form": form,
            "job": job,
        }

    return render(
        request, "workflow/job/ajax/change_platepackage.html", context=pagevars
    )


def remove_from_archive(request, job_id):
    """Perform the steps to remove a job from archive."""
    job = Job.objects.get(id=job_id)
    try:
        # Remove symlink in Archive.
        job.delete_folder_symlink()
        # This needs to come after deleting the symlink so that it can still find
        # the symlink to delete it.
        job.archive_disc = ""
        job.save()
        # Creates new symlink in Active.
        job.create_folder_symlink()
        job.unlock_folder()
        return HttpResponse(JSMessage("Saved."))
    except Exception:
        return HttpResponse(JSMessage("An error has occurred.", is_error=True))


@csrf_exempt
def misc_info(request, job_id):
    """Display the extended job information.
    This is the default view when a job is first loaded.
    """
    job = Job.objects.get(id=job_id)
    database_docs = fs_api.list_job_database_docs(job_id)

    pagevars = {
        "job": job,
        "database_docs": database_docs,
    }

    return render(
        request, "workflow/job/job_detail/lower/job_misc_info.html", context=pagevars
    )


class ExtendedCartonJobForm(ModelForm, JSONErrorForm):
    """For editing extended job information that doesn't fit in the upper left
    div of the job detail.
    """

    class Meta:
        # Inherit fields from the Job mode.
        model = Job
        fields = ("graphic_supplier",)


class ExtendedBeverageJobForm(ModelForm, JSONErrorForm):
    """For editing extended job information that doesn't fit in the upper left
    div of the job detail.
    """

    class Meta:
        # Inherit fields from the Job mode.
        model = Job
        fields = (
            "bill_to_type",
            "sales_service_rep",
            "business_type",
            "prepress_supplier",
            "customer_po_number",
            "use_new_bev_nomenclature",
        )


def extended_job_edit(request, job_id):
    """Display the extended job information editor."""
    job = Job.objects.get(id=job_id)
    if request.POST:
        if job.workflow.name == "Carton":
            form = ExtendedCartonJobForm(request.POST, instance=job)
        else:
            form = ExtendedBeverageJobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            for item in job.item_set.all():
                item.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            return form.serialize_errors()
    else:
        if job.workflow.name == "Carton":
            form = ExtendedCartonJobForm(instance=job)
        else:
            form = ExtendedBeverageJobForm(instance=job)

        pagevars = {
            "job": job,
            "form": form,
        }

        return render(
            request,
            "workflow/job/job_detail/lower/extended_job_edit.html",
            context=pagevars,
        )


def _get_carton_invoice_pdf_object(job_id, item_ids):
    """Get the data for the invoice PDF."""
    # We'll use BytesIO instead of saving files to the filesystem, that gets
    # to be pretty messy pretty quickly. BytesIO is a drop-in replacement
    # to file objects.
    save_destination = BytesIO()
    # Pass the BytesIO object, the job ID, and the list of items off to the generation func.
    generate_carton_invoice(save_destination, job_id, item_ids)
    # Read the entire contents of the BytesIO object into a string variable.
    data = save_destination.getvalue()
    return data


@csrf_exempt
def carton_invoice(request, job_id):
    """Process download requests for carton job invoice PDFs."""
    job = Job.objects.get(id=job_id)
    item_list = Item.objects.filter(job=job)

    if request.POST:
        # See which items they selected.
        check_list_ids = []
        check_list_ids = request.POST.getlist("items_checked")

        # Save a copy of the invoice PDF to database documents.
        jobfolder = fs_api.get_job_folder(job.id)
        dd_folder = os.path.join(jobfolder, fs_api.JOBDIR["1_documents"])
        if os.path.exists(dd_folder):  # Don't save if we can't see the dd folder.
            invoices_folder = os.path.join(dd_folder, "carton_graphics_invoices")
            if not os.path.exists(
                invoices_folder
            ):  # Make an invoices folder if needed.
                fs_api.g_mkdir(invoices_folder)
            pdf_name = "%s_invc_" % (str(job.id))
            pdf_name += "%s%s" % (timezone.now().strftime("%m_%d_%y-%H_%M"), ".pdf")
            pdf_path = os.path.join(invoices_folder, pdf_name)
            # Save the PDF
            generate_carton_invoice(pdf_path, job_id, check_list_ids)

        # Generate a downloadable copy of the invoice PDF for the user.
        data = _get_carton_invoice_pdf_object(job_id, check_list_ids)
        # Prepare a simple HTTP response with the BytesIO object as an attachment.
        response = HttpResponse(data, content_type="application/pdf")
        # This is the filename the server will suggest to the browser.
        filename = "%s_invoices.pdf" % job.id
        # The attachment header will make sure the browser doesn't try to
        # render the binary/ascii data.
        response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
        # Bombs away.
        return response

    else:
        pagevars = {
            "job": job,
            "item_list": item_list,
        }
        return render(
            request,
            "workflow/job/job_detail/lower/carton_invoice.html",
            context=pagevars,
        )


def cartonprofile_lookup(
    request,
    cartonworkflow_id,
    linescreen_id,
    inkset_id,
    substrate_id,
    printlocation_id,
    printcondition_id,
):
    """Returns a carton profile id and name for a given size via json. Print
    condition is an optional field that should only be used when supplied.
    Returns a list of lists:
        carton_profile[0][0] is the name.
        carton_profile[0][1] is the profile id.
    """
    found_carton_profiles = False
    try:
        if printcondition_id == "0":  # Perform query withOUT print condition
            carton_profiles = CartonProfile.objects.filter(
                carton_workflow__id=cartonworkflow_id,
                line_screen__id=linescreen_id,
                ink_set__id=inkset_id,
                substrate__id=substrate_id,
                print_location__id=printlocation_id,
                active=True,
            )
        else:  # Perform query with print condition
            carton_profiles = CartonProfile.objects.filter(
                carton_workflow__id=cartonworkflow_id,
                line_screen__id=linescreen_id,
                ink_set__id=inkset_id,
                substrate__id=substrate_id,
                print_condition__id=printcondition_id,
                print_location__id=printlocation_id,
                active=True,
            )
        # There should only be one profile. But send the findings as a list so
        # we can display an error if more than one was found.
        if carton_profiles:
            try:
                found_carton_profiles = []
                for profile in carton_profiles:
                    # Yeah it's a list of lists.
                    profile_data = [profile.name, profile.id]
                    found_carton_profiles.append(profile_data)
            except Exception:
                found_carton_profiles = False
    except Exception:
        found_carton_profiles = False
    return HttpResponse(
        json.dumps(found_carton_profiles), content_type="application/json"
    )


def etools_show_request(request, job_id):
    """Displays the etools request."""
    job = Job.objects.get(id=job_id)

    # Duplicated jobs don't copy over their etools IDs. If this is a duplicated
    # job, pull from the original's field instead.
    if job.duplicated_from:
        etools_id = job.duplicated_from.e_tools_id
    else:
        etools_id = job.e_tools_id

    cursor = etools.get_job_by_request_id(etools_id)
    ejob = cursor.fetchone()

    edict = {}
    for column in cursor.description:
        key_name = column[0]
        edict[key_name] = getattr(ejob, key_name, None)
        # Check for unicode errors in strings and replace them with '?'. Catches
        # strange characters from folks copy-and-pasting stuff from emails.
        if type(edict[key_name]) is str:
            edict[key_name] = str(edict[key_name])

    pagevars = {
        "job": job,
        "ejob": edict,
    }

    return render(request, "workflow/job/etools_show_request.html", context=pagevars)


def gps_connect_cust_info(request, job_id):
    """Displays customer info from GPS Connect."""
    job = Job.objects.get(id=job_id)
    data = job.get_customer_data()

    pagevars = {
        "job": job,
        "data": data,
    }

    return render(request, "workflow/job/gps_connect_cust_info.html", context=pagevars)


def gps_connect_cust_info_json(request, cust_id):
    """Fetches customer info from GPS connect and returns it as a json object.
    Mostly used by javascript to auto fill some form fields.
    """
    cust_info = gps_connect._get_customer_data(cust_id)
    if not cust_info:
        cust_info = None
    return HttpResponse(json.dumps(cust_info), content_type="application/json")


def item_duplicate_list(request, job_id):
    """If the job is duplicated from an existing one, list all items available
    to the user for duplicated from the parent job (job.duplicated_from)
    """
    job = Job.objects.get(id=job_id)
    parent_job = Job.objects.get(id=job.duplicated_from.id)
    parent_items = Item.objects.filter(job=parent_job)

    pagevars = {
        "job": job,
        "parent_job": parent_job,
        "parent_items": parent_items,
    }

    return render(
        request, "workflow/job/ajax/item_duplicate_list.html", context=pagevars
    )


class ItemFormAdd(ModelForm, JSONErrorForm):
    """Item addition form."""

    class Meta:
        model = Item
        # fields = ('job', 'size', 'plant', 'press')
        exclude = ("inkbook",)


@csrf_exempt
def add_item(request, job_id):
    """Saves the data for a new item added to a given job."""
    job = Job.objects.get(id=job_id)
    if request.POST:
        itemform = ItemFormAdd(request.POST)
        if itemform.is_valid():
            item = itemform
            item.item_status = "Pending"
            new_item = item.save()
            item.instance.create_folder()
            # Check if this job replaced a previous design. If so, a
            # notification email needs to be sent when an item is added.
            # First we see if this was created by eTools or GOLD Art Request
            art_req = ArtReq.objects.filter(Q(job_num=job_id) | Q(corr_job_num=job_id))
            if art_req:
                items_replacing_designs = []
                for req in art_req:
                    info = AdditionalInfo.objects.get(artreq=req)
                    if info.replaces_prev_design or info.prev_9_digit:
                        items_replacing_designs.append(new_item)
                etools._send_item_replaces_email(items_replacing_designs, job)
            else:
                if job.replaces_etools_design():
                    items_replacing_designs = []
                    items_replacing_designs.append(new_item)
                    etools._send_item_replaces_email(items_replacing_designs, job)
            return HttpResponse(JSMessage("Saved."))
        else:
            return itemform.serialize_errors()
    else:
        if job.workflow.name == "Foodservice":
            itemform = ItemFormFSB()
        if job.workflow.name == "Beverage":
            itemform = ItemFormBEV()
        if job.workflow.name == "Container":
            itemform = ItemFormCON()

        pagevars = {
            "job": job,
            "itemform": itemform,
        }

        return render(
            request, "workflow/job/job_detail/lower/add_item.html", context=pagevars
        )


class FileUploadForm(forms.Form, JSONErrorForm):
    """Handle file uploads to job's database documents folder."""

    file = forms.FileField()


def db_doc_upload(request, job_id):
    """Upload a file from the database to the Database Documents folder of the job."""
    job = Job.objects.get(id=job_id)
    if request.method == "POST" and request.FILES.get("file", False):
        fileform = FileUploadForm(request.POST, request.FILES)
        if fileform.is_valid():
            path = fs_api.get_job_database_path(job.id)
            destination = open(os.path.join(path, request.FILES["file"].name), "wb+")
            for chunk in request.FILES["file"]:
                destination.write(chunk)
            destination.close()
            # Send a growl notification to the artist.
            job.growl_at_artist(
                "Database Document Upload",
                "A document has been uploaded to job %s %s" % (str(job.id), job.name),
                pref_field="growl_hear_job_db_uploads",
            )
            try:
                # Email notifcation to Donna (New Items) if the uploader is a FSB CSR.
                grouped_csr_users = User.objects.filter(
                    groups__in=CSR_PERMISSION.group_set.all()
                )
                print(grouped_csr_users)
                if request.user in grouped_csr_users:
                    mail_subject = "PO Upload Notice: %s" % job
                    mail_send_to = []
                    mail_send_to.append(settings.EMAIL_GCHUB)
                    group_members = User.objects.filter(
                        groups__name="EmailGCHubNewItems", is_active=True
                    )
                    for user in group_members:
                        mail_send_to.append(user.email)
                    mail_body = (
                        "A PO has been uploaded for job %s. File name is: %s"
                        % (job, request.FILES["file"].name)
                    )
                    general_funcs.send_info_mail(mail_subject, mail_body, mail_send_to)
            # Try/Except to catch other crap...
            except Exception:
                pass

            return HttpResponseRedirect(reverse("jb_db_doc_upload_complete"))
        else:
            return fileform.serialize_errors()
    else:
        fileform = FileUploadForm()

        pagevars = {
            "job": job,
            "fileform": fileform,
        }

        return render(
            request,
            "workflow/job/job_detail/popups/db_doc_upload.html",
            context=pagevars,
        )


@csrf_exempt
def item_summary(request, job_id, view):
    """Display all items associated with a job in given view."""
    job = Job.objects.get(id=job_id)
    itemsinjob = Item.objects.filter(job=job_id).order_by("num_in_job")
    overdue = job.overdue()

    pagevars = {
        "page_title": "Job Details: %d %s" % (job.id, job.name),
        "job": job,
        "view": view,
        "overdue": overdue,
        "itemsinjob": itemsinjob,
    }

    return render(
        request,
        "workflow/job/job_detail/middle/summary_" + view + ".html",
        context=pagevars,
    )


def bev_item_nomenclature(request, job_id):
    """Simply displays data in a certain formatted way for the Beverage analysts."""
    job = Job.objects.get(id=job_id)

    pagevars = {
        "page_title": "Job Details: %d %s" % (job.id, job.name),
        "job": job,
    }

    return render(
        request, "workflow/job/ajax/bev_all_nomenclature.html", context=pagevars
    )


def return_job_item_info(item_id):
    """Returns data for an item in a dictionary, for use with editing all items."""
    this_item = Item.objects.get(id=item_id)
    item_information = {
        "size": this_item.size,
        "plant": this_item.plant,
        "press": this_item.press,
        "quality": this_item.quality,
    }

    return item_information


def job_item_json(request, job_id, null_char):
    item_list = Item.objects.filter(job=job_id)

    job_item_info = serializers.serialize(
        "json",
        item_list,
        ensure_ascii=False,
        fields=(
            "size",
            "plant",
            "press",
        ),
    )

    pagevars = {
        "job_item_info": job_item_info,
    }
    return render(request, "workflow/job/ajax/job_item_json.html", context=pagevars)


@csrf_exempt
def shipping_manager(request, job_id):
    """Manage shipping address associated with job."""
    jobaddresses = JobAddress.objects.filter(job=job_id).order_by("name")

    pagevars = {
        "addresses": jobaddresses,
        "job_id": job_id,
    }
    return render(
        request, "workflow/job/job_detail/lower/shipmgr.html", context=pagevars
    )


class JobAddressForm(ModelForm, JSONErrorForm):
    """Job Address management form."""

    class Meta:
        model = JobAddress
        fields = "__all__"


class CartJobAddressForm(ModelForm, JSONErrorForm):
    """Just like JobAddressForm but the job field is set to optional since we want
    the user to enter an address and a job at the same time. We just need
    to be sure we manually set the job before we save the form.
    """

    def __init__(self, *args, **kwargs):
        super(CartJobAddressForm, self).__init__(*args, **kwargs)
        # Making job optional
        self.fields["job"].required = False
        self.fields["title"].widget.attrs["placeHolder"] = "(Not Required)"
        self.fields["address2"].widget.attrs["placeHolder"] = "(Not Required)"
        self.fields["ext"].widget.attrs["placeHolder"] = "(Not Required)"
        self.fields["email"].widget.attrs["placeHolder"] = "(Not Required)"
        self.fields["cell_phone"].widget.attrs["placeHolder"] = "(Not Required)"

    class Meta:
        model = JobAddress
        fields = "__all__"


def add_job_address(request, job_id):
    """Add a new address attached to the Job."""
    if request.POST:
        form = JobAddressForm(request.POST)
        if form.is_valid():
            data = form
            data.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            return form.serialize_errors()
    else:
        job = Job.objects.get(id=job_id)
        jobaddressform = JobAddressForm()

        pagevars = {
            "jobaddressform": jobaddressform,
            "job": job,
        }

        return render(
            request,
            "workflow/job/job_detail/lower/shipmgr_add_address.html",
            context=pagevars,
        )


def edit_job_address(request, address_id):
    """Saves the edits of an address attached to a Job."""
    if request.POST:
        address = JobAddress.objects.get(id=address_id)
        form = JobAddressForm(request.POST, instance=address)
        if form.is_valid():
            data = form
            data.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            return form.serialize_errors()
    else:
        address = JobAddress.objects.get(id=address_id)
        jobaddressform = JobAddressForm(instance=address)

        pagevars = {
            "jobaddressform": jobaddressform,
            "address": address,
        }

    return render(
        request,
        "workflow/job/job_detail/lower/shipmgr_edit_address.html",
        context=pagevars,
    )


def delete_job_address(request, address_id):
    """Deletes an address attached to a Job."""
    address = JobAddress.objects.get(id=address_id)
    address.delete()
    return HttpResponse(JSMessage("Deleted."))


def attach_address_to_job(request):
    """TODO: Document this"""
    form = JobAddressForm(request.POST)
    # If a job number was entered, check to make sure it is a real job.
    if "job" in request.POST:
        job_id = request.POST["job"]
        job = Job.objects.get(id=job_id)
        form.job = job.id
        if form.is_valid():
            form.save()
            return HttpResponse(JSMessage(job_id))
        else:
            return form.serialize_errors()

    else:
        return HttpResponse(JSMessage("Job number not given."))


def copy_jobaddress_to_contacts(request, address_id):
    """Copy JobAddress entry to public Contacts list."""
    try:
        jobaddress = JobAddress.objects.get(id=address_id)
        jobaddress.copy_to_contacts()
        return HttpResponse(JSMessage("Address copied to Directory."))
    except Exception:
        return HttpResponse(JSMessage("An error has occured."))


class DupeFSBJobForm(ModelForm):
    """Form used for adding a job - Foodservice"""

    name = forms.CharField(widget=forms.TextInput(attrs={"size": "30"}), required=True)
    due_date = forms.DateField(
        widget=GCH_SelectDateWidget, initial=date.today() + timedelta(days=1)
    )
    # customer_name = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}), required=True)
    workflow = _safe_get_site("Foodservice")
    instructions = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "10"}), required=False
    )
    # Select users who are a member of the set of groups with the given permission.
    grouped_sales_users = (
        User.objects.filter(groups__in=SALES_PERMISSION.group_set.all())
        .order_by("username")
        .distinct()
    )
    salesperson = forms.ModelChoiceField(
        queryset=grouped_sales_users.distinct(), required=False
    )

    def __init__(self, request, *args, **kwargs):
        super(DupeFSBJobForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields["due_date"] = forms.DateField(
                widget=GCH_SelectDateWidget, initial=date.today() + timedelta(days=1)
            )

    class Meta:
        model = Job
        fields = "__all__"


class DupeBevJobForm(ModelForm, JSONErrorForm):
    """Form used for adding a job - Beverage"""

    # Here we are checking to make sure that the due date is 5 days after today
    # to avoid a rush charge automatically, and making sure that day doesnt fall
    # on a weekend
    dueDay = date.today() + timedelta(days=5)
    day_check = dueDay.isoweekday()
    if day_check == 6:
        dueDay = dueDay + timedelta(days=2)
    if day_check == 7:
        dueDay = dueDay + timedelta(days=1)
    due_date = forms.DateField(widget=GCH_SelectDateWidget, initial=dueDay)
    customer_name = forms.CharField(required=True)
    brand_name = forms.CharField(required=True)
    workflow = _safe_get_site("Beverage")
    instructions = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "14"}), required=False
    )
    prepress_supplier = forms.ChoiceField(choices=app_defs.PREPRESS_SUPPLIERS)
    # Select users who are a member of the set of groups with the given permission.
    grouped_sales_users = (
        User.objects.filter(groups__in=SALES_PERMISSION.group_set.all())
        .order_by("username")
        .distinct()
    )
    salesperson = forms.ModelChoiceField(
        queryset=grouped_sales_users.distinct(), required=False
    )
    temp_printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(
            plant__workflow=workflow, active=True
        ).order_by("plant__name")
    )
    # There's an old unused cyber graphics platemaker that we've been asked to
    # hide from this field.
    temp_platepackage = forms.ModelChoiceField(
        queryset=PlatePackage.objects.filter(workflow=workflow, active=True)
        .order_by("platemaker__name")
        .exclude(platemaker__id=18)
    )

    def __init__(self, request, *args, **kwargs):
        super(DupeBevJobForm, self).__init__(*args, **kwargs)

        # Hide some stuff from Evergreen.
        if request.user.groups.filter(name="Evergreen Analyst"):
            self.fields["temp_printlocation"].queryset = self.fields[
                "temp_printlocation"
            ].queryset.exclude(press__name="BHS")
            self.fields[
                "prepress_supplier"
            ].choices = app_defs.PREPRESS_SUPPLIERS_EVERGREEN

    class Meta:
        model = Job
        fields = (
            "customer_name",
            "brand_name",
            "workflow",
            "prepress_supplier",
            "salesperson",
            "temp_printlocation",
            "temp_platepackage",
            "customer_po_number",
            "bill_to_type",
            "business_type",
            "sales_service_rep",
            "olmsted_po_number",
            "purchase_request_number",
            "use_new_bev_nomenclature",
        )


def duplicate_job(request, job_id, dupe_type):
    """Duplicates a job in the database, resetting certain fields depending on the
    type.

    Types:
    default = No special options.
    press_change = Options for creating a press change.
    carton_imp = Options for creating a carton imposition job form a prepess job.
    carton_prepress = Duplicates an existing carton prepress job.
    """
    # Pull original data to duplicate (Job, Item, JobAddress)
    # Ignore linked records for JobLog, QC, Charges, Revisions
    job_original = Job.objects.get(id=job_id)
    items_original = Item.objects.filter(job__id=job_id)

    if request.POST:
        """
        Duplicate old job, change fields as needed.
        Set common fields first.
        """
        if not request.POST["salesperson"]:
            return HttpResponse(
                JSMessage(
                    "Job duplication error - Salesperson field is required.",
                    is_error=True,
                )
            )
        # Set job to new variable, set recid to None, save
        job_new = job_original
        job_new.id = None
        job_new.archive_disc = ""
        job_new.e_tools_id = ""
        job_new.type = ""
        job_new.artist = None
        job_new.workflow = job_original.workflow
        if job_original.workflow.name == "Beverage":
            job_new.name = request.POST["brand_name"]
        else:
            job_new.name = request.POST["name"]
        job_new.status = "Pending"
        job_new.duplicated_from = Job.objects.get(id=job_id)
        job_new.duplication_type = dupe_type
        job_new.due_date = date(
            int(request.POST["due_date_year"]),
            int(request.POST["due_date_month"]),
            int(request.POST["due_date_day"]),
        )
        job_new.salesperson = User.objects.get(id=request.POST["salesperson"])
        if dupe_type == "carton_imp":
            job_new.carton_type = "Imposition"
        job_new.save()

        if (
            job_original.workflow.name == "Foodservice"
            or job_original.workflow.name == "Carton"
        ):
            """
            Foodservice/carton specific fields. In this case, copy all checked items.
            """
            # Create folder here for FSB and carton, needed to accomodate item folders.
            job_new.create_folder()
            # Keep a record of which old item creates which new item.
            old_to_new_items = {}
            new_to_old_items = {}

            for item in items_original:
                if "item_%s" % str(item.id) in request.POST:
                    old_item_id = item.id  # Used to copy item colors later.
                    old_itemnum = item.num_in_job
                    new_item = item
                    new_item.id = None
                    # Reset all date-related information.
                    if dupe_type == "press_change":
                        new_item.press_change = True
                        new_item.printlocation = None
                        new_item.platepackage = None
                    if dupe_type == "carton_prepress":
                        new_item.graphic_req_number = None
                        new_item.grn = None
                    new_item.preflight_date = None
                    new_item.plant_review_date = None
                    new_item.assignment_date = None
                    new_item.special_mfg = None
                    new_item.path_to_file = ""
                    new_item.overdue_exempt = False
                    new_item.file_out_exempt = False
                    new_item.job = job_new
                    new_item.save()
                    # Record new and old item ids so we can set steps_with once all items are duplicated.
                    old_to_new_items[old_item_id] = new_item.id
                    new_to_old_items[new_item.id] = old_item_id
                    new_item.fsb_nine_digit_date = new_item.creation_date
                    new_item.save()
                    new_item.create_folder()
                    # Copy items colors for carton items.
                    if job_new.workflow.name == "Carton":
                        old_itemcolors = ItemColor.objects.filter(item__id=old_item_id)
                        for itemcolor in old_itemcolors:
                            itemcolor.id = None
                            itemcolor.item = new_item
                            itemcolor.save()
                    # Copy some files for carton jobs.
                    if dupe_type == "carton_imp":
                        fs_api.copy_carton_imp_files(
                            job_id, old_itemnum, job_new.id, new_item.num_in_job
                        )
                    if dupe_type == "carton_imp" or dupe_type == "carton_prepress":
                        fs_api.copy_carton_diestruct(
                            job_id, job_new.id, item.one_up_die
                        )
            # Set steps_with for each item now that they're all copied.
            if dupe_type == "carton_imp" or dupe_type == "carton_prepress":
                duped_items = Item.objects.filter(job=job_new)
                for new_item in duped_items:
                    # Get the item this was duped from.
                    old_item = Item.objects.get(id=new_to_old_items.get(new_item.id))
                    # See if the old item stepped with anything.
                    if old_item.steps_with:
                        # See if a new item was created from that old steps_with item.
                        try:
                            new_stepped_item_id = old_to_new_items.get(
                                old_item.steps_with.id
                            )
                        except Exception:
                            new_stepped_item_id = None
                        # If so, have the decendants step with each other like their forebears
                        if new_stepped_item_id:
                            new_stepped_item_stepped = Item.objects.get(
                                id=new_stepped_item_id
                            )
                            new_item.steps_with = new_stepped_item_stepped
                            new_item.save()

        if job_original.workflow.name == "Beverage":
            """
            Beverage specific fields. At this time, items will not yet be duplicated.
            """
            form = DupeBevJobForm(request, request.POST)
            if form.is_valid():
                job_new.salesperson = User.objects.get(id=request.POST["salesperson"])
                job_new.customer_name = request.POST["customer_name"]
                job_new.brand_name = request.POST["brand_name"]
                job_new.name = request.POST["customer_name"]
                job_new.customer_po_number = request.POST["customer_po_number"]
                job_new.bill_to_type = request.POST["bill_to_type"]
                job_new.business_type = request.POST["business_type"]
                try:
                    job_new.sales_service_rep = SalesServiceRep.objects.get(
                        id=request.POST["sales_service_rep"]
                    )
                except ValueError:
                    pass
                job_new.prepress_supplier = request.POST["prepress_supplier"]
                job_new.temp_printlocation = PrintLocation.objects.get(
                    id=request.POST["temp_printlocation"]
                )
                job_new.temp_platepackage = PlatePackage.objects.get(
                    id=request.POST["temp_platepackage"]
                )
                # Build the new PO Number based on plant code and new job id.
                job_new.po_number = form.cleaned_data.get("po_number", None)
                # This is where new PO# are being auto generated ^^^^
                # update to be the current PO# (Currently being reused as the olmstead PO field)
                # may want to just hide and use another seperate field.
                job_new.olmsted_po_number = form.cleaned_data.get("po_number", None)
                job_new.purchase_request_number = form.cleaned_data.get(
                    "purchase_request_number", None
                )
                job_new.use_new_bev_nomenclature = form.cleaned_data.get(
                    "use_new_bev_nomenclature", False
                )
                job_new.save()
                # Create folders here for Beverage. Needs to be done after name
                # is assigned to customer name.
                job_new.create_folder()
            else:
                return form.serialize_errors()

        # Make note in the Job Log that this job was duplicated from an existing one.
        logtype = JOBLOG_TYPE_JOB_CREATED
        logtext = "Job duplicated from job number " + str(job_id) + "."
        job_new.do_create_joblog_entry(logtype, logtext)
        if "instructions" in request.POST:
            job_new.do_create_joblog_entry(
                JOBLOG_TYPE_NOTE, request.POST["instructions"]
            )

        # Copy addresses from old job.
        addresses_original = JobAddress.objects.filter(job__id=job_id)
        for address in addresses_original:
            new_address = address
            new_address.id = None
            new_address.job = job_new
            new_address.save()
        return HttpResponse(JSMessage(job_new.id))
    else:
        if (
            job_original.workflow.name == "Foodservice"
            or job_original.workflow.name == "Carton"
        ):
            jobform = DupeFSBJobForm(request, instance=job_original)
        if job_original.workflow.name == "Beverage":
            jobform = DupeBevJobForm(request, instance=job_original)

        if dupe_type == "press_change":
            dupe_type_name = "Press Change"
        elif dupe_type == "carton_imp":
            dupe_type_name = "Carton Imposition"
        elif dupe_type == "carton_prepress":
            dupe_type_name = "Carton Prepress"
        else:
            dupe_type_name = "None"

        pagevars = {
            "jobform": jobform,
            "job_original": job_original,
            "items_original": items_original,
            "dupe_type": dupe_type,
            "dupe_type_name": dupe_type_name,
        }

        return render(request, "workflow/job/duplicate_job.html", context=pagevars)


def reset_permissions(request, job_id):
    """Tell the file server to reset the permissions on a job folder."""
    job = Job.objects.get(id=job_id)
    job.reset_folder()
    return HttpResponse(JSMessage("Done."))
