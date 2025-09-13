"""Auto-Corrugated Views"""

import os
import io
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.list import ListView
from django import forms
from django.forms import (
    ModelForm,
    ModelChoiceField,
    ChoiceField,
    IntegerField,
    TextInput,
    BooleanField,
    CharField,
)
from django.forms.formsets import formset_factory
from gchub_db.middleware import threadlocals
from gchub_db.includes.gold_json import JSMessage
from gchub_db.includes.form_utils import JSONErrorForm
from gchub_db.includes import general_funcs, fs_api
from gchub_db.apps.auto_corrugated.models import (
    GeneratedBox,
    BoxItem,
    BoxItemSpec,
    GeneratedLabel,
)
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.joblog.app_defs import JOBLOG_TYPE_NOTE
from gchub_db.apps.workflow.models import Plant, PlatePackage, Job
from gchub_db.apps.auto_corrugated.elements.fsb_elements import (
    barcodeFileExists,
    triggerBarcodeCreation,
)
import threading
import time

CASE_COLOR_CHOICE = (
    ("-----------", "-----------"),
    ("Kraft", "Kraft"),
    ("White", "White"),
)


class GeneratedBoxForm(ModelForm, JSONErrorForm):
    #    dummy_data = BooleanField()

    # We want this to be empty when the page is first loaded.
    six_digit_num = IntegerField(widget=TextInput(attrs={"maxlength": "6", "size": "6"}))
    replaced_6digit = IntegerField(required=False, widget=TextInput(attrs={"maxlength": "6", "size": "6"}))
    nine_digit_num = IntegerField(widget=TextInput(attrs={"maxlength": "9", "size": "9"}))
    fourteen_digit_num = IntegerField(widget=TextInput(attrs={"maxlength": "14", "size": "14"}))

    case_color = ChoiceField(choices=CASE_COLOR_CHOICE)

    plate_number = CharField(required=False)

    class Meta:
        model = GeneratedBox
        fields = (
            "pdf_type",
            "six_digit_num",
            "replaced_6digit",
            "nine_digit_num",
            "fourteen_digit_num",
            "plant",
            "item",
            "spec",
            "dim_length",
            "dim_width",
            "dim_height",
            "sleeve_count",
            "box_format",
            "text_line_1",
            "text_line_2",
            "board_spec",
            "case_color",
            #                  'sfi_stamp_cup', 'make_slugs', 'platepackage')
            # Hiding make_slugs for the time being.
            #                  'make_slugs',
            "platepackage",
            "plate_number",
        )

    def __init__(self, *args, **kwargs):
        """Populate some of the fields."""
        super(GeneratedBoxForm, self).__init__(*args, **kwargs)
        default_platemaker = PlatePackage.objects.get(platetype="Corrugate", platemaker__name="Shelbyville")
        self.fields["platepackage"] = ModelChoiceField(
            queryset=PlatePackage.objects.filter(platetype="Corrugate"),
            empty_label="None/Outsourced",
            initial=default_platemaker.id,
            required=False,
        )
        self.fields["pdf_type"].label = "Select a PDF Type"
        self.fields["spec"].label = "Case Pack"
        self.fields["item"].queryset = boxitems_with_specs()
        self.fields["item"].help_text = (
            "Contact Megan Varone if the size you need is unavailable (%s)"
            % User.objects.get(first_name="Megan", last_name="Varone").email
        )
        #        self.fields["make_slugs"].label = "Create Slugs"
        self.fields["platepackage"].label = "Platemaking"
        self.fields[
            "platepackage"
        ].help_text = "If no platemaker is chosen, the job will file out on approval. Clemson will not make TIFFs."
        self.fields["dim_length"].help_text = "(Outer Dimensions)"
        self.fields["dim_width"].help_text = "(Outer Dimensions)"
        self.fields["dim_height"].help_text = "(Outer Dimensions)"
        # self.fields["make_slugs"].help_text = "(Do not check if platemaking is being outsourced.)"

    def clean_six_digit_num(self):
        """Check that the six_digit_num field has the correct number of digits."""
        data = self.cleaned_data["six_digit_num"]
        if data > 999999:
            raise forms.ValidationError("The six digit number has more than 6 digits!")
        elif data < 100000:
            raise forms.ValidationError("The six digit number is not long enough!")
        return data

    def clean_nine_digit_num(self):
        """Check that the nine_digit_num field has the correct number of digits."""
        data = self.cleaned_data["nine_digit_num"]
        if data > 999999999:
            raise forms.ValidationError("The nine digit number has more than 9 digits!")
        elif data < 100000000:
            raise forms.ValidationError("The nine digit number is not long enough!")
        return data

    def clean_fourteen_digit_num(self):
        """Check that the fourteen_digit_num field has the correct number of digits."""
        data = self.cleaned_data["fourteen_digit_num"]
        # 0 is the dummy number we created if the 14-digit is not given.
        if data == 0:
            pass
        elif data > 99999999999999:
            raise forms.ValidationError("The fourteen digit (SCC) number has more than 14 digits!")
        elif data < 10000000000000:
            raise forms.ValidationError("The fourteen digit (SCC) number is not long enough!")
        return data


