"""Draw-Down"""

import os
import re
from datetime import date, timedelta

from django import forms
from django.contrib.auth.models import Permission, User
from django.core.mail import EmailMessage
from django.db.models import Q
from django.forms import ModelForm
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from gchub_db.apps.draw_down.models import Drawdown, DrawDownItem, DrawDownRequest
from gchub_db.apps.joblog.app_defs import JOBLOG_TYPE_NOTE
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models import Job, PrintLocation
from gchub_db.includes import fs_api
from gchub_db.includes.gold_json import JSMessage
from gchub_db.includes.widgets import GCH_SelectDateWidget

# These are cached once when the server is started to avoid future queries.
ARTIST_PERMISSION = Permission.objects.get(codename="in_artist_pulldown")
CLEMSON_ARTIST = (
    User.objects.filter(groups__in=ARTIST_PERMISSION.group_set.all())
    .order_by("username")
    .filter(is_active=True)
)

# Making a queryset for the PrintLocation
# This will only show the Plant + Press combinations used for Ink Drawdowns
PLANT = PrintLocation.objects.all()
# These are all plants and presses we want to include individually
PLANT_PRESS_QUERY = (
    Q(plant__name="Pittston")
    | Q(plant__name="Clarksville")
    | Q(plant__name="Kenton")
    | Q(plant__name="Shelbyville")
    | Q(plant__name="Visalia")
) & (
    Q(press__name="Vision")
    | Q(press__name="PMC")
    | Q(press__name="Uteco")
    | Q(press__name="FK")
    | Q(press__name="Unknown")
    | Q(press__name="Comco")
    | Q(press__name="Webtron")
    | Q(press__name="Kidder")
    | Q(press__name="In-Line")
)
# These are the specific plant / press combos we want to exclude from the possible combos above
PLANT_PRESS_EXCLUDE = (
    (Q(plant__name="Kenton") | Q(plant__name="Visalia")) & (Q(press__name="Kidder"))
    | (Q(plant__name="Kenton") & Q(press__name="In-Line"))
    | (Q(plant__name="Visalia") & Q(press__name="Kidder"))
    | (Q(plant__name="Visalia") & Q(press__name="Webtron"))
    | (Q(plant__name="Visalia") & Q(press__name="In-Line"))
)
PLANT_LIST = PLANT.filter(PLANT_PRESS_QUERY).exclude(PLANT_PRESS_EXCLUDE)

SUBSTRATE_CHOICES = (
    #    ('-----------', '-----------'),
    ("Poly 1/S", "Poly 1/S"),
    ("Poly 2/S", "Poly 2/S"),
    ("Kraft Cup Buddy", "Kraft Cup Buddy"),
    ("White Cup Buddy", "White Cup Buddy"),
    ("PLA 1/S", "PLA 1/S"),
    ("PLA 2/S", "PLA 2/S"),
    ("SDR", "SDR"),
    ("Clay Coated", "Clay Coated"),
    ("CRB", "CRB"),
)

PLANT_CHOICES = ()
for printLoc in PLANT_LIST:
    PLANT_CHOICES += (
        (
            printLoc.plant.name + " - " + printLoc.press.name,
            printLoc.plant.name + " - " + printLoc.press.name,
        ),
    )

# SUBSTRATE_CHOICES_2 = ['PLA 1/S', 'PLA 2/S', 'Kraft Cup Buddy', 'White Cup Buddy', 'Poly 1/S', 'Poly 2/S', 'SDR', 'Clay Coated']


class DrawDownRequestForm(ModelForm):
    """These are the attributes that will not change for each item request"""

    requested_by = forms.ModelChoiceField(queryset=CLEMSON_ARTIST)
    customer_name = forms.CharField()
    send_prints_to = forms.CharField(widget=forms.Textarea)
    comments = forms.CharField(widget=forms.Textarea, required=False)
    date_needed = forms.DateField(widget=GCH_SelectDateWidget)
    creation_date = forms.DateField(widget=GCH_SelectDateWidget)
    job_number = forms.IntegerField(min_value=1, max_value=99999, required=False)
    request_complete = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = DrawDownRequest
        fields = (
            "customer_name",
            "job_number",
            "date_needed",
            "requested_by",
            "comments",
            "creation_date",
            "request_complete",
            "send_prints_to",
        )


