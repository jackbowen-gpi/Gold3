"""Item Catalog Views"""

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.forms import CharField, ModelForm, Textarea
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.generic.list import ListView

from gchub_db.apps.workflow import app_defs
from gchub_db.apps.workflow.models import (
    ItemCatalog,
    ItemCatalogPhoto,
    ItemSpec,
    Plant,
    Press,
    PrintLocation,
    SpecialMfgConfiguration,
    StepSpec,
)
from gchub_db.includes import general_funcs
from gchub_db.includes.gold_json import JSMessage
from gchub_db.middleware import threadlocals


class CatalogSearchForm(forms.Form):
    """Search for Item Catalog records."""

    size = forms.CharField(required=False)
    active = forms.BooleanField(required=False, initial=False)
    type_choices = []
    type_choices.append(("", "---------"))
    for choice in app_defs.ITEM_TYPES:
        type_choices.append(choice)
    item_type = forms.ChoiceField(choices=type_choices, required=False)
    sub_choices = []
    sub_choices.append(("", "---------"))
    for choice in app_defs.PROD_SUBSTRATES:
        sub_choices.append(choice)
    substrate = forms.ChoiceField(choices=sub_choices, required=False)
    board_choices = []
    board_choices.append(("", "---------"))
    for choice in app_defs.PROD_BOARDS:
        board_choices.append(choice)
    board = forms.ChoiceField(choices=board_choices, required=False)
    sort_by = forms.ChoiceField(choices=[("size", "Size")], required=False)
    sort_order = forms.ChoiceField(
        choices=[("desc", "Descending"), ("asc", "Ascending")],
        initial="asc",
        required=False,
    )


class SpecSearchForm(forms.Form):
    """Search for Item Specification records."""

    size = forms.CharField(required=False)
    plant = forms.ModelChoiceField(
        queryset=Plant.objects.all().order_by("name"), required=False
    )
    press = forms.ModelChoiceField(
        queryset=Press.objects.all().order_by("name"), required=False
    )
    sort_by = forms.ChoiceField(choices=[("size", "Size")], required=False)
    sort_order = forms.ChoiceField(
        choices=[("desc", "Descending"), ("asc", "Ascending")],
        initial="asc",
        required=False,
    )


class ItemCatalogForm(ModelForm):
    """Form to add to Item Catalog."""

    def __init__(self, request, *args, **kwargs):
        super(ItemCatalogForm, self).__init__(*args, **kwargs)
        self.fields["acts_like"] = forms.ModelChoiceField(
            queryset=ItemCatalog.objects.filter(active=True).order_by("size"),
            required=False,
        )
        self.fields["acts_like"].help_text = (
            "(JDF Stepping Only -- Item will use S&R of selected item.)"
        )
        self.fields["product_substrate"].label = "Proofing"
        self.fields["product_substrate"].help_text = (
            "(Determines substrate for proofing purposes.)"
        )
        self.fields["mfg_name"].help_text = (
            "(QAD code, 8 characters. Example: SMR-0160)"
        )
        self.fields["bev_size_code"].label = "Bev Size Code"
        self.fields["bev_size_code"].help_text = (
            "(Evergreen only. Example: Q=Quart, A=4oz Eco)"
        )
        self.fields["productsubcategory"].help_text = (
            '(For sorting purposes in PDF Tempalte download page.) Hold down "Control", or "Command" on a Mac, to select more than one.'
        )

    class Meta:
        model = ItemCatalog
        exclude = ("photo", "template")


