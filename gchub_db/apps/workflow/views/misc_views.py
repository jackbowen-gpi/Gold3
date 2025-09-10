"""Misc. Views"""

import os
from datetime import timedelta

from django import forms
from django.db.models import Sum
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from gchub_db.apps.workflow.app_defs import (
    PROD_SUBSTRATE_DOUBLE_POLY,
    PROD_SUBSTRATE_SINGLE_POLY,
)
from gchub_db.apps.workflow.models import (
    BeverageBrandCode,
    BeverageCenterCode,
    BeverageLiquidContents,
    Charge,
    Item,
    ItemColor,
    Job,
)
from gchub_db.includes import fs_api, general_funcs
from gchub_db.includes.gold_json import JSMessage


class EndCodeForm(ModelForm):
    class Meta:
        model = BeverageLiquidContents
        fields = "__all__"


class FileUploadForm(forms.Form):
    """Handle file uploads to general drop folder."""

    file = forms.FileField()


def code_manager(request):
    """Page to manage Beverage Center & End codes."""
    codes = BeverageBrandCode.objects.all().order_by("name")

    pagevars = {
        "page_title": "Beverage Brand Codes",
        "codes": codes,
    }
    return render(request, "workflow/misc/beverage/code_manager.html", context=pagevars)


def code_manager_edit(request, code_id):
    """Page to edit Beverage Center & End codes."""
    code = BeverageBrandCode.objects.get(id=code_id)
    if request.POST:
        form = CodeEditForm(request, request.POST, instance=code)
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
        add_form = CodeEditForm(request, instance=code)
        pagevars = {
            "page_title": "Beverage Brand Codes",
            "add_form": add_form,
            "code_id": code_id,
            "code": code,
        }

        return render(
            request, "workflow/misc/beverage/code_manager_edit.html", context=pagevars
        )


class CodeEditForm(ModelForm):
    """Form to edit Beverage Center & End codes."""

    def __init__(self, request, *args, **kwargs):
        super(CodeEditForm, self).__init__(*args, **kwargs)
        self.fields["code"].label = "Code"
        self.fields["name"].label = "Name"

    class Meta:
        model = BeverageBrandCode
        fields = "__all__"


class CenterCodeForm(ModelForm):
    """Form to add additional center codes for Beverage (old nomenclature)"""

    class Meta:
        model = BeverageCenterCode
        fields = "__all__"


class BrandCodeForm(ModelForm):
    """Form to add additional brand codes for Beverage."""

    class Meta:
        model = BeverageBrandCode
        fields = "__all__"


def add_centercode(request, code="center"):
    """AJAX save to enter a new center code for Beverage."""
    if request.POST:
        # Select correct form to use.
        if code == "center":
            form = CenterCodeForm(request.POST)
        else:
            form = BrandCodeForm(request.POST)
        # Stop! Validate and save it.
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("add_code_complete"))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:
        if code == "center":
            form = CenterCodeForm()
        else:
            form = BrandCodeForm()
        pagevars = {
            "page_title": "Create New Center/Brand Code",
            "form": form,
        }
        return render(
            request, "workflow/misc/beverage/add_centercode.html", context=pagevars
        )


def add_endcode(request):
    """AJAX save to enter a new end (liquid) code for Beverage."""
    if request.POST:
        form = EndCodeForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("add_code_complete"))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:
        pagevars = {
            "page_title": "Create New End (Liquid) Code",
            "form": EndCodeForm(),
        }
        return render(
            request, "workflow/misc/beverage/add_endcode.html", context=pagevars
        )


def gen_doc_upload(request):
    """Upload a file from the database to a general folder on Beverage."""
    if request.method == "POST" and request.FILES.get("file", False):
        fileform = FileUploadForm(request.POST, request.FILES)
        if fileform.is_valid():
            path = fs_api.get_beverage_drop_folder()
            destination = open(os.path.join(path, request.FILES["file"].name), "wb+")
            for chunk in request.FILES["file"]:
                destination.write(chunk)
            destination.close()
            return HttpResponseRedirect(reverse("misc_gen_doc_upload_complete"))
        else:
            for error in fileform.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        fileform = FileUploadForm()

        pagevars = {
            "fileform": fileform,
        }

        return render(
            request, "workflow/misc/popups/gen_doc_upload.html", context=pagevars
        )


def data_trends_main(request):
    """Main page, navigate trend types."""
    pagevars = {
        "page_title": "Trends",
    }

    return render(request, "workflow/misc/trends/data_trends.html", context=pagevars)