class DrawDownItemForm(ModelForm):
    """These attributes will be different for each requested item on the draw drown"""

    substrate = forms.ChoiceField(choices=SUBSTRATE_CHOICES)
    print_location = forms.ModelChoiceField(queryset=PLANT_LIST)
    colors_needed = forms.CharField(widget=forms.Textarea)
    item_number = forms.IntegerField(min_value=1, max_value=50, required=False)
    number_copies = forms.IntegerField(initial=1, min_value=1, max_value=100)
    artwork = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = DrawDownItem
        fields = (
            "substrate",
            "print_location",
            "colors_needed",
            "draw_down_request",
            "number_copies",
            "item_number",
            "artwork",
        )

    def __init__(self, *args, **kwargs):
        super(DrawDownItemForm, self).__init__(*args, **kwargs)
        self.fields["print_location"].widget.attrs["size"] = 11
        self.fields["print_location"].empty_label = None
        self.fields["substrate"].widget.attrs["size"] = 11


class DrawDownItemHomeFormSet(
    modelformset_factory(DrawDownItem, form=DrawDownItemForm, extra=1)
):
    def clean(self):
        super(DrawDownItemHomeFormSet, self).clean()

        for form in self.forms:
            if not form.has_changed():
                form.add_error("print_location", "print_location is a required field")
                form.add_error("substrate", "substrate is a required field")


class DrawDownItemEditFormSet(
    modelformset_factory(DrawDownItem, form=DrawDownItemForm, extra=0)
):
    def clean(self):
        super(DrawDownItemEditFormSet, self).clean()

        for form in self.forms:
            if not form.has_changed():
                form.add_error("print_location", "print_location is a required field")
                form.add_error("substrate", "substrate is a required field")


class DrawDownSearchForm(forms.Form):
    """Searches through the Drawdown forms to find if any match the criteria"""

    job_number = forms.IntegerField(min_value=1, max_value=99999, required=False)
    customer_name = forms.CharField(required=False)
    requested_by = forms.ModelChoiceField(queryset=CLEMSON_ARTIST, required=False)
    print_location = forms.ModelChoiceField(queryset=PLANT_LIST, required=False)
    date_in_start = forms.DateField(widget=GCH_SelectDateWidget, required=False)
    date_in_end = forms.DateField(widget=GCH_SelectDateWidget, required=False)
    date_needed_start = forms.DateField(widget=GCH_SelectDateWidget, required=False)
    date_needed_end = forms.DateField(widget=GCH_SelectDateWidget, required=False)

    def __init__(self, request, *args, **kwargs):
        """Populate some of the relational fields."""
        super(DrawDownSearchForm, self).__init__(*args, **kwargs)

    def clean(self):
        if any(self.errors):
            return
        if not self.has_changed():
            raise forms.ValidationError("Please add at least one search criteria.")