def boxitems_with_specs():
    # Gather all the box items
    bitems = BoxItem.objects.all()
    # Create a blank list for the box items that have item specs.
    bitems_w_specs = []
    # Iterate through the box items and check them for box item specs.
    for bitem in bitems:
        specs = []
        # Gather all the box item specs that fk to this box item.
        specs = bitem.boxitemspec_set.all()
        # If this box item has box item specs that fk to it, add its ID to the list.
        if specs:
            bitems_w_specs.append(bitem.id)
    # Make a queryset out of the box items in our list.
    bitems_qset = BoxItem.objects.filter(id__in=bitems_w_specs)
    return bitems_qset


def pdf_generation_form(request, box_id=None, edit=False, download_pdf=False):
    """Show the form that the user may fill out to generate a container PDF."""
    if edit:
        current_box = GeneratedBox.objects.get(id=box_id)
        if request.method == "POST":
            form = GeneratedBoxForm(request.POST, instance=current_box)
            if form.is_valid():
                form.save()
                return HttpResponse(JSMessage("Saved."))
            else:
                for error in form.errors:
                    return HttpResponse(JSMessage("Uh-oh, there's an invalid value."))
        else:
            form = GeneratedBoxForm(instance=current_box)
            pagevars = {
                "form": form,
                "type": "Box",
                "edit": edit,
                "box_id": box_id,
            }

            return render(request, "auto_corrugated/pdf_generation_form2.html", context=pagevars)

    if request.POST:
        # If pdf_typeis 1 or 3 this is a blank label so we need to populate certain values with the dummy values
        if request.POST.get("pdf_type") == "1" or request.POST.get("pdf_type") == "3":
            # make the post object modifyable
            mutable = request.POST._mutable
            request.POST._mutable = True
            request.POST["fourteen_digit_num"] = 99999999999999
            request.POST["nine_digit_num"] = 999999999
            request.POST["text_line_1"] = "n/a"
            request.POST["text_line_2"] = "n/a"
            # set the post object back to normal
            request.POST._mutable = mutable
        form = GeneratedBoxForm(request.POST)
        if form.is_valid():
            #            dumb_data = form.cleaned_data['dummy_data']
            if len(form.cleaned_data["text_line_1"]) > 22 or len(form.cleaned_data["text_line_2"]) > 22:
                msg = "Text lines can't be more than 22 characters."
                form._errors["Too long"] = form.error_class([msg])
                return form.serialize_errors()
            # kenton must now have a plate number
            elif form.cleaned_data["plant"].name == "Kenton" and (
                form.cleaned_data["plate_number"] is None or form.cleaned_data["plate_number"] == ""
            ):
                msg = "Kenton must have a plate number."
                form._errors["Plate Number Error"] = form.error_class([msg])
                return form.serialize_errors()
            else:
                print("Saving pdf_generation_form")
            form.save()
            if download_pdf:
                box_pdf = io.BytesIO()
                form.instance.generate_box_pdf(box_pdf, "reportlab", False, threadlocals.get_current_user())

                # Prepare a simple HTTP response with the StringIO object as an attachment.
                response = HttpResponse(box_pdf.getvalue(), content_type="application/pdf")
                # This is the filename the server will suggest to the browser.
                filename = "fsb_box_%s.pdf" % form.instance.nine_digit_num
                # The attachment header will make sure the browser doesn't try to
                # render the binary/ascii data.
                response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
                # Bombs away.
                return response
            else:
                box_id = form.instance.id
                return HttpResponse(JSMessage(box_id))
        else:
            return form.serialize_errors()
    else:
        if box_id:
            box = GeneratedBox.objects.get(id=box_id)

            if not edit:
                box.six_digit_num = ""
            form = GeneratedBoxForm(instance=box)
        else:
            form = GeneratedBoxForm()

    pagevars = {
        "form": form,
        "type": "Box",
        "edit": edit,
        "box_id": box_id,
    }

    return render(request, "auto_corrugated/pdf_generation_form2.html", context=pagevars)