class ItemSpecsForm(ModelForm):
    """Form to add to Item Specs."""

    def __init__(self, request, *args, **kwargs):
        super(ItemSpecsForm, self).__init__(*args, **kwargs)
        # qset = PrintLocation.objects.filter(plant__workflow=self.fields["size.workflow"])
        # self.fields["printlocation"] = forms.ModelChoiceField(queryset=qset, required=False)
        self.fields["size"] = forms.ModelChoiceField(
            queryset=ItemCatalog.objects.filter(active=True).order_by("size")
        )
        self.fields["printlocation"] = forms.ModelChoiceField(
            queryset=PrintLocation.objects.filter(active=True).order_by("plant__name")
        )
        #        self.fields["num_colors"].label = 'Max. Num. Colors'
        self.fields["horizontal"].help_text = "(Rectangle dimensions to build art to.)"
        self.fields["vertical"].help_text = "(Rectangle dimensions to build art to.)"
        self.fields["total_print_area"].help_text = (
            "(A.K.A inch squared from pack edge.)"
        )

    #        self.fields["step_across"].help_text = '(Num. columns across the web.)'
    #        self.fields["step_around"].help_text = '(Num. rows around the plate cylinder.)'

    class Meta:
        model = ItemSpec
        exclude = ("case_dim_w", "case_dim_h", "case_dim_d", "case_wt", "case_pack")


class StepSpecsForm(ModelForm):
    """Form to add to Step Specs."""

    comments = CharField(widget=Textarea)

    def __init__(self, request, *args, **kwargs):
        super(StepSpecsForm, self).__init__(*args, **kwargs)
        self.fields["itemspec"] = forms.ModelChoiceField(
            queryset=ItemSpec.objects.filter(active=True).order_by("size")
        )
        self.fields["special_mfg"].label = "Special Mfg"
        self.fields["eng_num"].label = "Engineering Num"
        self.fields["num_colors"].label = "Max Num Colors"
        self.fields["active"].label = "Active"
        self.fields["step_across"].help_text = "(Num. columns across the web.)"
        self.fields["step_around"].help_text = "(Num. rows around the plate cylinder.)"
        self.fields["template_horizontal"]
        self.fields["template_vertical"]
        self.fields["step_around"].help_text = "(Num. rows around the plate cylinder.)"
        self.fields["num_blanks"].label = "Num Blanks"
        self.fields["status"]
        self.fields["comments"]

    class Meta:
        model = StepSpec
        exclude = ("creation_date", "last_user", "last_edit")


class StepSearchForm(forms.Form):
    """Search for Step and Repeat records."""

    size = forms.CharField(required=False)
    plant = forms.ModelChoiceField(
        queryset=Plant.objects.all().order_by("name"), required=False
    )
    press = forms.ModelChoiceField(
        queryset=Press.objects.all().order_by("name"), required=False
    )
    special_mfg = forms.ModelChoiceField(
        queryset=SpecialMfgConfiguration.objects.all().order_by("name"), required=False
    )
    eng_num = forms.CharField(required=False)
    sort_by = forms.ChoiceField(choices=[("size", "Size")], required=False)
    sort_order = forms.ChoiceField(
        choices=[("desc", "Descending"), ("asc", "Ascending")],
        initial="asc",
        required=False,
    )


def itemcatalog_home(request):
    """Home page for Item Catalog management."""
    item_count = ItemCatalog.objects.all().count()
    item_spec_count = ItemSpec.objects.all().count()
    item_photo = ItemCatalogPhoto.objects.all().count()

    pagevars = {
        "page_title": "Item Catalog Menu",
        "item_count": item_count,
        "item_spec_count": item_spec_count,
        "item_photo": item_photo,
    }
    return render(
        request, "workflow/itemcatalog/itemcatalog_home.html", context=pagevars
    )


def sendAddEditProductEmail(type, user, id):
    """Sends a notification email for additions or changes to the item catalog."""
    # Get the name of the product so we can put that in the email.
    product = ItemCatalog.objects.get(id=id)
    product_name = product.size

    # Continue composing the email.
    mail_send_to = []
    group_members = User.objects.filter(
        groups__name="EmailGCHubProductChanges", is_active=True
    )
    for manager in group_members:
        mail_send_to.append(manager.email)
    mail_from = "Gold - Clemson Support <%s>" % settings.EMAIL_SUPPORT
    if type == "add":
        mail_subject = "New product added to Item Catalog"
    else:
        mail_subject = "Item Catalog product was edited"
    mail_body = loader.get_template("emails/item_catalog_change.txt")
    mail_context = {
        "type": type,
        "user": user,
        "id": id,
        "product_name": product_name,
    }
    # send the email
    msg = EmailMultiAlternatives(
        mail_subject, mail_body.render(mail_context), mail_from, mail_send_to
    )
    msg.content_subtype = "html"
    msg.send()