def home(request, job_id=None):
    """New Drawdown add form, plus AJAX save of that form."""
    # drawdownItemFormSet = modelformset_factory(DrawDownItem, form=DrawDownItemForm, extra=1)

    if request.POST:
        ddform = DrawDownRequestForm(request.POST)
        # ddiformSet = drawdownItemFormSet(request.POST, queryset=DrawDownItem.objects.none(), prefix="Drawdown")
        ddiformSet = DrawDownItemHomeFormSet(request.POST, prefix="Drawdown")
        flag = True
        # Check and see if we have any blank forms or bad forms
        for ddiform in ddiformSet:
            if not ddiform.is_valid():
                try:
                    # this checks for bad forms, if it is not valid but has the number_copies field then it
                    # just needs some data entered
                    num_copies = ddiform.cleaned_data["number_copies"]
                    flag = False
                except Exception:
                    # If the whole number_copies field is missing, this is a blank form
                    print("This Form set contains a blank")
        if ddform.is_valid() and flag:
            drawdown = ddform.save()
            for ddiform in ddiformSet:
                try:
                    num_copies = ddiform.cleaned_data["number_copies"]
                    drawdownitem = ddiform.save()
                    drawdownitem.draw_down_request = drawdown
                    drawdownitem.save()
                except Exception:
                    print("Skipping the blank form")

            # Grabs the last Drawdown object
            drawdownReq = DrawDownRequest.objects.all().order_by("-id")[0]
            drawdownItems = DrawDownItem.objects.filter(draw_down_request=drawdownReq)

            if drawdownReq.job_number:
                try:
                    job = Job.objects.get(id=drawdownReq.job_number)
                except Exception:
                    job = None
            else:
                job = None

            # Send the email to all the active ink techs.
            mail_list = []

            group_members = User.objects.filter(groups__name="EmailDrawDowns")
            for member in group_members:
                mail_list.append(member.email)

            mail_subject = "New Drawdown Request from %s" % drawdownReq.requested_by

            mail_body = loader.get_template("emails/drawdown_entered.txt")
            mail_context = {
                "drawdownReq": drawdownReq,
                "drawdownItems": drawdownItems,
                "user": drawdownReq.requested_by,
                "job": job,
            }
            email = EmailMessage(
                mail_subject,
                mail_body.render(mail_context),
                drawdownReq.requested_by.email,
                mail_list,
            )

            # This part is just for attaching the artwork to the email so make sure we have a jobnum, itemnum, and
            # the artist thinks the artwork is available somewhere before we try and find it.
            removeFileArray = []
            if drawdownReq.job_number:
                jobnum = drawdownReq.job_number
                jobfolder = fs_api.get_job_folder(jobnum)
                folder = os.path.join(jobfolder, fs_api.JOBDIR["3_preview_art"])

                fileArray = []
                for drawdownItem in drawdownItems:
                    if drawdownItem.artwork and drawdownItem.item_number:
                        try:
                            itemnum = drawdownItem.item_number
                            pattern = re.compile(r"ap_(.*)_(%s)[.](pdf)$" % itemnum)
                            file = fs_api._generic_item_file_search(folder, pattern)
                            file2 = os.path.join(
                                folder, "testPreviewArt" + str(itemnum)
                            )
                            removeFileArray.append(file2)
                            os.system("convert " + file + " " + file2 + ".jpg")
                            os.system(
                                "convert "
                                + file2
                                + ".jpg -format JPG -quality 30 "
                                + file2
                                + ".pdf"
                            )
                            os.system("rm " + file2 + ".jpg")

                            # ATTACH THE ARTWORK IF THERE IS ANY
                            with open(file2 + ".pdf", "rb") as f:
                                fileData = f.read()
                            # Attach the file and specify type.
                            email.attach(
                                str(jobnum) + " - " + str(itemnum),
                                fileData,
                                "application/pdf",
                            )
                        except Exception as ex:
                            print((str(ex)))
                            pass

            # Poof goes the mail.
            email.send(fail_silently=False)

            for rmfile in removeFileArray:
                os.system("rm " + rmfile + ".pdf")

            if drawdownReq.job_number:
                try:
                    dd_job = Job.objects.get(id=drawdownReq.job_number)
                    note = JobLog()
                    note.job = dd_job
                    note.user = drawdownReq.requested_by
                    note.type = JOBLOG_TYPE_NOTE
                    note.log_text = "Drawdown Request Entered, Ink Dept. emailed"
                    note.save()
                except Exception:
                    pass

                return HttpResponse(JSMessage("Saved/Email Sent."))
            else:
                return HttpResponse(
                    JSMessage("Error has occurred sending the drawdown")
                )
        else:
            errorSet = ""
            for error in ddform.errors:
                errorSet += " - " + str(error)
            for error in ddiformSet.errors:
                for key, value in list(error.items()):
                    errorSet += " - " + str(key)
            return HttpResponse(
                JSMessage("Invalid value for field(s):" + errorSet, is_error=True)
            )
    else:
        user = request.user
        date_plus3 = date.today() + timedelta(days=3)
        if job_id:
            customer = Job.objects.get(id=job_id)
            drawDownObj = {
                "customer_name": customer.name,
                "job_number": job_id,
                "requested_by": user.id,
                "number_copies": 1,
                "date_needed": date_plus3,
                "creation_date": date.today(),
            }
        else:
            drawDownObj = {
                "job_number": "",
                "requested_by": user.id,
                "number_copies": 1,
                "date_needed": date_plus3,
                "creation_date": date.today(),
            }

        drawdownReqForm = DrawDownRequestForm(initial=drawDownObj)
        drawdownItemForm = DrawDownItemHomeFormSet(
            queryset=DrawDownItem.objects.none(), prefix="Drawdown"
        )

        pagevars = {
            "page_title": "Add New Drawdown Request",
            "drawdownReqform": drawdownReqForm,
            "drawdownItemForm": drawdownItemForm,
        }

        return render(request, "draw_down/home.html", context=pagevars)