def pdf_generation_form_edit(request, box_id):
    """Edit information in given GeneratedBox."""
    return pdf_generation_form(request, box_id, edit=True)


def json_get_boxitem_specs(request):
    """
    This view returns an options list for prototype.js to replace the
    'id_spec' select element. This is fired when an item type is selected.
    """
    # Get the BoxItem id from POST.
    boxitem_id = request.POST.get("boxitem_id", False)
    plant_id = request.POST.get("plant_id", False)
    if request.POST and boxitem_id:
        boxspec = get_object_or_404(BoxItem, id=boxitem_id)
        # These are all the BoxItemSpecs for this BoxItem.
        if not plant_id:
            specs = boxspec.boxitemspec_set.none()
        #            specs = boxspec.boxitemspec_set.all()
        else:
            specs = boxspec.boxitemspec_set.filter(plant=plant_id)
    else:
        # No BoxItem value has been provided, assume an empty list.
        specs = BoxItemSpec.objects.none()

    if specs:
        # No matching specs for this BoxItem, or no BoxItem specified.
        retval = ""
        # Generate the options list.
        for spec in specs:
            selected_attr = ""
            if spec.is_first:
                selected_attr = 'selected="selected"'
            retval += '<option value="%d" %s>%d case pack</option>\n' % (
                spec.id,
                selected_attr,
                spec.case_count,
            )
    else:
        # Empty option list HTML.
        retval = '<option value="" selected="selected">---------</option>'
    return HttpResponse(retval)


def json_get_boxitem_dimensions(request):
    """
    This view returns output appropriate for use in prototype.js's
    Ajax.Updater().
    """
    boxitemspec_id = request.POST.get("boxitemspec_id", False)
    if boxitemspec_id:
        boxspec = get_object_or_404(BoxItemSpec, id=boxitemspec_id)
        dimension_str = "%.4f %.4f %.4f" % (
            boxspec.width,
            boxspec.length,
            boxspec.height,
        )
        return HttpResponse(dimension_str)
    else:
        return HttpResponse()


class GeneratedBoxSearchForm(forms.Form):
    # Form for searching generated boxes.
    six_digit_num = IntegerField(required=False)
    nine_digit_num = IntegerField(required=False)
    fourteen_digit_num = IntegerField(required=False)
    case_count = IntegerField(required=False)
    plant = ModelChoiceField(Plant.objects.filter(is_in_acs=True), required=False)
    item = ModelChoiceField(BoxItem.objects.filter(active=True), required=False)


class PDFApprovalForm(forms.Form):
    """
    A super small form that asks the user if there are any special comments for the
    PDF. Rendered in the view_box_data view.
    """

    changes = CharField(widget=forms.Textarea, required=False)
    approvalSubmit = BooleanField(initial=False)


class PDFChangesForm(forms.Form):
    """
    A super small form that asks the user what changes they want made to a box
    PDF. Rendered in the view_box_data view.
    """

    changes = CharField(widget=forms.Textarea)
    approvalSubmit = BooleanField(initial=True)


class PDFFileForm(forms.Form):
    """
    A super small form that asks the user what changes they want made to a box
    PDF. Rendered in the view_box_data view. We're separating this form out
    so that it can be made into a formset and multiple copies generated. This
    will allow the user to upload multiple files at once.
    """

    file = forms.FileField(required=False)