def new_itemcatalog(request):
    """Saves the data for a new product added to Item Catalog."""
    if request.POST:
        form = ItemCatalogForm(request, request.POST)
        if form.is_valid():
            saveform = ItemCatalog()
            saveform = form
            saveform.active = "Yes"
            product = saveform.save()

            sendAddEditProductEmail("add", threadlocals.get_current_user(), product.id)
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        add_form = ItemCatalogForm(request)
        pagevars = {
            "page_title": "Add Product to Item Catalog",
            "add_form": add_form,
        }

        return render(
            request, "workflow/itemcatalog/add_itemcatalog.html", context=pagevars
        )


def edit_itemcatalog(request, item_id):
    """Home page for Item Catalog management."""
    item = ItemCatalog.objects.get(id=item_id)
    if request.POST:
        form = ItemCatalogForm(request, request.POST, instance=item)
        if form.is_valid():
            saveform = ItemCatalog()
            saveform = form
            product = saveform.save()
            sendAddEditProductEmail("edit", threadlocals.get_current_user(), product.id)
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        add_form = ItemCatalogForm(request, instance=item)
        pagevars = {
            "page_title": "Edit Product in Item Catalog",
            "add_form": add_form,
            "item": item,
        }
        return render(
            request, "workflow/itemcatalog/edit_itemcatalog.html", context=pagevars
        )


class BrowseItemCatalog(ListView):
    """Listing of all items in Item Catalog"""

    queryset = ItemCatalog.objects.all().order_by("size")
    paginate_by = 25
    template_name = "workflow/itemcatalog/search_results.html"

    def get_context_data(self, **kwargs):
        context = super(BrowseItemCatalog, self).get_context_data(**kwargs)
        context["page_title"] = "Item Catalog Search Results"
        context["type"] = "catalog"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def catalog_search(request):
    """Displays the item catalog search form."""
    pagevars = {
        "page_title": "Catalog Search",
        "form": CatalogSearchForm(),
        "type": "catalog",
    }
    # This is the search page to be re-displayed if there's a problem or no
    # POST data.
    search_page = render(
        request, "workflow/itemcatalog/search_form.html", context=pagevars
    )

    if request.GET:
        form = CatalogSearchForm(request.GET)
        if form.is_valid():
            # Call the result view directly for display.
            return CatalogSearchResults.as_view()(request)
        else:
            # Errors in form data, return the form with messages.
            return search_page
    else:
        # No POST data, return an empty form.
        return search_page


