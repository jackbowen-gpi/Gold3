"""This module contains the functions that are called in response to specific
URLs mentioned in urls.py in the project's root directory. It pulls the data
storage models from the models file in the rendersys directory (this one).
"""

from django import forms
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from gchub_db.apps.item_catalog.models import *
from gchub_db.apps.workflow.models import ItemCatalog
from gchub_db.includes import fs_api
from gchub_db.includes.form_utils import JSONErrorForm
from gchub_db.includes.gold_json import JSMessage


def home(request):
    """Home page for Item Catalog management."""
    pagevars = {"form": CatalogSearchForm()}

    return render(request, "item_catalog/home.html", context=pagevars)


class CatalogSearchForm(forms.Form, JSONErrorForm):
    """Search for Item Catalog records."""

    size = forms.CharField(required=False)
    mfg_name = forms.CharField(required=False)

    category = forms.ModelChoiceField(
        queryset=ProductSubCategory.objects.all(), required=False
    )

    active = forms.BooleanField(required=False, initial=False)

    # YUI DataTable stuff. Not rendered on the page.
    sort = forms.CharField(required=False)
    dir = forms.CharField(required=False)
    startIndex = forms.IntegerField(required=False)
    results = forms.IntegerField(required=False)


def catalog_search(request):
    """Processes the AJAX request to search the catalog. Returns JSON results."""
    if request.GET:
        form = CatalogSearchForm(request.GET)
        if form.is_valid():
            # Call the result view directly for display.
            return catalog_search_results(request, form)
        else:
            # Errors in form data, return the form with messages.
            return form.serialize_errors()
    else:
        # No POST data, return an empty form.
        return HttpResponse(JSMessage("Invalid query", is_error=True))


def catalog_search_results(request, form):
    """Queries, serializes, and returns JSON results through catalog_search()."""
    # The base QuerySet to use for the rest of the filtering.
    qset = ItemCatalog.objects.all()

    s_size = form.cleaned_data.get("size", "")
    if s_size != "":
        qset = qset.filter(size__istartswith=s_size)

    s_mfg_name = form.cleaned_data.get("mfg_name", "")
    if s_mfg_name != "":
        qset = qset.filter(mfg_name__istartswith=s_mfg_name)

    s_category = form.cleaned_data.get("category", False)
    if s_category:
        qset = qset.filter(productsubcategory=s_category)

    s_active = form.cleaned_data.get("active", False)
    if s_active:
        qset = qset.filter(active=True)

    sort_field = form.cleaned_data.get("sort", "size")
    if sort_field == "":
        sort_field = "size"

    sort_dir = form.cleaned_data.get("dir")
    if sort_dir == "desc":
        qset = qset.order_by("-" + sort_field)
    else:
        qset = qset.order_by(sort_field)

    start_index = form.cleaned_data.get("startIndex")
    if not start_index:
        start_index = 0
    num_results = form.cleaned_data.get("results")
    if not num_results:
        num_results = 25
    end_index = start_index + num_results

    # Begin formation of the JSON response.
    message = JSMessage("Success.")
    results = []
    for result in qset[start_index:end_index]:
        product_subcats = list(
            result.productsubcategory.values_list("sub_category", flat=True)
        )

        size_url = "<a href='javascript:create_item_editor(\"%s\")'>%s</a>" % (
            reverse("item_catalog_itemcat_popup_edit_itemcatalog", args=[result.id]),
            result.size,
        )
        if result.active:
            active_icon_img = "img/icons/accept.png"
        else:
            active_icon_img = "img/icons/cancel.png"

        active_img = "<img src='%s%s' />" % (settings.MEDIA_URL, active_icon_img)
        rdict = {
            "size": size_url,
            "mfg_name": result.mfg_name,
            "item_type": result.get_item_type_display(),
            "active": active_img,  # result.active,
            "product_substrate": result.get_product_substrate_display(),
            "productsubcategory": ", ".join(product_subcats),
            "workflow": result.workflow.name,
        }
        results.append(rdict)

    response_dict = {"total_records": qset.count(), "results": results}

    message.contents = response_dict
    return HttpResponse(message)


class ItemCatalogForm(forms.ModelForm, JSONErrorForm):
    """Form to add to Item Catalog"""

    acts_like = forms.ModelChoiceField(
        queryset=ItemCatalog.objects.filter(active=True).order_by("size"),
        required=False,
    )

    class Meta:
        model = ItemCatalog
        exclude = ("photo", "template")


def itemcat_popup(request, itemcat_id=None):
    """Renders the ItemCatalog editing popup. The main tab on the page is
    the form for adds/edits, this is handled by this view. Spec editing/adding
    is handled elsewhere.
    """
    # Stores extra context variables.
    pagevars = {}

    if itemcat_id:
        pagevars["mode"] = "edit"
        itemcat = ItemCatalog.objects.get(id=itemcat_id)
        pagevars["page_title"] = "Editing %s" % itemcat.size
        pagevars["object"] = itemcat
    else:
        pagevars["mode"] = "add"
        itemcat = None
        pagevars["page_title"] = "New Item"

    if request.GET:
        form = ItemCatalogForm(request.GET, instance=itemcat)

        if form.is_valid():
            form.save()
            message = JSMessage("Saved.")
            message.contents = {"instance_id": form.instance.id}
            return HttpResponse(message)
        else:
            return form.serialize_errors()
    else:
        form = ItemCatalogForm(instance=itemcat)

    pagevars["form"] = form

    return render(request, "item_catalog/itemcat_popup.html", context=pagevars)


def get_pdf_template(request, size_id):
    """Return the path to the template based on the size pased."""
    size = ItemCatalog.objects.get(id=size_id)
    file = fs_api.get_pdf_template(size.size)
    with open(file, "rb") as f:
        data = f.read()

    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=" + size.size + ".pdf"
    return response


def list_templates(request):
    """List off all the available templates for download.
    Eventually, this will be based on active item catalog records,
    sorted by type, with linked PDF templates.
    """
    # all_pdfs = fs_api.get_pdf_templates()

    active_pdf_list = []
    prod_categories = []
    prod_main_categories = []
    items_without_category = ItemCatalog.objects.filter(
        active=True, workflow__name="Foodservice", productsubcategory=None
    )

    # for type in workflow_app_defs.PRODUCT_CATEGORIES:
    for type in ProductSubCategory.objects.all().order_by(
        "main_category", "sub_category"
    ):
        all_active_items = type.itemcatalog_set.filter(
            active=True, workflow__name="Foodservice"
        )
        # If there are items in the category, use it.
        if all_active_items:
            prod_categories.append(type)
            if type.get_main_category_display() not in prod_main_categories:
                prod_main_categories.append(type.get_main_category_display())

    pagevars = {
        "page_title": "Foodservice Templates",
        "prod_categories": prod_categories,
        "prod_main_categories": prod_main_categories,
        "items_without_category": items_without_category,
        "pdf_location": settings.FSB_TEMPLATES,
    }

    return render(request, "item_catalog/list_templates.html", context=pagevars)