class BoxSearchResults(ListView):
    """Displays box item search results."""

    # Set up ListView stuff.
    paginate_by = 25
    template_name = "auto_corrugated/box_search_results.html"
    # Extra parameter to handle a form object.
    form = None

    # Filter down the generated boxes via search terms and return the queryset.
    def get_queryset(self):
        # Gather all the generated boxes into a queryset.
        qset = GeneratedBox.objects.all()

        # Filter via search terms.
        s_six_digit_num = self.form.cleaned_data.get("six_digit_num", None)
        if s_six_digit_num:
            qset = qset.filter(six_digit_num=s_six_digit_num)
        s_nine_digit_num = self.form.cleaned_data.get("nine_digit_num", None)
        if s_nine_digit_num:
            qset = qset.filter(nine_digit_num=s_nine_digit_num)
        s_fourteen_digit_num = self.form.cleaned_data.get("fourteen_digit_num", None)
        if s_fourteen_digit_num:
            qset = qset.filter(fourteen_digit_num=s_fourteen_digit_num)
        s_case_count = self.form.cleaned_data.get("case_count", None)
        if s_case_count:
            qset = qset.filter(spec__case_count=s_case_count)
        s_plant = self.form.cleaned_data.get("plant", None)
        if s_plant:
            qset = qset.filter(plant=s_plant)
        s_item = self.form.cleaned_data.get("item", None)
        if s_item:
            qset = qset.filter(item=s_item)

        # Order by ID and return.
        qset = qset.order_by("-id")
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(BoxSearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Search Results"
        context["type"] = "item"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def box_search_form(request):
    """View for search form to find previously created boxes."""
    if request.GET:
        form = GeneratedBoxSearchForm(request.GET)
        if form.is_valid():
            # Call the result view directly for display.
            return BoxSearchResults.as_view(form=form)(request)
        else:
            print(form.errors)

    else:
        # This is the search page to be re-displayed if there's a problem or no
        # POST data.
        pagevars = {
            "form": GeneratedBoxSearchForm(),
        }

        return render(request, "auto_corrugated/box_search_form.html", context=pagevars)


class GeneratedLabelSearchForm(forms.Form):
    # Form for searching generated boxes.
    nine_digit_num = IntegerField(required=False)
    fourteen_digit_num = IntegerField(required=False)


class LabelSearchResults(ListView):
    """Displays item search results."""

    # Set up ListView stuff.
    paginate_by = 25
    template_name = "auto_corrugated/label_search_results.html"
    # Extra parameter to handle a form object.
    form = None

    # Filter down the generated labels via search terms and return the queryset.
    def get_queryset(self):
        # Gather all the generated labels into a queryset.
        qset = GeneratedLabel.objects.all()

        # Filter via search terms.
        s_nine_digit_num = self.form.cleaned_data.get("nine_digit_num", None)
        if s_nine_digit_num:
            qset = qset.filter(nine_digit_num=s_nine_digit_num)

        s_fourteen_digit_num = self.form.cleaned_data.get("fourteen_digit_num", None)
        if s_fourteen_digit_num:
            qset = qset.filter(fourteen_digit_num=s_fourteen_digit_num)

        # Order by ID and return.
        qset = qset.order_by("-id")
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(LabelSearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Search Results"
        context["type"] = "item"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def label_search_form(request):
    """View for search form to find previously created boxes."""
    if request.GET:
        form = GeneratedLabelSearchForm(request.GET)
        if form.is_valid():
            # Call the result view directly for display.
            return LabelSearchResults.as_view(form=form)(request)
        else:
            print(form.errors)

    else:
        # This is the search page to be re-displayed if there's a problem or no
        # POST data.
        pagevars = {
            "form": GeneratedLabelSearchForm(),
        }

        return render(request, "auto_corrugated/label_search_form.html", context=pagevars)


def check_and_create_barcode(box, argArr, type="box_pdf"):
    """
    This function will check for and create the barcode files if they do not exist in a blocking while loop.
    argArr = [fullpath, method, save_to_job] for type=box_pdf and [] for type=label

    The type is either box_pdf, or label, if we want to generate an entire autocorrugated box, or just a label
    """
    timeout = False
    # if there are no barcodes file then kick off the creation process and wait for it in a while loop
    if not barcodeFileExists(box.id, type):
        # start the barcode creation process
        triggerBarcodeCreation(box.id, type)

        # check to see if barcode file exists (returns true if does, so while not true)
        barcodeReady = False
        counter = 0
        while not barcodeReady:
            barcodeReady = barcodeFileExists(box.id, type)
            # a condition to check if we are approaching an infinite loop. 90 seconds here as the max time we want to wait
            # the polling interval of automation engine is 60 seconds
            if counter > 90:
                timeout = True
                break
            # increment out counter with a time mechanic so we dont wait forever if there is an error
            counter = counter + 1
            time.sleep(1)

    # if we get here, check to see if we timed out and if not, then generate the box. If not timeout, we should have barcodes
    if timeout:
        return False
    else:
        if type == "box_pdf":
            box.generate_box_pdf(argArr[0], argArr[1], argArr[2], threadlocals.get_current_user())
        else:
            # Here box = lable
            box.generate_label_pdf(argArr[0], box.id)
        return True


def generate_box(request, box_id, method, save_to_job=False):
    """Create PDF from existing GeneratedBox object."""
    box = GeneratedBox.objects.get(id=box_id)

    if save_to_job:
        # Generate the PDF and save into the job folder.
        # Can't create PDF in folder if there is no job associated with it.
        if box.job:
            # Allow the model to create the full path for the PDF.
            fullpath = None
            # Check and make sure that the barcode files exist for a production ready job and Generate
            # the PDF and save at the given path (inside job folder)
            if barcodeFileExists(box.id, "box_pdf"):
                box.generate_box_pdf(fullpath, method, save_to_job, threadlocals.get_current_user())
            else:
                # if the barcode files do no exist then kick off the automation engine workflow to make them and
                # wait before trying to create the job. This is threaded which should not lock the client for the user.
                thread1 = threading.Thread(
                    target=check_and_create_barcode,
                    args=[box, [fullpath, method, save_to_job]],
                )
                thread1.start()
            response = HttpResponse("")
            response.set_cookie(key="fileDownload", value="true", path="/")
            return response
        else:
            # None triggers an error that can be caught by jquery on the client side
            return None
            #    response = HttpResponse(JSMessage("Error saving PDF to job folder, there is no associated job.",
            #                                      is_error=True))
            #    response.set_cookie(key='fileDownload', value="true", path='/')
            #    return response
    else:
        box_pdf = io.BytesIO()
        # create the box, but if we use automation engine then we dont want a thread so the user has to wait for the
        # production ready file
        if method == "automationEngine":
            if not check_and_create_barcode(box, [box_pdf, method, save_to_job]):
                # None triggers an error that can be caught by jquery on the client side
                return None
                # response = HttpResponse(JSMessage("Error creating PDF",
                #                              is_error=True))
                # response.set_cookie(key='fileDownload', value="true", path='/')
                # return response
        else:
            # if we use reportlab to generate the barcodes then proceeed with Preview PDF generation normally.
            box.generate_box_pdf(box_pdf, method, save_to_job, threadlocals.get_current_user())
        # Prepare a simple HTTP response with the StringIO object as an attachment.
        response = HttpResponse(box_pdf.getvalue(), content_type="application/pdf")
        # This is the filename the server will suggest to the browser.
        filename = "fsb_box_%s.pdf" % box.nine_digit_num
        # The attachment header will make sure the browser doesn't try to
        # render the binary/ascii data.
        response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
        response.set_cookie(key="fileDownload", value="true", path="/")
        # Bombs away.
        return response


def approve_box(request, box_id, type="Approved"):
    """
    Set GeneratedBox to Approved=True. This will allow download of the PDF
    in a editable, useable format.
    This will also create a job from the Corrugate information for billing
    purposes, and save the PDF into that job folder.
    """
    box = GeneratedBox.objects.get(id=box_id)
    box.approved = True
    box.save()

    # Create the job that this will be saved into.
    if type == "Approved":
        if box.platepackage:
            creation_type = "Tiffs"
        else:
            creation_type = "PDF_Only"
        box.create_job_for_box(creation_type=creation_type)

    elif type == "Changes":
        box.create_job_for_box(creation_type="Changes")

    # No need for filename (let method handle that. Set Save to Job as True.)
    # in approvals we do not need to wait for the function so we put it on its own thread.
    thread1 = threading.Thread(target=check_and_create_barcode, args=[box, [None, "automationEngine", True]])
    thread1.start()

    if type == "Approved":
        # return HttpResponse(JSMessage(box_id))
        return box.job.id
    elif type == "Changes":
        #    return HttpResponse(JSMessage(box.job.id))
        return box.job.id


def view_box_data(request, box_id):
    """View input data for a GeneratedBox record."""
    box = GeneratedBox.objects.get(id=box_id)
    """
    A small form that pops up when the user requests a change to a box PDF. Asks
    them what changes they want and then adds that info to the job's joblog. Also
    let's the user upload a reference file.
    """
    # Make a formset out of PDFFileForm so the user can upload multiple files.
    PDFFileFormSet = formset_factory(PDFFileForm, extra=1)

    if request.POST:
        approvalCheck = request.POST.get("approvalSubmit", False)
        changeform = PDFChangesForm(request.POST)
        approvalform = PDFApprovalForm(request.POST)

        fileformset = PDFFileFormSet(request.POST, request.FILES)
        fileformsetApproval = PDFFileFormSet(request.POST, request.FILES)
        """
            Checks the ApprovalCheck boolean. It is set to on/off. Off = False
            For some reason this will not evaluate to True but will to False
            so we will take not False as our True
        """
        if approvalCheck:
            if changeform.is_valid() and fileformset.is_valid():
                # Create a job for the box and assign the ID to a variable.
                new_box_job = approve_box(request, box_id, "Changes")
                # Create a JobLog with the requested changes specified by user.
                #                changes = changeform.cleaned_data['changes']
                changes = request.POST.get("changes")

                box_job = Job.objects.get(id=new_box_job)
                log = JobLog(
                    job=box_job,
                    user=threadlocals.get_current_user(),
                    type=JOBLOG_TYPE_NOTE,
                    log_text=changes,
                )
                log.save()

                # Check for reference files and drop them in the job folder.
                path = fs_api.get_job_folder(box_job.id)
                path += "/Database_Documents"
                # Iterate through the upload fields and check for files.
                for fileform in fileformset.cleaned_data:
                    # Check if there's a file in this field.
                    if fileform:
                        destination = open(os.path.join(path, fileform["file"].name), "wb+")
                        # Write the file to the job folder.
                        for chunk in fileform["file"]:
                            destination.write(chunk)
                        destination.close()
                # All done. Send them to the new job.
                # return HttpResponseRedirect('/workflow/job/%s/' %box_job.id )
                return HttpResponseRedirect("/acs/view_box_data/%s/" % box.id)
        else:
            if approvalform.is_valid() and fileformsetApproval.is_valid():
                new_box_job = approve_box(request, box_id)
                # changes = approvalform.cleaned_data['changes']
                changes = request.POST.get("changes")

            box_job = Job.objects.get(id=new_box_job)
            if not changes == "":
                log = JobLog(
                    job=box_job,
                    user=threadlocals.get_current_user(),
                    type=JOBLOG_TYPE_NOTE,
                    log_text=changes,
                )
                log.save()

            # Check for reference files and drop them in the job folder.
            path = fs_api.get_job_folder(box_job.id)
            path += "/Database_Documents"
            # Iterate through the upload fields and check for files.
            for fileform in fileformsetApproval.cleaned_data:
                # Check if there's a file in this field.
                if fileform:
                    destination = open(os.path.join(path, fileform["file"].name), "wb+")
                    # Write the file to the job folder.
                    for chunk in fileform["file"]:
                        destination.write(chunk)
                    destination.close()
                return HttpResponseRedirect("/acs/view_box_data/%s/" % box.id)

    else:
        changeform = PDFChangesForm()
        approvalform = PDFApprovalForm()
        fileformset = PDFFileFormSet()
        fileformsetApproval = PDFFileFormSet()
    pagevars = {
        "box": box,
        "changeform": changeform,
        "approvalform": approvalform,
        "fileformset": fileformset,
        "fileformsetApproval": fileformsetApproval,
    }

    return render(request, "auto_corrugated/view_box_data.html", context=pagevars)


def view_label_data(request, label_id):
    """View input data for a GeneratedBox record."""
    label = GeneratedLabel.objects.get(id=label_id)

    pagevars = {
        "label": label,
    }

    return render(request, "auto_corrugated/view_label_data.html", context=pagevars)


def generate_label(request, label_id):
    """Create PDF from existing GeneratedBox object."""
    label = GeneratedLabel.objects.get(id=label_id)
    label_pdf = io.BytesIO()
    check_and_create_barcode(label, [label_pdf], "label")
    # label.generate_label_pdf(label, [label_pdf], "label")

    # Prepare a simple HTTP response with the StringIO object as an attachment.
    response = HttpResponse(label_pdf.getvalue(), content_type="application/pdf")
    # This is the filename the server will suggest to the browser.
    filename = "fsb_label_%s.pdf" % label.nine_digit_num
    # The attachment header will make sure the browser doesn't try to
    # render the binary/ascii data.
    response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
    response.set_cookie(key="fileDownload", value="true", path="/")
    # Bombs away.
    return response


class GeneratedLabelForm(ModelForm):
    # We want this to be empty when the page is first loaded.
    nine_digit_num = IntegerField(widget=TextInput(attrs={"maxlength": "9", "size": "9"}))
    fourteen_digit_num = IntegerField(widget=TextInput(attrs={"maxlength": "14", "size": "14"}))
    pdf_type = IntegerField(initial=2)

    class Meta:
        model = GeneratedLabel
        fields = (
            "nine_digit_num",
            "fourteen_digit_num",
            "text_line_1",
            "text_line_2",
            "pdf_type",
        )

    def clean_nine_digit_num(self):
        """Check that the nine_digit_num field has the correct number of digits."""
        data = self.cleaned_data["nine_digit_num"]
        if data > 999999999:
            raise forms.ValidationError("The nine digit number has more than 9 digits!")
        elif data < 100000000:
            raise forms.ValidationError("The nine digit number is not long enough!")
        return data

    def clean_fourteen_digit_num(self):
        """Check that the fourteen_digit_num field has the correct number of digits."""
        data = self.cleaned_data["fourteen_digit_num"]
        if data > 99999999999999:
            raise forms.ValidationError("The fourteen digit (SCC) number has more than 14 digits!")
        elif data < 10000000000000:
            raise forms.ValidationError("The fourteen digit (SCC) number is not long enough!")
        return data


def pdf_label_generation_form(request):
    """Show the form that the user may fill out to generate a label-only PDF."""
    if request.POST:
        form = GeneratedLabelForm(request.POST)
        if form.is_valid():
            label = form.save()
            label_pdf = io.BytesIO()
            check_and_create_barcode(label, [label_pdf], "label")
            # form.instance.generate_label_pdf(label_pdf, form.instance.id)

            # Prepare a simple HTTP response with the StringIO object as an attachment.
            response = HttpResponse(label_pdf.getvalue(), content_type="application/pdf")
            # This is the filename the server will suggest to the browser.
            filename = "fsb_label_%s.pdf" % form.instance.nine_digit_num
            # The attachment header will make sure the browser doesn't try to
            # render the binary/ascii data.
            response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
            response.set_cookie(key="fileDownload", value="true", path="/")
            # Bombs away.

            #            return response
            label_id = form.instance.id
            return HttpResponse(JSMessage(label_id))
    else:
        form = GeneratedLabelForm()

    pagevars = {
        "form": form,
        "type": "Label",
    }

    return render(request, "auto_corrugated/pdf_generation_form2.html", context=pagevars)


def help(request):
    """Display help page for Automated Corrugated System"""
    pagevars = {
        "page_title": "Automated Corrugated System Help",
    }

    return render(request, "auto_corrugated/help.html", context=pagevars)