def show(request):
    """Displays All Drawdown Requests"""
    drawdownReq = DrawDownRequest.objects.all().order_by("-id")

    pagevars = {
        "page_title": "All Drawdown Requests",
        "object_list": drawdownReq,
    }

    return render(request, "draw_down/show.html", context=pagevars)


def show_legacy(request):
    """Displays All Drawdown Requests"""
    drawdowns = Drawdown.objects.all().order_by("-id")
    pagevars = {
        "page_title": "Legacy Drawdown Requests",
        "search_number": drawdowns.count(),
        "object_list": drawdowns,
    }

    return render(request, "draw_down/show_legacy.html", context=pagevars)


def edit_drawdown(request, contact_id):
    """Saves edited Drawdown Request data."""
    current_data = DrawDownRequest.objects.get(id=contact_id)
    current_items = DrawDownItem.objects.filter(draw_down_request=current_data.id)

    if request.method == "POST":  # save form
        ddform = DrawDownRequestForm(request.POST, instance=current_data)
        ddiformSet = DrawDownItemEditFormSet(
            request.POST,
            queryset=DrawDownItem.objects.filter(draw_down_request=current_data.id),
        )
        if ddform.is_valid() and ddiformSet.is_valid():
            drawdown = ddform.save()
            for ddiform in ddiformSet:
                drawdownitem = ddiform.save()
                drawdownitem.draw_down_request = drawdown
                drawdownitem.save()

            return HttpResponse(JSMessage("Saved."))
        else:
            errorSet = ""
            for error in ddform.errors:
                errorSet += " - " + str(error)
            for error in ddiformSet.errors:
                for key, value in list(error.items()):
                    errorSet += " - " + str(key)
            return HttpResponse(
                JSMessage("Invalid value for field(s):" + errorSet, is_error=True)
            )
    else:  # present form
        drawdownReqForm = DrawDownRequestForm(instance=current_data)
        drawdownItemForm = DrawDownItemEditFormSet(
            queryset=DrawDownItem.objects.filter(draw_down_request=current_data.id)
        )
        pagevars = {
            "page_title": "Edit Drawdown Request",
            "drawdownReqform": drawdownReqForm,
            "drawdownItemForm": drawdownItemForm,
            "drawDownReqID": current_data.id,
        }

        return render(request, "draw_down/edit.html", context=pagevars)


def view_drawdown(request, contact_id):
    """View drawdown request and the drawdown items associated with the request.
    This is an attempt to make the legacy draw down system work with the new one, if the id cannot be found in the
    new system then it tries the legacy system and returns that object / builds the page the old way instead.
    """
    try:
        drawdownReq = DrawDownRequest.objects.get(id=contact_id)
        drawdownItem = DrawDownItem.objects.filter(draw_down_request=drawdownReq)

        pagevars = {
            "page_title": "Your Drawdown Request",
            "drawdownReq": drawdownReq,
            "drawdownItem": drawdownItem,
            "system": "new",
        }

    except Exception:
        drawdownreq = Drawdown.objects.get(id=contact_id)
        pagevars = {
            "page_title": "Your Drawdown Request",
            "contact": drawdownreq,
            "system": "old",
        }

    return render(request, "draw_down/view.html", context=pagevars)


def delete_drawdown(request, contact_id):
    """Delete a drawdown request from the Request Drawdown Forms as well as all of the drawdown items
    associated with that request.
    """
    drawdownrequest = DrawDownRequest.objects.get(id=contact_id)
    drawdownitems = DrawDownItem.objects.filter(draw_down_request=drawdownrequest.id)
    for drawdownitem in drawdownitems:
        drawdownitem.delete()
    drawdownrequest.delete()

    return HttpResponse(JSMessage("Deleted."))