class CatalogSearchResults(ListView):
    """Displays item catalog search results."""

    paginate_by = 25
    template_name = "workflow/itemcatalog/search_results.html"

    # Searching and filtering.
    def get_queryset(self):
        qset = ItemCatalog.objects.all()
        # Filter via search terms if any.
        if self.request.GET:
            s_size = self.request.GET.get("size", "")
            if s_size != "":
                qset = qset.filter(size__icontains=s_size)
            s_type = self.request.GET.get("item_type", "")
            if s_type != "":
                qset = qset.filter(item_type__icontains=s_type)
            s_substrate = self.request.GET.get("substrate", "")
            if s_substrate != "":
                qset = qset.filter(product_substrate__icontains=s_substrate)
            s_board = self.request.GET.get("board", "")
            if s_board != "":
                qset = qset.filter(product_board__icontains=s_board)
            try:
                s_type = self.request.GET.get("active", "")
                if s_type == "on":
                    qset = qset.filter(active=True)
            except Exception:
                pass
            # Sort via selected order.
            sort = self.request.GET.get("sort_order")
            if sort == "desc":
                qset = qset.order_by("-size")
            if sort == "asc":
                qset = qset.order_by("size")
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(CatalogSearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Item Catalog Search Results"
        context["type"] = "catalog"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def spec_search(request):
    """Displays the item specification search form."""
    pagevars = {
        "page_title": "Item Specification Search",
        "form": SpecSearchForm(),
        "type": "specs",
    }
    # This is the search page to be re-displayed if there's a problem or no
    # POST data.
    search_page = render(
        request, "workflow/itemcatalog/search_form.html", context=pagevars
    )

    if request.GET:
        form = SpecSearchForm(request.GET)
        if form.is_valid():
            # Call the result view directly for display.
            return SpecSearchResults.as_view()(request)
        else:
            # Errors in form data, return the form with messages.
            return search_page
    else:
        # No POST data, return an empty form.
        return search_page


class SpecSearchResults(ListView):
    """Displays item specification search results."""

    paginate_by = 25
    template_name = "workflow/itemcatalog/search_results.html"

    # Searching and filtering.
    def get_queryset(self):
        qset = ItemSpec.objects.all()
        # Filter via search terms if any.
        if self.request.GET:
            s_size = self.request.GET.get("size", "")
            if s_size != "":
                qset = qset.filter(size__size__icontains=s_size)
            s_plant = self.request.GET.get("plant", "")
            if s_plant != "":
                qset = qset.filter(printlocation__plant=s_plant)
            s_press = self.request.GET.get("press", "")
            if s_press != "":
                qset = qset.filter(printlocation__press=s_press)

            sort = self.request.GET.get("sort_order")
            if sort == "desc":
                qset = qset.order_by("-size")
            if sort == "asc":
                qset = qset.order_by("size")
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(SpecSearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Item Specs Search Results"
        context["type"] = "specs"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def step_search(request):
    """Displays the step and repeat search form."""
    pagevars = {
        "page_title": "Step & Repeat Search",
        "form": StepSearchForm(),
        "type": "step",
    }
    # This is the search page to be re-displayed if there's a problem or no
    # POST data.
    search_page = render(
        request, "workflow/itemcatalog/search_form.html", context=pagevars
    )

    if request.GET:
        form = StepSearchForm(request.GET)
        if form.is_valid():
            # Call the result view directly for display.
            return StepSearchResults.as_view()(request)
        else:
            # Errors in form data, return the form with messages.
            return search_page
    else:
        # No POST data, return an empty form.
        return search_page


class StepSearchResults(ListView):
    """Displays step and repeat search results."""

    paginate_by = 25
    template_name = "workflow/itemcatalog/search_results.html"

    # Searching and filtering.
    def get_queryset(self):
        qset = StepSpec.objects.all()
        # Filter via search terms if any.
        if self.request.GET:
            s_size = self.request.GET.get("size", "")
            if s_size != "":
                qset = qset.filter(itemspec__size__size__icontains=s_size)
            s_plant = self.request.GET.get("plant", "")
            if s_plant != "":
                qset = qset.filter(itemspec__printlocation__plant=s_plant)
            s_press = self.request.GET.get("press", "")
            if s_press != "":
                qset = qset.filter(itemspec__printlocation__press=s_press)
            s_special_mfg = self.request.GET.get("special_mfg", "")
            if s_special_mfg != "":
                qset = qset.filter(special_mfg=s_special_mfg)
            s_eng_num = self.request.GET.get("eng_num", "")
            if s_eng_num != "":
                qset = qset.filter(eng_num__icontains=s_eng_num)
            # Sort ascending or descending.
            sort = self.request.GET.get("sort_order")
            if sort == "desc":
                qset = qset.order_by("-itemspec__size")
            if sort == "asc":
                qset = qset.order_by("itemspec__size")
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(StepSearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Step Specs Search Results"
        context["type"] = "step"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


class BrowseItemSpecs(ListView):
    """Listing of all items in Item Specs"""

    paginate_by = 25
    template_name = "workflow/itemcatalog/search_results.html"
    queryset = ItemSpec.objects.all().order_by("size")

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(BrowseItemSpecs, self).get_context_data(**kwargs)
        context["page_title"] = "Item Specs Search Results"
        context["type"] = "specs"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def new_itemspecs(request, set_size=None, set_printlocation=None):
    """Saves the data for a new product added to Item Catalog."""
    if request.POST:
        form = ItemSpecsForm(request, request.POST)
        if form.is_valid():
            saveform = ItemSpec()
            saveform = form
            saveform.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        add_form = ItemSpecsForm(request)
        # If a specific size was passed, prepopulate that field.
        try:
            get_size = ItemCatalog.objects.get(id=set_size)
            add_form.fields["size"].initial = get_size.id
        except ItemCatalog.DoesNotExist:
            pass
        # If a specfic printlocation was passed, prepopulate that field.
        try:
            get_pl = PrintLocation.objects.get(id=set_printlocation)
            add_form.fields["printlocation"].initial = get_pl.id
        except PrintLocation.DoesNotExist:
            pass

        pagevars = {
            "page_title": "Add Specification for Product",
            "add_form": add_form,
        }
        return render(
            request, "workflow/itemcatalog/add_itemspecs.html", context=pagevars
        )


def new_stepspecs(request):
    """Saves the data for a new step and repeat added to Item Catalog."""
    if request.POST:
        form = StepSpecsForm(request, request.POST)
        if form.is_valid():
            saveform = StepSpec()
            saveform = form
            saveform.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        add_form = StepSpecsForm(request)
        pagevars = {
            "page_title": "Add Specification for Step & Repeat",
            "add_form": add_form,
        }
        return render(
            request, "workflow/itemcatalog/add_stepspecs.html", context=pagevars
        )


def edit_stepspecs(request, stepspec_id):
    """Edit Step & Repeat Specs"""
    stepspec = StepSpec.objects.get(id=stepspec_id)
    if request.POST:
        form = StepSpecsForm(request, request.POST, instance=stepspec)
        if form.is_valid():
            form.save()
            # Set up some time/user stamps on the file that was just edited.
            lookup = StepSpec.objects.get(id=stepspec_id)
            lookup.last_user = threadlocals.get_current_user()
            lookup.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        add_form = StepSpecsForm(request, instance=stepspec)
        page_title = "Edit step and repeat specifications"
        pagevars = {
            "page_title": page_title,
            "add_form": add_form,
            "stepspec": stepspec,
        }

        return render(
            request, "workflow/itemcatalog/edit_stepspecs.html", context=pagevars
        )


def edit_itemspecs(request, spec_id):
    """Edit Item Specs"""
    spec = ItemSpec.objects.get(id=spec_id)
    if request.POST:
        form = ItemSpecsForm(request, request.POST, instance=spec)
        if form.is_valid():
            form.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        add_form = ItemSpecsForm(request, instance=spec)
        page_title = "Edit Specification for Item"
        pagevars = {
            "page_title": page_title,
            "add_form": add_form,
            "spec": spec,
        }
        return render(
            request, "workflow/itemcatalog/edit_itemspecs.html", context=pagevars
        )


def new_itemspecs_dupe(request, spec_id):
    """Duplicate an item specification."""
    spec = ItemSpec.objects.get(id=spec_id)
    if request.POST:
        print("POST recieved!")
        form = ItemSpecsForm(request, request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        add_form = ItemSpecsForm(request, instance=spec)
        page_title = "Duplicating Specification for Item"
        pagevars = {
            "page_title": page_title,
            "add_form": add_form,
            "spec": spec,
            "duplicate": True,
        }
        return render(
            request, "workflow/itemcatalog/edit_itemspecs.html", context=pagevars
        )


def new_stepspecs_dupe(request, stepspec_id):
    """Duplicate a step and repeat specification."""
    stepspec = StepSpec.objects.get(id=stepspec_id)
    if request.POST:
        print("POST recieved!")
        form = StepSpecsForm(request, request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            for field, errors in list(form.errors.items()):
                errorMsg = " "
                for error in errors:
                    errorMsg += error + " "
                return HttpResponse(
                    JSMessage(
                        "Error on field: " + field + ". Reason: " + errorMsg,
                        is_error=True,
                    )
                )
    else:
        add_form = StepSpecsForm(request, instance=stepspec)
        page_title = "Duplicating Specification for Step and Repeat"
        pagevars = {
            "page_title": page_title,
            "add_form": add_form,
            "stepspec": stepspec,
            "duplicate": True,
        }
        return render(
            request, "workflow/itemcatalog/edit_stepspecs.html", context=pagevars
        )
