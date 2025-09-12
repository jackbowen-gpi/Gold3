"""
Module gchub_db\apps\art_req\views.py
"""

import os
import shutil
import json
from datetime import date, timedelta
from django.utils import timezone
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.forms import ModelForm, ModelChoiceField
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from gchub_db.apps.address.models import Contact
from gchub_db.apps.art_req.models import (
    PartialArtReq,
    ArtReq,
    ExtraProof,
    Product,
    AdditionalInfo,
    MarketSegment,
    CORRUGATED_TYPE_CHOICES,
)
from gchub_db.apps.qad_data.models import QAD_PrintGroups, QAD_CasePacks
from gchub_db.apps.workflow.models import (
    Job,
    Item,
    JobAddress,
    ItemTracker,
    ItemTrackerType,
    Charge,
    ChargeType,
)
from gchub_db.apps.workflow.models.general import ItemCatalog
from gchub_db.apps.workflow.views.job_views import CSR_PERMISSION
from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.includes import general_funcs, fs_api
from gchub_db.middleware import threadlocals
from gchub_db.includes.gold_json import JSMessage
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


# The following "Custom" classes let us change how choices are displayed.
class CustomPrintGroupChoice(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.description + "-" + obj.name


class CustomSalesRepChoice(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.first_name + " " + obj.last_name


class CustomCasePackChoice(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.case_pack


class NewArtReqForm(ModelForm):
    """Form used for adding a new art request."""

    # Use those custom choices we defined earlier.
    printgroup = CustomPrintGroupChoice(queryset=QAD_PrintGroups.objects.all().order_by("description"))
    sales_rep = CustomSalesRepChoice(
        queryset=User.objects.filter(is_active=True, groups__name="Salesperson")
        .exclude(groups__name="Evergreen Analyst")
        .order_by("last_name")
    )
    save_address = forms.BooleanField(label="", required=False, help_text="Save to address book")

    class Meta:
        model = ArtReq
        exclude = ("job_num", "corr_job_num", "created_by", "creation_date")

    def __init__(self, request, *args, **kwargs):
        super(NewArtReqForm, self).__init__(*args, **kwargs)
        self.fields["design_name"].label = "*Design Name"
        self.fields["design_name"].widget.attrs["size"] = 70
        self.fields["design_name"].widget.attrs["title"] = "This will be the name of the job in GOLD."
        self.fields["contact_name"].label = "*Contact Name"
        self.fields["contact_email"].label = "*Contact Email"
        self.fields["contact_email"].widget.attrs["size"] = 70
        self.fields["sales_rep"].label = "*Sales Rep"
        self.fields["csr"].label = "*CSR"
        self.fields["channel"].label = "*Channel"
        self.fields["print_type"].label = "*Print Type"
        self.fields["contact_name"].widget.attrs["size"] = 70
        self.fields["contact_name"].widget.attrs["title"] = "This will be the primary contact for the job."
        self.fields["ship_to_name"].label = "*Customer Name"
        self.fields["ship_to_name"].widget.attrs["size"] = 70
        self.fields["ship_to_company"].label = "Company"
        self.fields["ship_to_company"].widget.attrs["size"] = 70
        self.fields["ship_to_addy_1"].label = "*Address 1"
        self.fields["ship_to_addy_1"].widget.attrs["size"] = 70
        self.fields["ship_to_addy_2"].label = "Address 2"
        self.fields["ship_to_addy_2"].widget.attrs["size"] = 70
        self.fields["ship_to_city"].label = "*City"
        self.fields["ship_to_state"].label = "State"
        self.fields["ship_to_zip"].label = "Zip"
        self.fields["ship_to_country"].label = "Country"
        self.fields["ship_to_country"].initial = "USA"
        self.fields["ship_to_email"].label = "Email"
        self.fields["ship_to_email"].widget.attrs["size"] = 70
        self.fields["ship_to_phone"].label = "*Phone"
        self.fields["mkt_segment"].label = "*Market Segment"
        self.fields["design_name"].widget.attrs["size"] = 70
        self.fields["design_name"].widget.attrs["title"] = "This will be the name of the job in GOLD."
        self.fields["csr"].queryset = User.objects.filter(is_active=True, groups__in=CSR_PERMISSION.group_set.all()).order_by("last_name")
        self.fields["printgroup"].label = "*Printgroup"


class ExtraProofForm(ModelForm):
    """
    This is just used to change some of the field attributes in the
    ExtraProofFormSet genetrated by modelformset_factory.
    """

    save_address = forms.BooleanField(label="", required=False, help_text="Save to address book")

    def __init__(self, *args, **kwargs):
        super(ExtraProofForm, self).__init__(*args, **kwargs)
        self.fields["ship_to_name"].widget.attrs["size"] = 70
        self.fields["ship_to_company"].widget.attrs["size"] = 70
        self.fields["ship_to_addy_1"].widget.attrs["size"] = 70
        self.fields["ship_to_addy_2"].widget.attrs["size"] = 70
        self.fields["ship_to_email"].widget.attrs["size"] = 70


class ProductForm(ModelForm):
    """
    This is just used to change some of the field attributes in the
    CorrProductFormSet genetrated by modelformset_factory.
    """

    # Use those custom choices we defined earlier.
    case_pack = CustomCasePackChoice(required=False, queryset=QAD_CasePacks.objects.all())

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields["size"].label = "*Size"
        self.fields["annual_usage"].label = "*Annual Usage (cases)"
        # We need to hide the IPFB choice since it's no longer used. It's the first choice so slice it out.
        self.fields["corr_type"].choices = CORRUGATED_TYPE_CHOICES[1:]
        self.fields["corr_only"].label = ""
        self.fields["corr_only"].help_text = "Corrugated Only"
        self.fields["corr_only"].widget.attrs["title"] = (
            "Check this if you just want a corrugated (KD) job created in GOLD. No cup job will be created."
        )
        self.fields["customer_number"].widget.attrs["title"] = "Customer specific numbers like WRIN#, GIN#, SKU#, etc."
        self.fields["plant1"].label = "Plant/Press"
        self.fields["plant1"].widget.attrs["title"] = "Plant 1"
        self.fields["plant2"].label = ""
        self.fields["plant2"].widget.attrs["title"] = "Plant 2"
        self.fields["plant3"].label = ""
        self.fields["plant3"].widget.attrs["title"] = "Plant 3"
        self.fields["ink_jet_promo"].label = "Ink Jet Promo"
        self.fields["label_promo"].label = "Label Promo"
        self.fields["corr_plant1"].label = "Corrugated Plant(s)"
        self.fields["press1"].widget.attrs["title"] = "Press 1"
        self.fields["press2"].widget.attrs["title"] = "Press 2"
        self.fields["press3"].widget.attrs["title"] = "Press 3"
        self.fields["case_pack"].queryset = QAD_CasePacks.objects.filter(active=True).order_by("size", "case_pack")
        self.fields["size"].queryset = ItemCatalog.objects.filter(workflow__name="Foodservice", active="True").exclude(size__contains=" KD")


class AdditionalInfoForm(ModelForm):
    """Form used for adding products to an existing art request."""

    class Meta:
        model = AdditionalInfo
        exclude = ("artreq",)

    def __init__(self, request, *args, **kwargs):
        super(AdditionalInfoForm, self).__init__(*args, **kwargs)
        self.fields["keep_same_upc"].help_text = "Keep same UPC"
        self.fields["keep_same_upc"].label = ""
        self.fields["replaces_prev_design"].help_text = "Replaces previous design (Requires previous 9-Digit #)"
        self.fields["replaces_prev_design"].label = ""
        self.fields["prev_9_digit"].widget = forms.Textarea(attrs={"cols": 15, "rows": 3})
        self.fields["prev_9_digit"].help_text = "(Separate multiples with comma.)"
        self.fields["incoming_art_format"].label = "Incoming Art Format"
        self.fields["arrival_date"].label = "Arrival Date"
        self.fields["sender"].label = "Sender"
        self.fields["date_needed"].label = "Date Needed"
        due_date = date.today() + timedelta(days=14)
        self.fields["date_needed"].initial = due_date.strftime("%m/%d/%Y")
        self.fields["special_instructions"].label = "Special Instructions"
        self.fields["forecast"].label = "*Forecast"

    def clean(self):
        """
        Used for custom validation. We currently check the following:
        -Make sure the date needed isn't on the weekend.
        -Make the previous 9 digit required if replaces previous design is checked.
        """
        # Gather the data we intend to check
        cleaned_data = self.cleaned_data
        replaces_prev_design = cleaned_data.get("replaces_prev_design")
        prev_9_digit = cleaned_data.get("prev_9_digit")
        date_needed = cleaned_data.get("date_needed")
        # Check if replaces previous design is true.
        if replaces_prev_design and not prev_9_digit:
            msg_design = "Required when replacing a previous design."
            self._errors["prev_9_digit"] = self.error_class([msg_design])
        # Check if date needed is a weekday.
        if date_needed:
            if date_needed.weekday() >= 5:
                msg_date = "Please choose a weekday."
                self._errors["date_needed"] = self.error_class([msg_date])
        # Always return the full collection of cleaned data.
        return cleaned_data


class ArtReqFileForm(forms.Form):
    """This is to gather uploads into their own formset"""

    file = forms.FileField(required=False)


def ShowFiles(artreq_id):
    """
    Shows any files uploaded by an Art request. If there's a job folder it
    looks there. If there's not a job folder it looks in ARTREQFILES_DIR which
    is where files are held until a job folder is created.
    """
    artreq = ArtReq.objects.get(id=artreq_id)

    # If there's a job number look in the job folder.
    if artreq.job_num:
        jobfolder_path = fs_api.get_job_folder(artreq.job_num) + "/Reference_Files/"
        path = os.path.join(jobfolder_path, "ArtRequest_%s") % artreq_id

    # If there's not a job folder look in ARTREQFILES_DIR
    else:
        path = os.path.join(settings.ARTREQFILES_DIR, "ArtRequest_%s") % artreq.id

    try:
        files = os.listdir(path)
    except Exception:
        files = ["No files."]

    return files


@login_required
def art_req_delete(request, temp_id):
    """
    This will delete a partial art_request which will remove it from the pending list
    for each user
    """
    try:
        partialartreq = PartialArtReq.objects.get(id=temp_id)
        partialartreq.delete()
    except Exception:
        pass

    return HttpResponseRedirect("/art_req/home/")


@login_required
def art_req_home(request):
    reqs = PartialArtReq.objects.filter(created_by=threadlocals.get_current_user(), is_completed=False)

    pagevars = {
        "page_title": "Art Requests Home",
        "user": threadlocals.get_current_user(),
        "user_reqs": reqs,
    }

    return render(request, "art_req/home.html", context=pagevars)


@login_required
def art_req_add(request, artreq_id=None, new_artreq_id=None):
    """
    Form and save function for creating new art requests. If an artreq_id
    is passed then the view will be used to edit an existing art request. If
    a new_artreq_id is passed then the user just finished creating a new art
    request and will be shown a success message at the top of the screen along
    with a link to their newly created job.
    """
    # Check for an artreq id to see if we're editing an existing record or not.
    if artreq_id:  # We're editing an existing art request. Gather it all up.
        print(("Editing artreq number %s" % artreq_id))
        try:
            # make sure that this art req doesnt try and create a new partial if it is saved during edit
            # so check and make sure it didnt come from a partial already, if it did then prime the variable
            partialArt = PartialArtReq.objects.get(artReq=artreq_id)
            partial_id = partialArt.id
        except Exception:
            pass
        artreq = ArtReq.objects.get(id=artreq_id)
        extra_proofs = ExtraProof.objects.filter(artreq=artreq)
        products = Product.objects.filter(artreq=artreq).order_by("id")
        info = AdditionalInfo.objects.get(artreq=artreq)
        filelist = ShowFiles(artreq_id)
    else:  # It's a new blank form. Just leave the instances blank.
        artreq = None
        extra_proofs = ExtraProof.objects.none()
        products = Product.objects.none()
        info = None
        filelist = None

    # Determine how many blank forms are shown for proofs.
    if extra_proofs:
        # No blank form needed if editing existing extra proof.
        blank_proofs_forms = 0
    else:
        blank_proofs_forms = 1

    if products:
        # No blank form needed if editing existing product.
        pass
    else:
        pass
    # Build our formsets.
    ExtraProofFormSet = modelformset_factory(ExtraProof, form=ExtraProofForm, exclude=("artreq",), extra=blank_proofs_forms)
    ProductFormSet = modelformset_factory(Product, form=ProductForm, exclude=("artreq",), min_num=1, extra=0)
    ArtReqFileFormSet = formset_factory(ArtReqFileForm, extra=1)

    # Normal form stuff starts
    if request.POST:
        if "form_submit" in request.POST:
            artreqform = NewArtReqForm(request, request.POST, instance=artreq)
            extraproofformset = ExtraProofFormSet(request.POST, queryset=extra_proofs, prefix="Proof")
            productformset = ProductFormSet(request.POST, queryset=products, prefix="Product")
            infoform = AdditionalInfoForm(request, request.POST, instance=info)
            fileformset = ArtReqFileFormSet(request.POST, request.FILES, prefix="ArtReqFiles")

            # Validate the form data and save.
            if (
                artreqform.is_valid()
                and extraproofformset.is_valid()
                and productformset.is_valid()
                and infoform.is_valid()
                and fileformset.is_valid()
            ):
                print("Saving and processing form.")
                # Make the art request.
                new_artreq = artreqform.save(commit=False)
                # Save this address to contacts?
                try:
                    if request.POST.get("save_address"):
                        print("Saving address.")
                        contact = Contact()
                        contact.first_name = new_artreq.ship_to_name.split(" ")[0]
                        contact.last_name = new_artreq.ship_to_name.split(" ")[1]
                        contact.company = new_artreq.ship_to_company
                        contact.address1 = new_artreq.ship_to_addy_1
                        contact.address2 = new_artreq.ship_to_addy_2
                        contact.city = new_artreq.ship_to_city
                        contact.state = new_artreq.ship_to_state
                        contact.zip_code = new_artreq.ship_to_zip
                        contact.country = new_artreq.ship_to_country
                        contact.phone = new_artreq.ship_to_phone
                        contact.email = new_artreq.ship_to_email
                        contact.save()
                except Exception:
                    print("Problem saving address")
                new_artreq.created_by = threadlocals.get_current_user()
                new_artreq = artreqform.save()
                print("Making artreq.")
                # Make the extra proof objects.
                new_extraproofformset = extraproofformset.save(commit=False)
                counter = 0
                for form in new_extraproofformset:
                    print("Making extra proofs.")
                    form.artreq = new_artreq
                    # Save this address to contacts?
                    try:
                        if request.POST.get("Proof-%s-save_address" % counter):
                            print(("Saving address %s." % counter))
                            contact = Contact()
                            contact.first_name = form.ship_to_name.split(" ")[0]
                            contact.last_name = form.ship_to_name.split(" ")[1]
                            contact.company = form.ship_to_company
                            contact.address1 = form.ship_to_addy_1
                            contact.address2 = form.ship_to_addy_2
                            contact.city = form.ship_to_city
                            contact.state = form.ship_to_state
                            contact.zip_code = form.ship_to_zip
                            contact.country = form.ship_to_country
                            contact.phone = form.ship_to_phone
                            contact.email = form.ship_to_email
                            contact.save()
                            counter += 1
                    except Exception:
                        print("Problem saving address")
                    form.save()
                # Make the product objects.
                new_productformset = productformset.save(commit=False)
                for form in new_productformset:
                    print("Making product.")
                    form.artreq = new_artreq
                    form.save()

                # Process uploaded files

                for fileform in fileformset.cleaned_data:
                    if fileform:
                        # Designate temporary upload path and file name
                        path = os.path.join(settings.ARTREQFILES_DIR, "ArtRequest_%s") % new_artreq.id
                        if not os.path.exists(path):
                            os.makedirs(path)
                        destination = open(os.path.join(path, fileform["file"].name), "wb+")
                        # Write file to folder
                        for chunk in fileform["file"]:
                            destination.write(chunk)
                        destination.close()

                # Make the additional info object
                new_info = infoform.save(commit=False)
                new_info.artreq = new_artreq
                new_info.save()
                print("Making extra info.")

                # Art Request complete. Send them to the review page to finish up.
                # Add True to the URL so the submit buttons and info box will show up.
                partial_id = request.POST.get("partial", "None")
                if partial_id == "":
                    partial_id = "None"
                try:
                    # Saving artreq reference to the partial so that if the artreq is edited and saved
                    # it wont create a new partial, but reference the old one
                    partialArt = PartialArtReq.objects.get(id=partial_id)
                    partialArt.artReq = new_artreq
                    partialArt.save()
                except Exception:
                    pass
                return HttpResponseRedirect("/art_req/review/%s/%s/True/" % (new_artreq.id, partial_id))
            else:
                print("Form validation error.")

        elif "form_save" in request.POST:
            str = json.dumps(request.POST)
            fileStr = json.dumps(request.FILES)
            partial_id = request.POST.get("partial", "None")
            design_name = request.POST.get("design_name", "None")
            if design_name == "None" or design_name == "":
                message = "Design Name is required for saving."
                return HttpResponse(JSMessage(message, is_error=True))
            else:
                if partial_id == "None" or partial_id == "":
                    partialArt = PartialArtReq()
                    partialArt.fieldData = str
                    partialArt.fieldFile = fileStr
                    partialArt.partial_name = request.POST.get("design_name")
                    partialArt.created_by = threadlocals.get_current_user()
                    partialArt.last_updated = timezone.now()
                    partialArt.save()
                    partial_id = partialArt.id
                else:
                    partialArt = PartialArtReq.objects.get(id=partial_id)
                    partialArt.fieldData = str
                    partialArt.fieldFile = fileStr
                    partialArt.partial_name = request.POST.get("design_name")
                    partialArt.last_updated = timezone.now()
                    partialArt.save()

            # return render(request, 'art_req/add.html', context={})
            message = "Saved!"
            return HttpResponse(JSMessage(message, is_error=False))

        elif "form_load" in request.POST:
            partial_id = request.POST.get("partial")
            partialArt = PartialArtReq.objects.get(id=partial_id)
            try:
                obj = json.loads(partialArt.fieldData)
            except Exception:
                obj = {}

            try:
                fileObj = json.loads(partialArt.fileData)
            except Exception:
                fileObj = {}

            artreq = None
            extra_proofs = ExtraProof.objects.none()
            products = Product.objects.none()
            info = None
            filelist = None

            # Build our formsets.
            ExtraProofFormSet = modelformset_factory(ExtraProof, form=ExtraProofForm, exclude=("artreq",), extra=0)
            ProductFormSet = modelformset_factory(Product, form=ProductForm, exclude=("artreq",), extra=0)
            ArtReqFileFormSet = formset_factory(ArtReqFileForm, extra=1)

            artreqform = NewArtReqForm(request, obj, instance=None)
            extraproofformset = ExtraProofFormSet(obj, queryset=None, prefix="Proof")
            productformset = ProductFormSet(obj, queryset=None, prefix="Product")
            infoform = AdditionalInfoForm(request, obj, instance=None)
            fileformset = ArtReqFileFormSet(obj, fileObj, prefix="ArtReqFiles")
        else:
            artreqform = NewArtReqForm(request, obj, instance=None)
            extraproofformset = ExtraProofFormSet(obj, queryset=None, prefix="Proof")
            productformset = ProductFormSet(obj, queryset=None, prefix="Product")
            infoform = AdditionalInfoForm(request, obj, instance=None)
            fileformset = ArtReqFileFormSet(obj, fileObj, prefix="ArtReqFiles")
            filelist = None

    else:  # Make all the forms and formsets to be filled out.
        artreqform = NewArtReqForm(request, instance=artreq)
        extraproofformset = ExtraProofFormSet(queryset=extra_proofs, prefix="Proof")
        productformset = ProductFormSet(queryset=products, prefix="Product")
        infoform = AdditionalInfoForm(request, instance=info)
        fileformset = ArtReqFileFormSet(prefix="ArtReqFiles")

    """
    Now gather up any newly created jobs so they can be linked to in the success
    message at the top of the add page. That's where the user will be re-directed
    back to once the request is complete.
    """
    if new_artreq_id:
        try:
            print("Gathering up newly created jobs for display at top of page.")
            artreq = ArtReq.objects.get(id=new_artreq_id)
            new_jobs = Job.objects.filter(Q(id=artreq.job_num) | Q(id=artreq.corr_job_num))
        except Exception:
            new_jobs = None
            print("No art req found. Can't display success message.")
    else:
        new_jobs = None

        # get all art requests that have not been created yet.

    reqs = PartialArtReq.objects.filter(created_by=threadlocals.get_current_user())

    try:
        partialArt = PartialArtReq.objects.get(id=partial_id)
    except Exception:
        partialArt = "None"

    pagevars = {
        "page_title": "Art Requests",
        "user": threadlocals.get_current_user(),
        "user_reqs": reqs,
        "currentArt": partialArt,
        "artreqform": artreqform,
        "extraproofformset": extraproofformset,
        "productformset": productformset,
        "infoform": infoform,
        "fileformset": fileformset,
        "filelist": filelist,
        "new_jobs": new_jobs,
    }

    return render(request, "art_req/add.html", context=pagevars)


@login_required
def art_req_review(request, artreq_id, temp_id=None, submit=False):
    """
    Serves up the art request review page. If submit is set to true the back
    and submit buttons will be shown at the bottom.
    """
    try:
        artreq = ArtReq.objects.get(id=artreq_id)
        extra_proofs = ExtraProof.objects.filter(artreq=artreq)
        products = Product.objects.filter(artreq=artreq).order_by("id")
        info = AdditionalInfo.objects.get(artreq=artreq)
        filelist = ShowFiles(artreq_id)

    except Exception:
        print("Something went wrong displaying the Art Req page.")
        artreq = None
        extra_proofs = None
        products = None
        info = None
        filelist = None

    try:
        partialArt = PartialArtReq.objects.get(id=temp_id)
    except Exception:
        partialArt = "None"

    pagevars = {
        "page_title": "Art Request Review",
        "artreq": artreq,
        "extra_proofs": extra_proofs,
        "currentArt": partialArt,
        "products": products,
        "info": info,
        "filelist": filelist,
        "submit": submit,
    }

    return render(request, "art_req/review.html", context=pagevars)


def art_req_process(request, artreq_id, temp_id):
    try:
        artreq = ArtReq.objects.get(id=artreq_id)
        job = create_new_job(artreq)
        info = AdditionalInfo.objects.get(artreq=artreq_id)
        if info.forecast == "promotional":
            # email the promotions list
            salespersonArr = job.salesperson.username.split("_")
            salesperson = salespersonArr[0] + " " + salespersonArr[1]
            mail_send_to = []
            group_members = User.objects.filter(groups__name="EmailArtReqPromotional", is_active=True)
            for user in group_members:
                mail_send_to.append(user.email)
            mail_from = "Gold - Clemson Support <%s>" % settings.EMAIL_SUPPORT
            mail_subject = "GOLD Alert: Promotional Job Created"
            mail_body = loader.get_template("emails/promotional_job.txt")
            mail_context = {"job": job, "salesperson": salesperson}
            # send the email
            msg = EmailMultiAlternatives(mail_subject, mail_body.render(mail_context), mail_from, mail_send_to)
            msg.content_subtype = "html"
            msg.send()
    except Exception as ex:
        print("Something went wrong with art_req_process() in the Art Req view.")
        print(str(ex))

    try:
        partialartreq = PartialArtReq.objects.get(id=temp_id)
        partialartreq.is_completed = True
        partialartreq.save()
    except Exception:
        pass

    return HttpResponseRedirect("/art_req/add/%s/" % artreq_id)


def mktseg_lookup(request, seg_id):
    """
    Returns market segment info via json. Used by the more info button next to
    the market segment selector in the art request form.
    """
    message = {"name": "", "description": ""}
    if request.is_ajax():
        segment = get_object_or_404(MarketSegment, id=seg_id)
        message["name"] = segment.name
        message["description"] = segment.description
    else:
        message = "Market segment lookup error."
    return HttpResponse(json.dumps(message), content_type="application/json")


def casepack_lookup(request, size_id):
    """
    Returns casepacks for a given size via json. Used to update the casepack
    list based on what size is selected in the art request form.
    """
    casepack_list = []
    if request.is_ajax():
        casepacks = QAD_CasePacks.objects.filter(size__id=size_id)
        for casepack in casepacks:
            casepack_list.append(casepack.id)
    else:
        casepack_list = "Case pack lookup error."
    return HttpResponse(json.dumps(casepack_list), content_type="application/json")


def address_autocomplete(request):
    """Checks GOLDs contacts for a match to the name passed in the request."""
    addresses = []
    if request.is_ajax():
        term = request.GET["term"]
        # Try to split the term at spaces to check first and last names separately.
        term1 = "False"
        term2 = "False"
        try:
            term1 = term.split(" ")[0]
            term2 = term.split(" ")[1]
        except Exception:
            pass
        contacts = Contact.objects.filter(
            Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(first_name__icontains=term1, last_name__icontains=term2)
        )
        for contact in contacts:
            name_string = contact.first_name + " " + contact.last_name
            address = {
                "name": name_string,
                "company": contact.company,
                "addy_1": contact.address1,
                "addy_2": contact.address2,
                "city": contact.city,
                "state": contact.state,
                "zip": contact.zip_code,
                "country": contact.country,
                "email": contact.email,
                "phone": contact.phone,
            }
            addresses.append(address)

    else:
        addresses = "Autocomplete error."
    return HttpResponse(json.dumps(addresses), content_type="application/json")


def create_new_job(artreq):
    """
    Creates a new GOLD job for a given art request. Also walks through creating
    the items, populating the shipping info and populating the joblog.
    """
    print("Creating job from %s." % artreq)
    info = AdditionalInfo.objects.get(artreq=artreq)

    job = Job()
    job.name = artreq.design_name
    job.workflow = Site.objects.get(name="Foodservice")
    job.due_date = info.date_needed
    # This is wrong    job.ship_to_state = artreq.ship_to_state
    job.art_rec_type = info.incoming_art_format
    job.customer_name = artreq.contact_name
    job.customer_email = artreq.contact_email
    job.customer_phone = artreq.ship_to_phone
    job.keep_upc = info.keep_same_upc
    job.printgroup = artreq.printgroup
    job.salesperson = artreq.sales_rep
    job.csr = artreq.csr
    """
    If all the products were check as corrugated only then there's no point in
    making a non-KD job. So let's check and see if there are any products that
    don't have that checked before we make a job to contain them.
    """
    non_corr_only_products = Product.objects.filter(artreq=artreq, corr_only=False).order_by("id")
    if non_corr_only_products:
        job.save()
        print("Job saved for %s." % artreq)
        job.create_folder()
        # Now that a job has been generated from this artreq let's record it's number.
        artreq.job_num = job.id
        artreq.save()
        # Populate the shipping and joblog information.
        populate_shipping(job, artreq)
        populate_joblog(job, artreq)
        # Create items for our newly created job.
        create_items(job, artreq)

    # Check for items with preprint corrugated specified. They get seperate jobs.
    corr_products = Product.objects.filter(artreq=artreq, corr_type="preprint").order_by("id")
    if corr_products:
        print("Making corrugated job.")
        # We can copy the job objects we just created by wiping the primary key
        # and saving it again.
        job.pk = None
        job.name += " KD"
        job.save()
        print("Corrugated job saved for %s." % artreq)
        job.create_folder()
        # Now that a corrugated job has been generated let's record it's number.
        artreq.corr_job_num = job.id
        artreq.save()
        # Populate the shipping and joblog information.
        populate_shipping(job, artreq)
        populate_joblog(job, artreq)
        # Create items for our newly created job. Set the corr_flag to true so
        # it will change the size to the KD version.
        create_items(job, artreq, corr_flag=True)

    if not non_corr_only_products and not corr_products:
        # No items found. Create an empty job anyway.
        job.save()
        print("Empty job saved for %s." % artreq)
        job.create_folder()
        # Now that a job has been generated from this artreq let's record it's number.
        artreq.job_num = job.id
        artreq.save()
        # Populate the shipping and joblog information.
        populate_shipping(job, artreq)
        populate_joblog(job, artreq)

    # Move accompanying file(s) to job's Reference_Files folder
    print("Attempting to move files")
    frompath = os.path.join(settings.ARTREQFILES_DIR, "ArtRequest_%s") % artreq.id
    if not os.path.exists(frompath):
        os.makedirs(frompath)
    if corr_products and not non_corr_only_products:
        topath = fs_api.get_job_folder(artreq.corr_job_num) + "/Reference_Files/"
    else:
        topath = fs_api.get_job_folder(artreq.job_num) + "/Reference_Files/"
    shutil.move(frompath, topath)
    print("File transfer complete")

    return job


def create_items(job, artreq, corr_flag=False):
    """
    Creates items for a given job using the products specified in an art request.
    As well as any ItemTrackers needed for new promotions.
    """
    print(("Creating items for %s from %s." % (job, artreq)))

    items_replacing_designs = []

    # Gather all the products specified in the art request.
    if corr_flag:
        products = Product.objects.filter(artreq=artreq, corr_type="preprint").order_by("id")
    else:
        products = Product.objects.filter(artreq=artreq, corr_only=False).order_by("id")
    # Grab the additional info object for this art request.
    info = AdditionalInfo.objects.get(artreq=artreq)

    # Go through the products and create an item for each.
    for product in products:
        print(("Making an item from product %s" % product))
        item = Item()
        item.job = job
        item.workflow = Site.objects.get(name="Foodservice")
        # If it's a corrugated item try to change the size to the KD version.
        if corr_flag:
            try:
                item.size = ItemCatalog.objects.get(size=product.size.size + " KD")
            except Exception:
                item.size = product.size
        else:
            item.size = product.size
        if info.prev_9_digit:
            item.replaces = info.prev_9_digit
        try:
            item.case_pack = product.case_pack.case_pack
        except Exception:
            print("No casepack info found.")
        item.annual_use = product.annual_usage
        item.quality = "B"
        item.render = product.render
        item.wrappable_proof = product.wrap_proof
        item.mock_up = product.mock_up
        item.wrin_number = product.customer_number

        # Check for corrugated info
        print("Item complete.")
        item.save()
        item.create_folder()

        # If it's a corrugated item add some specific charges.
        if corr_flag:
            charge_type = ChargeType.objects.get(type="PDF Proof")
            charge = Charge(item=item, description=charge_type, amount=charge_type.base_amount)
            charge.save()
            charge_type = ChargeType.objects.get(type="Prepress Package")
            charge = Charge(item=item, description=charge_type, amount=100)
            charge.save()

        # Check to see if this item is replacing a previous design.
        try:
            if info.replaces_prev_design or info.prev_9_digit:
                print("Setting up replaces prev design email.")
                items_replacing_designs.append(item)
        except Exception:
            print("Something went wrong setting up the replacement emails.")
            pass
        if product.ink_jet_promo:
            new_tracker = ItemTracker()
            new_tracker.item = item
            new_tracker.type = ItemTrackerType.objects.get(id=12)
            new_tracker.addition_date = date.today()
            new_tracker.edited_by = threadlocals.get_current_user()
            new_tracker.save()
        if product.label_promo:
            new_tracker = ItemTracker()
            new_tracker.item = item
            new_tracker.type = ItemTrackerType.objects.get(id=13)
            new_tracker.addition_date = date.today()
            new_tracker.edited_by = threadlocals.get_current_user()
            new_tracker.save()
    # Send item replacement notification email (if applicable).
    print("Attempting to send replaces prev design email.")
    send_item_replaces_email(items_replacing_designs, job)


def populate_shipping(job, artreq):
    """Populates shipping info to a job from an art request."""
    try:
        print(("Populating primary shipping for %s from %s." % (job, artreq)))
        # Create a job address for the primary contact.
        address = JobAddress()
        address.job = job
        address.name = artreq.ship_to_name
        address.company = artreq.ship_to_company
        address.address1 = artreq.ship_to_addy_1
        address.address2 = artreq.ship_to_addy_2
        address.city = artreq.ship_to_city
        address.state = artreq.ship_to_state
        address.zip = artreq.ship_to_zip
        address.country = artreq.ship_to_country
        address.phone = artreq.ship_to_phone
        address.email = artreq.ship_to_email
        address.save()
    except Exception:
        print("Error populate_shipping main contact.")

    # Check for extra proofs and create addresses for them too.
    try:
        print(("Populating extra proof shipping for %s from %s." % (job, artreq)))
        extra_proofs = ExtraProof.objects.filter(artreq=artreq)
        if extra_proofs:
            for proof in extra_proofs:
                address = JobAddress()
                address.job = job
                address.name = proof.ship_to_name
                address.company = proof.ship_to_company
                address.address1 = proof.ship_to_addy_1
                address.address2 = proof.ship_to_addy_2
                address.city = proof.ship_to_city
                address.state = proof.ship_to_state
                address.zip = proof.ship_to_zip
                address.country = proof.ship_to_country
                address.phone = proof.ship_to_phone
                address.email = proof.ship_to_email
                address.save()
    except Exception:
        print("Error populate_shipping extra proofs.")


def populate_joblog(job, artreq):
    """Create JobLog entries after the Job object has been saved."""
    try:
        print(("Populating joblog for %s from %s." % (job, artreq)))
        # Grab the additional info object for this art request.
        info = AdditionalInfo.objects.get(artreq=artreq)

        # Create joblog entries in the job from the following info.
        if info.special_instructions:
            job.do_create_joblog_entry(
                joblog_defs.JOBLOG_TYPE_NOTE,
                info.special_instructions,
                user_override=artreq.created_by,
                is_editable=False,
            )
    except Exception:
        print(("Error populating joblog for %s from %s." % (job, artreq)))


def send_item_replaces_email(items_replacing_designs, job):
    """Sends an email to certain people when a new item replaces a previous design."""
    if items_replacing_designs:
        mail_subject = "Design Replaced: %s" % job
        mail_body = loader.get_template("emails/etools_replaces_design.txt")
        mail_context = {"items": items_replacing_designs, "job": job}
        mail_send_to = [settings.EMAIL_GCHUB]
        group_members = User.objects.filter(groups__name="EmailGCHubNewItems", is_active=True)
        for user in group_members:
            mail_send_to.append(user.email)
        general_funcs.send_info_mail(mail_subject, mail_body.render(mail_context), mail_send_to)
        print("Notification e-mail sent.")