@cache_page(60 * 10080)
def data_trends_volume(request):
    """Page of trends in data collected. (Avg. colors/items, etc..)"""
    EXCEPTION_STATUSES = (
        "Cancelled",
        "Hold",
        "Hold for Art",
    )
    REL_BILLING_SCALE_FACTOR = 550

    # Calculate overall trends.
    fsb_jobs = Job.objects.filter(workflow__name="Foodservice").exclude(
        status__in=EXCEPTION_STATUSES
    )
    fsb_items = Item.objects.filter(job__workflow__name="Foodservice").exclude(
        job__status__in=EXCEPTION_STATUSES
    )
    fsb_colors = ItemColor.objects.filter(
        item__job__workflow__name="Foodservice"
    ).exclude(item__job__status__in=EXCEPTION_STATUSES)

    fsb_items_per_job = float(fsb_items.count()) / float(fsb_jobs.count())
    fsb_colors_per_item = float(fsb_colors.count()) / float(fsb_items.count())

    today = general_funcs._utcnow_naive().date()
    # Set end year range -- only calculating data for current year if current
    # month is June or later.
    if today.month >= 6:
        end_year = today.year + 1
    else:
        end_year = today.year

    fsb_by_year = {}
    for year in range(2000, end_year):
        jobs = fsb_jobs.filter(creation_date__year=year)
        items = fsb_items.filter(job__creation_date__year=year)
        colors = fsb_colors.filter(item__job__creation_date__year=year)
        charges = Charge.objects.filter(invoice_date__year=year).aggregate(
            total=Sum("amount")
        )["total"]

        num_items = items.count()
        num_jobs = jobs.count()
        num_Aquality_items = items.filter(quality="A").count()

        items_per_job = float(num_items) / float(num_jobs)
        colors_per_item = float(colors.count()) / float(num_items)
        fsb_by_year[year] = {
            "items_per_job": items_per_job,
            "colors_per_item": colors_per_item,
            "num_items": num_items,
            "num_jobs": num_jobs,
            "num_Aquality_items": num_Aquality_items,
            "charges": float(charges) / float(REL_BILLING_SCALE_FACTOR),
        }

    pagevars = {
        "page_title": "Trends",
        "fsb_items_per_job": fsb_items_per_job,
        "fsb_colors_per_item": fsb_colors_per_item,
        "fsb_by_year": fsb_by_year,
        "billing_scale_factor": REL_BILLING_SCALE_FACTOR,
    }

    return render(
        request, "workflow/misc/trends/data_trends_volume.html", context=pagevars
    )


@cache_page(60 * 10080)
def data_trends_cuptype(request):
    """Trends in type of cup by season."""
    EXCEPTION_STATUSES = (
        "Cancelled",
        "Hold",
        "Hold for Art",
    )

    SPRING_MONTHS = (
        3,
        4,
        5,
    )
    SUMMER_MONTHS = (
        6,
        7,
        8,
    )
    FALL_MONTHS = (
        9,
        10,
        11,
    )
    WINTER_MONTHS = (
        12,
        1,
        2,
    )

    spring_hot = 0
    spring_cold = 0
    summer_hot = 0
    summer_cold = 0
    fall_hot = 0
    fall_cold = 0
    winter_hot = 0
    winter_cold = 0

    today = general_funcs._utcnow_naive().date()
    five_years_ago = today + timedelta(days=-2190)

    fsb_items = (
        Item.objects.filter(
            job__workflow__name="Foodservice",
            creation_date__range=(five_years_ago, today),
        )
        .exclude(job__status__in=EXCEPTION_STATUSES)
        .exclude(job__salesperson__username="Sharon_Ault")
        .select_related()
    )
    for item in fsb_items:
        if item.item_status == "Complete":
            if item.creation_date.month in SPRING_MONTHS:
                if item.size.product_substrate == PROD_SUBSTRATE_DOUBLE_POLY:
                    spring_cold += 1
                elif item.size.product_substrate == PROD_SUBSTRATE_SINGLE_POLY:
                    spring_hot += 1
            elif item.creation_date.month in SUMMER_MONTHS:
                if item.size.product_substrate == PROD_SUBSTRATE_DOUBLE_POLY:
                    summer_cold += 1
                elif item.size.product_substrate == PROD_SUBSTRATE_SINGLE_POLY:
                    summer_hot += 1
            elif item.creation_date.month in FALL_MONTHS:
                if item.size.product_substrate == PROD_SUBSTRATE_DOUBLE_POLY:
                    fall_cold += 1
                elif item.size.product_substrate == PROD_SUBSTRATE_SINGLE_POLY:
                    fall_hot += 1
            elif item.creation_date.month in WINTER_MONTHS:
                if item.size.product_substrate == PROD_SUBSTRATE_DOUBLE_POLY:
                    winter_cold += 1
                elif item.size.product_substrate == PROD_SUBSTRATE_SINGLE_POLY:
                    winter_hot += 1

    pagevars = {
        "page_title": "Trends",
        "spring_hot": spring_hot,
        "spring_cold": spring_cold,
        "summer_hot": summer_hot,
        "summer_cold": summer_cold,
        "fall_hot": fall_hot,
        "fall_cold": fall_cold,
        "winter_hot": winter_hot,
        "winter_cold": winter_cold,
    }

    return render(
        request, "workflow/misc/trends/data_trends_cuptype.html", context=pagevars
    )


@cache_page(60 * 10080)
def data_trends_quality(request):
    """Trends on quality by year."""
    EXCEPTION_STATUSES = (
        "Cancelled",
        "Hold",
        "Hold for Art",
    )

    today = general_funcs._utcnow_naive().date()
    if today.month >= 6:
        end_year = today.year + 1
    else:
        end_year = today.year

    # Calculate overall trends.
    fsb_items = (
        Item.objects.filter(
            job__workflow__name="Foodservice",
            item_status="Complete",
            size__product_substrate=PROD_SUBSTRATE_DOUBLE_POLY,
        )
        .exclude(job__status__in=EXCEPTION_STATUSES)
        .exclude(job__duplicated_from__isnull=False)
    )
    fsb_by_year = {}
    for year in range(2001, end_year):
        items = fsb_items.filter(job__creation_date__year=year)
        count = float(items.count())
        A_quality_items = items.filter(quality="A").count()
        B_quality_items = items.filter(quality="B").count()
        C_quality_items = items.filter(quality="C").count()
        perc_A = A_quality_items / count * 100
        perc_B = B_quality_items / count * 100
        perc_C = C_quality_items / count * 100
        fsb_by_year[year] = {
            "A_quality_items": A_quality_items,
            "B_quality_items": B_quality_items,
            "C_quality_items": C_quality_items,
            "perc_A": perc_A,
            "perc_B": perc_B,
            "perc_C": perc_C,
            "count": count,
        }

    pagevars = {
        "page_title": "Trends",
        "fsb_by_year": fsb_by_year,
    }

    return render(
        request, "workflow/misc/trends/data_trends_quality.html", context=pagevars
    )