def complete_drawdown(request, drawdown_id):
    """Mark a drawdown as complete."""
    user = request.user

    if user.has_perm("draw_down.change_drawdown"):
        drawdownrequest = DrawDownRequest.objects.get(id=drawdown_id)
        drawdownrequest.request_complete = True
        drawdownrequest.save()

        if drawdownrequest.job_number:
            note = JobLog()
            dd_job = Job.objects.get(id=drawdownrequest.job_number)
            note.job = dd_job
            note.user = user
            note.type = JOBLOG_TYPE_NOTE
            note.log_text = "Ink Drawdown Request Received, by %s." % user.username
            note.save()
        return HttpResponse(JSMessage("Drawdown Request has been completed."))
    return HttpResponse(JSMessage("You don't have rights to change the status."))


def pending_drawdown(request, drawdown_id):
    """Mark a completed drawdown as Pending..."""
    user = request.user

    if user.has_perm("draw_down.change_drawdown"):
        drawdownrequest = DrawDownRequest.objects.get(id=drawdown_id)
        drawdownrequest.request_complete = False
        drawdownrequest.save()
        return HttpResponse(JSMessage("Drawdown Request is now Pending."))
    return HttpResponse(JSMessage("You don't have rights to change the status."))


def drawdown_search_results(request, form=None):
    """Displays Drawdown search results.
    Filters through search request from results.
    """
    qset = DrawDownRequest.objects.all()

    if form:
        s_draw_num = form.cleaned_data.get("job_number", None)
        if s_draw_num:
            qset = qset.filter(job_number__icontains=s_draw_num)

        s_draw_name = form.cleaned_data.get("customer_name", None)
        if s_draw_name:
            search_words = s_draw_name.split(" ")
            q = Q()
            for word in search_words:
                q &= Q(customer_name__icontains=word)
            qset = qset.filter(q)

        s_draw_artist = form.cleaned_data.get("requested_by")
        if s_draw_artist:
            qset = qset.filter(requested_by=s_draw_artist)

        s_draw_press = form.cleaned_data.get("print_location")
        if s_draw_press:
            query_set = DrawDownItem.objects.filter(print_location=s_draw_press)
            reqArray = []
            for query in query_set:
                reqArray.append(query.draw_down_request.id)
            qset = qset.filter(id__in=reqArray)

        s_draw_date_in_start = form.cleaned_data.get("date_in_start", None)
        s_draw_date_in_end = form.cleaned_data.get("date_in_end", None)
        if s_draw_date_in_end:
            if s_draw_date_in_start:
                qset = qset.filter(
                    creation_date__range=(s_draw_date_in_start, s_draw_date_in_end)
                )
        elif s_draw_date_in_start:
            qset = qset.filter(creation_date=s_draw_date_in_start)

        s_draw_date_needed_start = form.cleaned_data.get("date_needed_start", None)
        s_draw_date_needed_end = form.cleaned_data.get("date_needed_end", None)
        if s_draw_date_needed_end:
            if s_draw_date_needed_start:
                qset = qset.filter(
                    date_needed__range=(
                        s_draw_date_needed_start,
                        s_draw_date_needed_end,
                    )
                )

        elif s_draw_date_needed_start:
            qset = qset.filter(creation_date=s_draw_date_needed_start)

    qset = qset.exclude(id=99999).order_by("-id")

    pagevars = {
        "page_title": "Drawdown Request Search Results",
        "type": "Drawdown",
        "search_number": qset.count(),
        "object_list": qset,
    }

    return render(request, "draw_down/search_results.html", context=pagevars)


def drawdown_search(request):
    """Displays the Drawdown search form."""
    form = DrawDownSearchForm(request, request.GET)

    if request.GET and form.is_valid():
        # Call the result view directly for display.
        return drawdown_search_results(request, form=form)
    else:
        # This is the search page to be re-displayed if there's a problem or no
        # POST data.
        pagevars = {
            "page_title": "Drawdown Request Search",
            "form": form,
            "type": "Drawdown",
        }
        return render(request, "draw_down/search_form.html", context=pagevars)
