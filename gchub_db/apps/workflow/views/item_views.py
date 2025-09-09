"""Item Views"""

import json
import os
import re
import shutil
import zipfile
from abc import abstractstaticmethod
from datetime import date, timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.contrib.sites.models import Site
from django.db.models import Q
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from gchub_db.apps.color_mgt.models import ColorDefinition
from gchub_db.apps.joblog.app_defs import *
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models import (
    BeverageBrandCode,
    BeverageCenterCode,
    BeverageLiquidContents,
    Charge,
    ChargeType,
    Item,
    ItemCatalog,
    ItemColor,
    ItemReview,
    ItemSpec,
    ItemTracker,
    ItemTrackerType,
    Job,
    Plant,
    PlatePackage,
    PrintLocation,
    Revision,
    SpecialMfgConfiguration,
)
from gchub_db.includes import fs_api, general_funcs
from gchub_db.includes.form_utils import JSONErrorForm
from gchub_db.includes.gold_json import JSMessage
from gchub_db.includes.widgets import GCH_SelectDateWidget
from gchub_db.middleware import threadlocals

from gchub_db.apps.workflow import app_defs


def _safe_get_site(name):
    try:
        return Site.objects.get(name=name)
    except Exception:
        return None


OUTDATED_PRESS = []
OUTDATED_PRESS = (
    Q(plant__name="Bogata")
    | Q(plant__name="Clinton")
    | Q(plant__name="Duro")
    | Q(plant__name="Flexoconverters")
    | Q(plant__name="Hopkinsville")
    | Q(plant__name="International")
    | Q(plant__name="Jackson")
    | Q(plant__name="Shorewood")
    | Q(plant__name="Wilmington")
    | Q(plant__name="Mobile")
    | Q(plant__name="Ronpak")
    | Q(plant__name="Roses")
    #                  |((Q(plant__name="Kenton") | Q(plant__name="Visalia")) & (Q(press__name="Kidder"))
    | (Q(plant__name="Visalia") & (Q(press__name="BDM")))
)  # )


class ItemForm(ModelForm):
    """Base auto-generated modelform from which the more specialized forms are
    sub-classed.
    """

    class Meta:
        model = Item
        fields = "__all__"


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


def json_get_item_specs(request):
    """This view returns an options list for prototype.js to replace the
    'id_printlocation' select element. This is fired when an item type is selected.
    """
    # Get the Print Location id selected from POST.
    selected_printlocation_id = request.POST.get("id_printlocation", False)
    if request.POST and selected_printlocation_id:
        size = get_object_or_404(Plant, id=selected_printlocation_id)
        # These are all the ItemSpecs for this ItemCatalog.
        specs = size.itemspec_set.filter(active=True)
    else:
        # No ItemCatalog value has been provided, assume an empty list.
        specs = ItemSpec.objects.none()

    if specs:
        # No matching specs for this ItemCatalog, or no ItemCatalog specified.
        retval = ""
        # Generate the options list.
        is_first = True
        for spec in specs:
            if is_first:
                selected_attr = 'selected="selected"'
            retval += '<option value="%d" %s>%s</option>\n' % (
                spec.printlocation.id,
                selected_attr,
                spec.printlocation,
            )
    else:
        # Empty option list HTML.
        retval = '<option value="" selected="selected">---------</option>'
    return HttpResponse(retval)


# Subclass each Production form per workflow.
class ItemFormSAPCarton(ModelForm, JSONErrorForm):
    # Note, bom_number (BEV usage) will be used as the scc_number for FSB
    description = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(plant__name="Marion", active=True),
        required=False,
    )
    workflow = _safe_get_site("Carton")

    distortion = forms.DecimalField(max_digits=10, decimal_places=4, required=False)
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
    upc = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=True
    )
    product_group = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=False
    )
    location = forms.ChoiceField(choices=app_defs.LOCATION_OPTIONS)  # Inside/Outside
    plate_thickness = forms.ChoiceField(
        choices=app_defs.PLATE_THICKNESS, required=False
    )
    graphic_po = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30", "maxsize": "255"}), required=False
    )
    # A read-only field to show the user which carton profile has been selected.
    # The actual carton profile will be set via a hidden field. This is done
    # to prevent the user from manually selecting a carton profile.
    carton_profile_display = forms.CharField()

    class Meta:
        model = Item
        fields = (
            "distortion",
            "one_up_die",
            "step_die",
            "grn",
            "graphic_req_number",
            "print_repeat",
            "coating_pattern",
            "upc",
            "product_group",
            "location",
            "plate_thickness",
            "customer_code",
            "graphic_po",
            "gdd_origin",
            "substrate",
            "gcr",
            "carton_workflow",
            "line_screen",
            "ink_set",
            "print_condition",
            "trap",
            "carton_profile",
            "ecg",
        )

    def __init__(self, *args, **kwargs):
        super(ItemFormSAPCarton, self).__init__(*args, **kwargs)
        # Used to display the current carton profile.
        profile_name = ""
        if self.instance.carton_profile:
            profile_name = self.instance.carton_profile.name
        self.fields["carton_profile_display"] = forms.CharField(
            initial=profile_name,
            required=False,
            widget=forms.TextInput(
                attrs={"size": "45", "maxsize": "255", "readonly": "True"}
            ),
        )


# Subclass each Production form per workflow.
class ItemFormProductionFSB(ModelForm, JSONErrorForm):
    # Note, bom_number (BEV usage) will be used as the scc_number for FSB
    description = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    production_edit_notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )
    workflow = _safe_get_site("Foodservice")
    color = forms.CharField(required=False)
    printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(plant__workflow=workflow, active=True)
        .exclude(OUTDATED_PRESS)
        .order_by("plant__name"),
        required=False,
    )
    platepackage = forms.ModelChoiceField(
        queryset=PlatePackage.objects.filter(workflow=workflow).order_by(
            "platemaker__name"
        ),
        required=False,
    )
    size = forms.ModelChoiceField(
        queryset=ItemCatalog.objects.filter(workflow=workflow, active=True).order_by(
            "size"
        )
    )
    special_mfg = forms.ModelChoiceField(
        queryset=SpecialMfgConfiguration.objects.filter(workflow=workflow).exclude(
            Q(name="Blank-Fed_Big Cylinder")
            | Q(name="Blank-Fed_Small Cylinder")
            | Q(name="Small Cylinder")
            | Q(name="Big Cylinder")
        ),
        required=False,
    )
    steps_with = forms.ModelChoiceField(
        queryset=Item.objects.filter(workflow=workflow), required=False
    )

    class Meta:
        model = Item
        fields = (
            "size",
            "printlocation",
            "platepackage",
            "special_mfg",
            "quality",
            "description",
            "case_pack",
            "annual_use",
            "fsb_nine_digit",
            "wrin_number",
            "upc_number",
            "bom_number",
            "inkbook",
            "proof_type",
            "steps_with",
            "kd_press",
            "proof_type_notes",
        )
        widgets = {
            "proof_type_notes": forms.Textarea(
                attrs={"placeHolder": "Please explain the edits.", "rows": "3"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super(ItemFormProductionFSB, self).__init__(*args, **kwargs)
        self.fields["steps_with"] = forms.ModelChoiceField(
            queryset=Item.objects.filter(
                job=self.instance.job,
                size=self.instance.size,
                printlocation=self.instance.printlocation,
            )
            .exclude(id=self.instance.id)
            .order_by("num_in_job"),
            empty_label="------",
            required=False,
        )
        if self.instance.steps_with:
            self.fields["steps_with"] = forms.ModelChoiceField(
                queryset=Item.objects.filter(
                    job=self.instance.job,
                    size=self.instance.size,
                    printlocation=self.instance.printlocation,
                )
                .exclude(id=self.instance.id)
                .order_by("num_in_job"),
                initial=self.instance.steps_with.id,
                empty_label="------",
                required=False,
            )

        # Override the unicode method on item to display prettier.
        self.fields["steps_with"].label_from_instance = lambda obj: "%s-%s" % (
            str(obj.num_in_job),
            str(obj),
        )
        # Hide the proof type notes unless the proof type is an edits to original type.
        if self.instance.proof_type:
            if not self.instance.proof_type.startswith("EDITS_ORIGINAL"):
                self.fields["proof_type_notes"].widget.attrs["style"] = "display:none"
        else:
            self.fields["proof_type_notes"].widget.attrs["style"] = "display:none"


# Subclass each Production form per workflow.
class ItemFormProductionCarton(ModelForm, JSONErrorForm):
    # Note, bom_number (BEV usage) will be used as the scc_number for FSB
    description = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    production_edit_notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )
    # Carton items need to show FSB things sometimes.
    fsb_workflow = _safe_get_site("Foodservice")
    carton_workflow = _safe_get_site("Carton")

    color = forms.CharField(required=False)
    printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(
            plant__workflow=carton_workflow, active=True
        )
        .exclude(OUTDATED_PRESS)
        .order_by("plant__name"),
        required=False,
    )
    platepackage = forms.ModelChoiceField(
        queryset=PlatePackage.objects.filter(workflow=fsb_workflow).order_by(
            "platemaker__name"
        ),
        required=False,
    )
    size = forms.ModelChoiceField(
        queryset=ItemCatalog.objects.filter(
            workflow=carton_workflow, active=True
        ).order_by("size")
    )
    special_mfg = forms.ModelChoiceField(
        queryset=SpecialMfgConfiguration.objects.filter(workflow=fsb_workflow).exclude(
            Q(name="Blank-Fed_Big Cylinder")
            | Q(name="Blank-Fed_Small Cylinder")
            | Q(name="Small Cylinder")
            | Q(name="Big Cylinder")
        ),
        required=False,
    )
    steps_with = forms.ModelChoiceField(
        queryset=Item.objects.filter(workflow=fsb_workflow), required=False
    )

    class Meta:
        model = Item
        fields = (
            "size",
            "printlocation",
            "platepackage",
            "special_mfg",
            "quality",
            "description",
            "case_pack",
            "annual_use",
            "fsb_nine_digit",
            "wrin_number",
            "upc_number",
            "bom_number",
            "inkbook",
            "proof_type",
            "steps_with",
            "proof_type_notes",
        )
        widgets = {
            "proof_type_notes": forms.Textarea(
                attrs={"placeHolder": "Please explain the edits.", "rows": "3"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super(ItemFormProductionCarton, self).__init__(*args, **kwargs)
        self.fields["steps_with"] = forms.ModelChoiceField(
            queryset=Item.objects.filter(
                job=self.instance.job,
                size=self.instance.size,
                printlocation=self.instance.printlocation,
            )
            .exclude(id=self.instance.id)
            .order_by("num_in_job"),
            empty_label="------",
            required=False,
        )
        if self.instance.steps_with:
            self.fields["steps_with"] = forms.ModelChoiceField(
                queryset=Item.objects.filter(
                    job=self.instance.job,
                    size=self.instance.size,
                    printlocation=self.instance.printlocation,
                )
                .exclude(id=self.instance.id)
                .order_by("num_in_job"),
                initial=self.instance.steps_with.id,
                empty_label="------",
                required=False,
            )
        # Override the unicode method on item to display prettier.
        self.fields["steps_with"].label_from_instance = lambda obj: "%s-%s" % (
            str(obj.num_in_job),
            str(obj),
        )
        # Hide the proof type notes unless the proof type is an edits to original type.
        if self.instance.proof_type:
            if not self.instance.proof_type.startswith("EDITS_ORIGINAL"):
                self.fields["proof_type_notes"].widget.attrs["style"] = "display:none"
        else:
            self.fields["proof_type_notes"].widget.attrs["style"] = "display:none"


class ItemFormProductionBEV(ModelForm, JSONErrorForm):
    """Form for editing Beverage item production data."""

    description = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    bev_center_code = forms.ModelChoiceField(
        queryset=BeverageCenterCode.objects.all().order_by("code"), required=False
    )
    bev_brand_code = forms.ModelChoiceField(
        queryset=BeverageBrandCode.objects.all().order_by("code"),
        required=False,
        widget=forms.HiddenInput,
    )
    bev_liquid_code = forms.ModelChoiceField(
        queryset=BeverageLiquidContents.objects.all().order_by("code"), required=False
    )

    bev_alt_code = forms.CharField(required=False)
    bev_end_code = forms.CharField(required=False)
    workflow = _safe_get_site("Beverage")
    size = forms.ModelChoiceField(
        queryset=ItemCatalog.objects.filter(workflow=workflow, active=True).order_by(
            "size"
        )
    )
    special_mfg = forms.ModelChoiceField(
        queryset=SpecialMfgConfiguration.objects.filter(workflow=workflow),
        required=False,
    )
    production_edit_notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )
    uses_old_distortion = forms.BooleanField(required=False)

    # Item tracker fields.
    label_tracker = forms.ModelChoiceField(
        ItemTrackerType.objects.filter(category__name="Beverage Label"), required=False
    )
    fiber_tracker = forms.ModelChoiceField(
        ItemTrackerType.objects.filter(category__name="Beverage Fiber"), required=False
    )

    nutrition_facts = forms.BooleanField(required=False)

    class Meta:
        model = Item
        fields = (
            "size",
            "bev_center_code",
            "bev_liquid_code",
            "special_mfg",
            "description",
            "upc_number",
            "upc_ink_color",
            "bom_number",
            "num_up",
            "replaces",
            "bev_alt_code",
            "bev_end_code",
            "bev_brand_code",
            "uses_old_distortion",
        )


class ItemFormProductionCON(ModelForm, JSONErrorForm):
    description = forms.CharField(
        widget=forms.TextInput(attrs={"size": "50"}), required=False
    )
    production_edit_notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )
    workflow = _safe_get_site("Container")
    printlocation = forms.ModelChoiceField(
        queryset=PrintLocation.objects.filter(plant__workflow=workflow)
        .exclude(OUTDATED_PRESS)
        .order_by("plant__name"),
        required=False,
    )
    platepackage = forms.ModelChoiceField(
        queryset=PlatePackage.objects.filter(workflow=workflow).order_by(
            "platemaker__name"
        ),
        required=False,
    )
    size = forms.ModelChoiceField(
        queryset=ItemCatalog.objects.filter(workflow=workflow, active=True).order_by(
            "size"
        )
    )

    class Meta:
        model = Item
        fields = (
            "size",
            "printlocation",
            "platepackage",
            "special_mfg",
            "description",
            "upc_number",
            "upc_ink_color",
            "material",
            "length",
            "width",
            "height",
            "ect",
            "num_up",
        )


@csrf_exempt
def item_production_detail(request, item_id):
    """Display production details for an item."""
    item = Item.objects.get(id=item_id)
    logoform = False
    itemform = False

    if item.job.workflow.name == "Foodservice":
        itemform = ItemFormProductionFSB(instance=item)
    elif item.job.workflow.name == "Beverage":
        # See if there are any existing item trackers for fiber or labels.
        try:
            label_tracker = item.get_label_tracker().type.id
        except Exception:
            label_tracker = None
        try:
            fiber_tracker = item.get_fiber_tracker().type.id
        except Exception:
            fiber_tracker = None
        try:
            nutrition_facts = item.get_nutrition_facts()
        except Exception:
            nutrition_facts = False
        tracker_data = {
            "label_tracker": label_tracker,
            "fiber_tracker": fiber_tracker,
            "nutrition_facts": nutrition_facts,
        }
        # Populate the form with item data and existing trackers.
        itemform = ItemFormProductionBEV(instance=item, initial=tracker_data)
    elif item.job.workflow.name == "Container":
        itemform = ItemFormProductionCON(instance=item)
    elif item.job.workflow.name == "Carton":
        itemform = ItemFormProductionCarton(instance=item)
    else:
        itemform = ItemFormProductionFSB(instance=item)

    pagevars = {
        "job": item.job,
        "item": item,
        "itemform": itemform,
        "view": "production",
        "inks_used": ItemColor.objects.filter(item=item).order_by("id"),
    }
    return render(
        request, "workflow/item/ajax/subview_production_detail.html", context=pagevars
    )


def item_sap_detail(request, item_id):
    """Display production details for an item."""
    item = Item.objects.get(id=item_id)
    logoform = False
    itemform = False

    if item.job.workflow.name == "Foodservice":
        itemform = ItemFormProductionFSB(instance=item)
    elif item.job.workflow.name == "Carton":
        itemform = ItemFormSAPCarton(instance=item)
    elif item.job.workflow.name == "Beverage":
        # See if there are any existing item trackers for fiber or labels.
        try:
            label_tracker = item.get_label_tracker().type.id
        except Exception:
            label_tracker = None
        try:
            fiber_tracker = item.get_fiber_tracker().type.id
        except Exception:
            fiber_tracker = None
        try:
            nutrition_facts = item.get_nutrition_facts()
        except Exception:
            nutrition_facts = False
        tracker_data = {
            "label_tracker": label_tracker,
            "fiber_tracker": fiber_tracker,
            "nutrition_facts": nutrition_facts,
        }
        # Populate the form with item data and existing trackers.
        itemform = ItemFormProductionBEV(instance=item, initial=tracker_data)
    elif item.job.workflow.name == "Container":
        itemform = ItemFormProductionCON(instance=item)
    else:
        itemform = ItemFormProductionFSB(instance=item)

    pagevars = {
        "job": item.job,
        "item": item,
        "itemform": itemform,
        "view": "sap",
        "inks_used": ItemColor.objects.filter(item=item).order_by("id"),
    }
    return render(
        request, "workflow/item/ajax/subview_sap_detail.html", context=pagevars
    )


def tiff_rip(request, item_id):
    """Display the Tiff RIP data for each Tiff in the tiff_folder of the item that was
    clicked. Either FlexRip or ImagingEngine should be the RIP Programs.
    """
    item = Item.objects.get(id=item_id)
    # Get the tiffs in the folder of the item (or blank if there is no folder yet)
    try:
        item_tiffs = fs_api.list_item_tiffs(item.job.id, item.num_in_job)
    except Exception:
        item_tiffs = []
    ripTiffs = {}
    for file in item_tiffs:
        # get the tiff filename, dont have to worry about folders cause they dont get returned from fsapi call
        filename = file["file_name"]
        filePartsArr = filename.split(".")
        ending = filePartsArr[-1]
        # only want to show tiff files
        if ending == "tif":
            ripTiffs[filename] = []
            # find the file and open it for reading
            filepath = fs_api.get_item_tiff_path(item.job.id, item.num_in_job, filename)
            data = open(filepath, encoding="ISO-8859-1").read()
            try:
                # search for the start and end tags of the Creator Tool attribute
                colorStart = data.find("<xmp:CreatorTool")
                colorEnd = data.find("</xmp:CreatorTool")
                # +17 will get rid of the start tag and yield just the value
                colorStr = data[colorStart + 17 : colorEnd]
                # regex match FlexRip which either exists or does not within that string
                flexMatch = re.search("FlexRip", colorStr)
                PixelMachine = re.search("PixelMachine", colorStr)
                ImagingMatch = re.search("Imaging Engine", colorStr)

                if flexMatch:
                    ripTiffs[filename].append("FlexRip")
                elif ImagingMatch or PixelMachine:
                    ripTiffs[filename].append("ImagingEngine")
                else:
                    ripTiffs[filename].append("Unknown")
            except Exception:
                # print str(ex)
                ripTiffs[filename].append("Error")

            try:
                if data.find("<egScreen:singlepressDGC>") != -1:
                    curveStart = data.find("<egScreen:singlepressDGC>")
                    curveEnd = data.find("</egScreen:singlepressDGC>")
                    curveStr = data[curveStart + 25 : curveEnd]
                    stratStr = "N/A"
                    # Curve and Strat
                    ripTiffs[filename].append(curveStr)
                    ripTiffs[filename].append(stratStr)
                else:
                    if data.find("<egScreen:autopressDGCreq>") != -1:
                        stratStart = data.find("<egScreen:autopressDGCreq>")
                        stratEnd = data.find("</egScreen:autopressDGCreq>")
                        stratStr = data[stratStart + 26 : stratEnd]
                        # Strat
                        ripTiffs[filename].append(stratStr)
                    else:
                        # Strat
                        ripTiffs[filename].append("N/A")
                    if data.find("<egScreen:autopressDGCCT>") != -1:
                        curveStart = data.find("<egScreen:autopressDGCCT>")
                        curveEnd = data.find("</egScreen:autopressDGCCT>")
                        curveStr = data[curveStart + 25 : curveEnd]
                        # Curve
                        ripTiffs[filename].append(curveStr)
                    else:
                        # Curve
                        ripTiffs[filename].append("N/A")

            except Exception as ex:
                # Curve and Strat
                print(str(ex))
                ripTiffs[filename].append("Error")
                ripTiffs[filename].append("Error")

    pagevars = {"ripTiffs": ripTiffs, "item": item}

    return render(request, "workflow/item/ajax/tiff_rip.html", context=pagevars)


def edit_bev_brand_code(request, item_id):
    item = Item.objects.get(id=item_id)
    new_bev_id = request.POST.getlist("all_brand_codes")[0]
    new_bev_brand_code = BeverageBrandCode.objects.get(id=new_bev_id)

    item.bev_brand_code = new_bev_brand_code
    item.save()

    return HttpResponse(JSMessage("Saved."))


class BevBrandCodeForm(ModelForm):
    all_brand_codes = forms.ModelChoiceField(
        queryset=BeverageBrandCode.objects.all().order_by("code"), required=False
    )

    class Meta:
        model = BeverageBrandCode
        fields = "__all__"


def view_bev_brand_code(request, item_id, bev_brand_code):
    try:
        old_bev_brand_code = BeverageBrandCode.objects.get(id=bev_brand_code)
    except Exception:
        old_bev_brand_code = "None"
    all_brand_codes_form = BevBrandCodeForm()
    item = Item.objects.get(id=item_id)

    pagevars = {
        "job": item.job,
        "old_bev_brand_code": old_bev_brand_code,
        "all_brand_codes_form": all_brand_codes_form,
        "item": item,
    }
    return render(
        request, "workflow/item/ajax/view_bev_brand_code.html", context=pagevars
    )


class ItemFormTimeline(ModelForm, JSONErrorForm):
    class Meta:
        model = Item
        fields = ("fsb_nine_digit",)


class ItemTimelineEdit(ItemFormTimeline):
    """Expands on ItemFormTimeline to incorporate boolean flags to trigger timeline events"""

    proof_out = forms.BooleanField(required=False)
    marketing_review = forms.BooleanField(required=False)
    approve = forms.BooleanField(required=False)
    forecast = forms.BooleanField(required=False)
    forecast_notes = forms.CharField(required=False)
    file_out = forms.BooleanField(required=False)
    proof_notes = forms.CharField(required=False)
    approve_notes = forms.CharField(required=False)
    fileout_notes = forms.CharField(required=False)
    preflight = forms.BooleanField(required=False)
    preflight_notes = forms.CharField(required=False)


class ItemTimelineEditBEV(ItemTimelineEdit):
    """Expands on ItemTimelineEdit for Beverage, adding preflight option"""

    preflight = forms.BooleanField()


#    preflight_notes = forms.CharField(required=False)


@csrf_exempt
def item_timeline_detail(request, item_id):
    """Display item details in the bottom pane."""
    item = Item.objects.get(id=item_id)
    if item.job.workflow.name == "Beverage":
        itemform = ItemTimelineEditBEV(instance=item)
    else:
        itemform = ItemTimelineEdit(instance=item)

    revisions_entered = Revision.objects.filter(item=item_id).order_by("-due_date")

    proof_history = JobLog.objects.filter(
        type__in=[
            JOBLOG_TYPE_ITEM_APPROVED,
            JOBLOG_TYPE_ITEM_PROOFED_OUT,
            JOBLOG_TYPE_ITEM_FILED_OUT,
        ],
        item=item_id,
    ).order_by("-event_time")

    pagevars = {
        "job": item.job,
        "item": item,
        "itemform": itemform,
        "revisions_entered": revisions_entered,
        "view": "timeline",
        "proof_history": proof_history,
    }

    return render(
        request, "workflow/item/ajax/subview_timeline_detail.html", context=pagevars
    )


def delete_item_tracker(request, item_id, item_tracker_id, comment=""):
    """Used to delete item trackers. We don't actually delete them but
    rather give them a removal date and comments. The view filters out trackers
    with a removal date. They are effectively deleted.
    """
    item_tracker = ItemTracker.objects.get(id=item_tracker_id)
    # First, check to see if there are any open marketing reviews for this
    # tracker. Dismiss them if so.
    reviews = ItemReview.objects.filter(
        item=item_tracker.item,
        review_catagory="market",
        review_date__isnull=True,
        entry_comments__icontains=item_tracker.type.name,
    )
    for review in reviews:
        review.review_date = date.today()
        review.resubmitted = True
        review.resub_comments += " Review dismissed."
        review.save()
    # Now get rid of the tracker.
    item_tracker.removal_date = date.today()
    item_tracker.removed_by = threadlocals.get_current_user()
    item_tracker.removal_comments = comment
    item_tracker.save()
    return HttpResponse(JSMessage("Item tracker removed."))


def do_colorkey_queue(request, item_id):
    """Try to make a color key queue item for the jdf"""
    try:
        item = Item.objects.get(id=item_id)
        item.fsb_colorkeys_queue()
        return HttpResponse(JSMessage("Success!"))
    except Item.DoesNotExist:
        return HttpResponse(JSMessage("Error: Item Not Found."))


def ajax_item_save(request, item_id, save_type):
    """AJAX request for saving an item and handling updates associated with each."""
    # Fetch the current record data.
    item = Item.objects.get(id=item_id)

    # Capture current information, which could result in warnings about changes.
    old_fsb_nine_digit = item.fsb_nine_digit
    # Detect change in size.
    oldsize = item.size.size
    # Detect change in plant/press.
    if item.printlocation is None:
        oldplant = "None"
    else:
        oldplant = item.printlocation
    # Detect change in Platemaker/type
    if item.platepackage is None:
        oldplate_maker = "None"
    else:
        oldplate_maker = item.platepackage
    # Detect change in BOM/SCC number.
    old_bom_number = item.bom_number

    # Detect change in UPC number.
    old_upc_number = item.upc_number

    # Detect change in label and fiber trackers.
    old_label_tracker = item.get_label_tracker()
    old_fiber_tracker = item.get_fiber_tracker()
    old_nutrition_facts = item.get_nutrition_facts()

    # Set up item form type based on save_type passed via URL.
    if save_type == "production":
        if item.job.workflow.name == "Foodservice":
            itemform = ItemFormProductionFSB(request.POST, instance=item)
        elif item.job.workflow.name == "Carton":
            itemform = ItemFormProductionCarton(request.POST, instance=item)
        elif item.job.workflow.name == "Beverage":
            # This portion of code will lock down the ability to update the production information
            # if the item has already been preflighted, then only a Beverage Artist can change the info
            ARTIST = Permission.objects.get(codename="in_artist_pulldown")
            BEV_ARTIST = (
                User.objects.filter(groups__in=ARTIST.group_set.all())
                .filter(groups=Group.objects.get(name="Beverage"))
                .filter(is_active=True)
            )
            user = threadlocals.get_current_user()
            if item.can_preflight() or (user in BEV_ARTIST):
                itemform = ItemFormProductionBEV(request.POST, instance=item)
            else:
                return HttpResponse(
                    JSMessage(
                        "You don't have permission to currently make these changes.",
                        is_error=True,
                    )
                )
        elif item.job.workflow.name == "Container":
            itemform = ItemFormProductionCON(request.POST, instance=item)

    elif save_type == "timeline":
        itemform = ItemTimelineEdit(request.POST, instance=item)

    elif save_type == "jdf":
        itemform = ItemFormJDF(request.POST, instance=item)
    elif save_type == "sap":
        itemform = ItemFormSAPCarton(request.POST, instance=item)

    if itemform.is_valid():
        # Save form, regardless if it is production or timeline.
        itemform.save()

        if save_type == "sap":
            item.calculate_item_distortion()
        # Perform events needed when entering in a 9 digit number.
        # Do this regardless of timeline or production update.
        if "fsb_nine_digit" in request.POST:
            if request.POST["fsb_nine_digit"] != "":
                # If it's new or changed...
                if request.POST["fsb_nine_digit"] != old_fsb_nine_digit:
                    item.do_fsb_nine_digit()

        # Now that everything is saved, take care of logging what has changed.
        # Also, trigger certain timeline events that need to occur.
        if save_type == "production":
            # If a production detail save, log what changed.
            logchanges = ""

            # Log any changes to the Size.
            if request.POST["size"]:
                lookup_size = ItemCatalog.objects.get(id=request.POST["size"])
                newsize = lookup_size.size
                if newsize != oldsize:
                    logchanges = (
                        logchanges
                        + "<strong>Size:</strong> ("
                        + oldsize
                        + " to "
                        + newsize
                        + "). "
                    )
            # Log any change to the Print Location
            if "printlocation" in request.POST:
                try:
                    if request.POST["printlocation"]:
                        lookup_plant = PrintLocation.objects.get(
                            id=request.POST["printlocation"]
                        )
                        newplant = lookup_plant
                    else:
                        newplant = "None"
                except PrintLocation.DoesNotExist:
                    newplant = "None"
                if newplant != oldplant:
                    if item.job.workflow.name == "Carton" and newplant is not None:
                        if newplant.plant.name == "Marion":
                            if newplant.press.name in [
                                "7201",
                                "7202",
                                "7203",
                                "7204",
                                "7205",
                                "7207",
                                "7211",
                            ]:
                                item.plate_thickness = "0.067"
                            elif newplant.press.name in ["7206", "7212", "7213"]:
                                item.plate_thickness = "0.045"
                            item.save()
                            item.calculate_item_distortion()
                        elif newplant.plant.name == "Stone Mtn":
                            item.plate_thickness = "0.067"
                            item.save()
                            item.calculate_item_distortion()
                    logchanges = (
                        logchanges
                        + "<strong>Print Location:</strong> ("
                        + str(oldplant)
                        + " to "
                        + str(newplant)
                        + "). "
                    )
                    # If the change is from None to something, set the assignment date,
                    # unless it's been set already.
                    if oldplant == "None" and not item.assignment_date:
                        # First time assigning printlocation
                        item.set_assignement_date()
                        # Now that the item has a printlocation, create templates for it.
                        try:
                            item.do_fsb_copy_die()
                        except Exception:
                            pass
                        try:
                            item.get_master_template()
                        except Exception:
                            pass
                        try:
                            item.do_fsb_make_rectangle()
                        except Exception:
                            pass

            # Log any changes to the Plate Package.
            if "platepackage" in request.POST:
                try:
                    if request.POST["platepackage"]:
                        lookup_platemaker = PlatePackage.objects.get(
                            id=request.POST["platepackage"]
                        )
                        newplatemaker = lookup_platemaker
                    else:
                        newplatemaker = "None"
                except PrintLocation.DoesNotExist:
                    newplatemaker = "None"
                if newplatemaker != oldplate_maker:
                    logchanges = (
                        logchanges
                        + "<strong>Plate Package:</strong> ("
                        + str(oldplate_maker)
                        + " to "
                        + str(newplatemaker)
                        + "). "
                    )

            #            if request.POST.has_key('bom_number'):
            #                if request.POST['bom_number'] != '' and request.POST['bom_number'] != old_bom_number:
            #                    print "SCC Number has changed"
            #                    #pass
            #                    item.do_nine_digit_email()

            if "bom_number" in request.POST or "upc_number" in request.POST:
                if (
                    request.POST["bom_number"] != ""
                    and request.POST["bom_number"] != old_bom_number
                ) or (
                    request.POST["upc_number"] != ""
                    and request.POST["upc_number"] != old_upc_number
                ):
                    # Beverage analysts should not get this email.
                    if item.job.workflow.name != "Beverage":
                        item.do_nine_digit_email()

            # Log any notes that may have been added about why changes occurred.
            if "production_edit_notes" in request.POST:
                logchanges = (
                    logchanges + " Notes: " + request.POST["production_edit_notes"]
                )
            item.do_production_edit(logchanges)

            if item.job.workflow.name == "Beverage":
                # Process changes to the two beverage item trackers for labels and fiber.
                if request.POST["label_tracker"]:
                    new_label_tracker = ItemTrackerType.objects.get(
                        id=request.POST["label_tracker"]
                    )
                    if old_label_tracker:  # Edit an existing tracker
                        if old_label_tracker.type != new_label_tracker:
                            old_label_tracker.type = new_label_tracker
                            old_label_tracker.save()
                        else:
                            pass
                    else:  # Create a new tracker
                        new_tracker = ItemTracker(item=item)
                        new_tracker.type = new_label_tracker
                        new_tracker.addition_date = date.today()
                        new_tracker.edited_by = threadlocals.get_current_user()
                        new_tracker.save()
                if request.POST["fiber_tracker"]:
                    new_fiber_tracker = ItemTrackerType.objects.get(
                        id=request.POST["fiber_tracker"]
                    )
                    if old_fiber_tracker:  # Edit an existing tracker
                        if old_fiber_tracker.type != new_fiber_tracker:
                            old_fiber_tracker.type = new_fiber_tracker
                            old_fiber_tracker.save()
                        else:
                            pass
                    else:  # Create a new tracker
                        new_tracker = ItemTracker(item=item)
                        new_tracker.type = new_fiber_tracker
                        new_tracker.addition_date = date.today()
                        new_tracker.edited_by = threadlocals.get_current_user()
                        new_tracker.save()
                if request.POST.get("nutrition_facts"):
                    print("not false")
                    print(old_nutrition_facts)
                    if not old_nutrition_facts:
                        new_tracker = ItemTracker(item=item)
                        new_tracker.type = ItemTrackerType.objects.get(
                            id=31, name="Nutrition Facts"
                        )
                        new_tracker.addition_date = date.today()
                        new_tracker.edited_by = threadlocals.get_current_user()
                        new_tracker.save()
                else:  # Delete the old tracker
                    try:
                        old_tracker = ItemTracker.objects.get(
                            item=item, type__name="Nutrition Facts"
                        )
                        old_tracker.delete()
                    except Exception:
                        pass

        # End if save_type == 'production's

        # Perform events needed to handle timeline triggers.
        if save_type == "timeline":
            # Check timeline flags, update appropriate fields with dates.
            # Pass notes/excuses user recorded into log.
            if "preflight" in request.POST:
                if request.POST["preflight"] == "on":
                    logthis = ""
                    if "preflight_notes" in request.POST:
                        logthis = request.POST["preflight_notes"]
                    item.do_preflight(logthis)
            # Proofing an item.
            if "proof_out" in request.POST:
                if request.POST["proof_out"] == "on":
                    logthis = ""
                    if "proof_exception" in request.POST:
                        logthis = request.POST["proof_exception"]
                        if "proof_notes" in request.POST:
                            logthis = logthis + " " + request.POST["proof_notes"]
                    item.do_proof(logthis)

            # Approving an item.
            if "approve" in request.POST:
                if request.POST["approve"] == "on":
                    logthis = ""
                    if "approve1_exception" in request.POST:
                        logthis = request.POST["approve1_exception"]
                    if "approve2_exception" in request.POST:
                        logthis = logthis + " " + request.POST["approve2_exception"]
                    if "approve_notes" in request.POST:
                        logthis = logthis + " " + request.POST["approve_notes"]
                    item.do_approve(logthis)

            # Forecasting an item.
            if "forecast" in request.POST:
                if request.POST["forecast"] == "on":
                    logthis = ""
                    if "forecast_notes" in request.POST:
                        logthis = request.POST["forecast_notes"]
                    item.do_forecast(logthis)

            # File out an item.
            if "file_out" in request.POST:
                if request.POST["file_out"] == "on":
                    logthis = ""
                    if "fileout_exception" in request.POST:
                        logthis = request.POST["fileout_exception"]
                        if "fileout_notes" in request.POST:
                            logthis = logthis + " " + request.POST["fileout_notes"]
                    item.do_final_file(logthis)
                    # Create a plate order.
                    item.do_plate_order()

        return HttpResponse(JSMessage("Saved."))
    # End if itemform.is_valid()
    else:
        for error in itemform.errors:
            return HttpResponse(
                JSMessage("Warning! Invalid value for field: " + error, is_error=True)
            )


def do_item_make_bev_die(request, job_num, item_num):
    """Trigger the make bev die action for the given item"""
    try:
        item = Item.objects.get(job__id=job_num, num_in_job=item_num)
        item.do_bev_make_die()
        return HttpResponse(JSMessage("Success!"))
    except Item.DoesNotExist:
        return HttpResponse(JSMessage("Error: Item Not Found."))


def do_item_import_qad(request, job_num, item_id):
    """Try to import QAD data into an item."""
    try:
        item = Item.objects.get(id=item_id)
        item.import_qad_data()
        return HttpResponse(JSMessage("Success!"))
    except Item.DoesNotExist:
        return HttpResponse(JSMessage("Error: Item Not Found."))


def do_copy_qad_data(request, job_num, item_id):
    """From a 'master' item (one that has child 'steps_with' items), copy
    9 digit number, 9 digit number date, upc number and scc number to those
    child records.
    """
    try:
        item = Item.objects.get(id=item_id)
        item_set = item.steps_with_item.all()
        for i in item_set:
            i.fsb_nine_digit = item.fsb_nine_digit
            i.fsb_nine_digit_date = item.fsb_nine_digit_date
            i.upc_number = item.upc_number
            i.bom_number = item.bom_number
            i.save()
        return HttpResponse(JSMessage("Success!"))
    except Exception:
        return HttpResponse(JSMessage("Error occurred copying data."))


def do_copy_fsb_production_template(request, job_num, item_id):
    """Copy the FSB Production template from the templates directory into the
    item subfolder in Final Files.
    """
    try:
        item = Item.objects.get(id=item_id)
        if item.printlocation is not None:
            item.do_fsb_copy_die()
            return HttpResponse(JSMessage("Success!"))
        else:
            return HttpResponse(
                JSMessage(
                    "Error occurred. Item needs a print location for this action.",
                    is_error=True,
                )
            )
    except Exception:
        return HttpResponse(
            JSMessage(
                "Error occurred. Template may not exist or may not be named correctly."
            )
        )


def do_copy_misregistration_pdf(request, job_num, item_id):
    """Copy the misregistration pdf to the job folder with name of the item in question"""
    try:
        misreg_form = "Misregistration.pdf"
        media_location = os.path.join(settings.MEDIA_ROOT, "files")
        item = Item.objects.get(id=item_id)
        job_folder_path = fs_api.get_job_database_path(job_num)
        filename = str(job_num) + "-" + str(item.num_in_job) + "_Misreg_Sim.pdf"

        # check to see if the file exists, we dont want to accidently overwrite
        # an existing filled out form
        if os.path.isfile(os.path.join(job_folder_path, filename)):
            print("exists already - fail silently")
        else:
            shutil.copy(
                os.path.join(media_location, misreg_form),
                os.path.join(job_folder_path, filename),
            )

        return HttpResponse(JSMessage("Success!"))
    except Exception:
        return HttpResponse(
            JSMessage("Error occurred copying the misregistration form.")
        )


def do_copy_nx_plates(request, item_id):
    """Copy an item's tiffs to a remote server so that NX plates can be made.
    This version uploads the tiffs as a zip file to sidestep a problem we had
    trying to create folders on the remote server. They always showed up as
    hidden folders for some reason we couldn't figure out.
    """
    try:
        item = Item.objects.get(id=item_id)

        # Get the path to the remote server we're copying to.
        remote_directory = settings.NXPLATES_DIR

        # Keep a list of tiffs to zip.
        tiffs_to_zip = []
        # Keep a list any duplicate match plate tiffs we might find.
        duplicate_tiffs = []

        # Gather the items tiffs from the job folder.
        tiffs = fs_api.list_item_tiffs(item.job.id, item.num_in_job)
        for tiff in tiffs:
            if "TEMPLATE" not in tiff["file_name"].upper():  # No template tiffs.
                tiffs_to_zip.append(tiff)

        # Check if this is a matchplate item that might have tiffs in an old job.
        matchplate_flag = False
        itemcolors = ItemColor.objects.filter(item=item)
        # Check each itemcolor's plate code against the item's nine digit number.
        # A mis-match means this item is a matchplate.
        for color in itemcolors:
            # Check the nine digit number against the plate code.
            if item.fsb_nine_digit not in color.plate_code:
                matchplate_flag = True
                # Remove this color from the queryset since its tiffs will be in the current item's tiff folder.
                # This seems backwards but we're assured it's correct.
                itemcolors = itemcolors.exclude(id=color.id)

        # Search for and copy matchplate tiffs if we found any above.
        if matchplate_flag and itemcolors:
            for this_color in itemcolors:
                # Find old versions of this itemcolor that used this nine digit number in the plate code. Exclude the current item.
                old_itemcolors = ItemColor.objects.filter(
                    color=this_color.color, plate_code__icontains=item.fsb_nine_digit
                ).exclude(item=item)
                if old_itemcolors:
                    # If there's more than one old item color then record that for the notification email.
                    if len(old_itemcolors) > 1:
                        for dupe_color in old_itemcolors:
                            dupe_message = "%s in job %s-%s" % (
                                dupe_color.color,
                                dupe_color.item.job.id,
                                dupe_color.item.num_in_job,
                            )
                            duplicate_tiffs.append(dupe_message)
                    # If there's just one old item color then go ahead and copy it's tiff.
                    else:
                        old_itemcolor = old_itemcolors[0]
                        # Gather the tiffs for this item.
                        old_tiffs = fs_api.list_item_tiffs(
                            old_itemcolor.item.job.id, old_itemcolor.item.num_in_job
                        )
                        # Check the tiff names to find this color.
                        for old_tiff in old_tiffs:
                            if old_itemcolor.color in old_tiff["file_name"]:
                                tiffs_to_zip.append(old_tiff)

        # Create an open zip file on the remote server.
        zip_name = "%s-%s.zip" % (item.job.id, item.num_in_job)
        remote_zip_file = os.path.join(remote_directory, zip_name)
        zipped_tiff_file = zipfile.ZipFile(remote_zip_file, "w", zipfile.ZIP_DEFLATED)

        # Add each of the tiffs to the remote zip file.
        for tiff in tiffs_to_zip:
            # This creates a zip file which unzips correctly (1 folder w/ tiffs inside)
            zipped_tiff_file.write(
                tiff["file_path"], tiff["file_name"], zipfile.ZIP_DEFLATED
            )
        # Close the remote zip file.
        zipped_tiff_file.close()

        # Send a notification email with a list of the tiffs that were copied.
        mail_body = loader.get_template("emails/on_do_copy_nx_plates.txt")
        mail_subject = "NX plates copied for Item:%s-%s" % (
            item.job.id,
            item.num_in_job,
        )
        # Get a list of the tiff file names that were copied.
        copied_tiffs = []
        for tiff in tiffs_to_zip:
            copied_tiffs.append(tiff["file_name"])
        econtext = {
            "item": item,
            "copied_tiffs": copied_tiffs,
            "duplicate_tiffs": duplicate_tiffs,
        }
        mail_send_to = []
        group_members = User.objects.filter(
            groups__name="EmailNXPlates", is_active=True
        )
        for user in group_members:
            mail_send_to.append(user.email)

        if len(mail_send_to) > 0 and len(tiffs_to_zip) > 0:
            general_funcs.send_info_mail(
                mail_subject, mail_body.render(econtext), mail_send_to
            )

        return HttpResponse(JSMessage("Success!"))

    except Exception:
        return HttpResponse(JSMessage("Error occurred copying the NX plate files."))


def do_copy_master_template(request, job_num, item_id):
    """Copy the mastern template from the templates directory into the
    item subfolder in 1_bit_tiffs.
    """
    try:
        item = Item.objects.get(id=item_id)
        if item.printlocation is not None:
            item.get_master_template()
            return HttpResponse(JSMessage("Success!"))
        else:
            return HttpResponse(
                JSMessage(
                    "Error occurred. Item needs a print location for this action.",
                    is_error=True,
                )
            )
    except Exception:
        return HttpResponse(
            JSMessage(
                "Error occurred. Template may not exist or may not be named correctly."
            )
        )


def do_make_fsb_art_rectangle(request, job_num, item_id):
    """Create the art rectangle in the item folder."""
    try:
        item = Item.objects.get(id=item_id)
        if item.printlocation is not None:
            item.do_fsb_make_rectangle()
            return HttpResponse(JSMessage("Success!"))
        else:
            return HttpResponse(
                JSMessage(
                    "Error occurred. Item needs a print location for this action.",
                    is_error=True,
                )
            )
    except Exception:
        return HttpResponse(
            JSMessage(
                "Error occurred. Perhaps the dimensions for this item are not there."
            )
        )


def do_item_tiff_to_pdf(request, job_num, item_num):
    """Trigger the make do_tif_to_pdf action for the given item"""
    try:
        item = Item.objects.get(job__id=job_num, num_in_job=item_num)
        item.do_tiff_to_pdf()
        return HttpResponse(JSMessage("Success!"))
    except Item.DoesNotExist:
        return HttpResponse(JSMessage("Error: Item Not Found."))


def get_item_proof(request, job_num, item_num, quality="l", log_id=None):
    """Return a given item's proof pdf."""
    job = Job.objects.get(id=job_num)
    workflow = job.workflow.name

    if workflow == "Beverage":
        # Beverage links low res proofs.
        filepath = fs_api.get_item_proof(
            job_num, item_num, quality, proof_log_id=log_id
        )
    else:
        filepaths_array = fs_api.get_item_proof(
            job_num, item_num, quality=None, proof_log_id=log_id, return_first=False
        )

        """
            This blurb will go get all of the filepaths in the proofs folder for an item of a job.
            Sort them from oldest to newest, and return the file that was most recently modified. 
            All of this is currently sorted off of the last modified time stamp.
        """
        # make an object to store the times and filepaths
        pathObj = {}
        for path in filepaths_array:
            # create a time - path relationship per entry
            pathObj[os.path.getmtime(path)] = path
        # sort the keys (times) of pathObj and get the last (newest) one
        most_recent_time = sorted(pathObj)[-1]
        # use that newest time to lookup the path to get the file from
        filepath = pathObj[most_recent_time]
    # return that newest file to the client
    with open(filepath, "rb") as f:
        data = f.read()

    response = HttpResponse(data, content_type="application/pdf")
    if log_id:
        # If this is a past proof, take the log ID and use it to append the
        # date to the back of the PDF name.
        log = JobLog.objects.get(id=log_id)
        response["Content-Disposition"] = (
            "attachment; filename="
            + job_num
            + "-"
            + item_num
            + "_proof_"
            + str(log.event_time.date())
            + ".pdf"
        )
    else:
        response["Content-Disposition"] = (
            "attachment; filename=" + job_num + "-" + item_num + "_proof.pdf"
        )
    return response


def get_stepped_item_proof(request, job_num, item_num, quality="h", log_id=None):
    """Return a given item's stepped proof pdf.
    This function just called get item proof with quality=h
    """
    response = get_item_proof(request, job_num, item_num, quality)

    return response


def get_item_finalfile(request, job_num, item_num):
    """Return a given item's final file/production pdf."""
    job = Job.objects.get(id=job_num)
    item = Item.objects.get(job__id=job_num, num_in_job=item_num)
    workflow = job.workflow.name

    extra = str(item.bev_nomenclature())

    filepath = fs_api.get_item_finalfile(job_num, item_num)
    with open(filepath, "rb") as f:
        data = f.read()

    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=%s-%s_%s.pdf" % (
        job_num,
        item_num,
        extra,
    )
    return response


def get_item_preview_art(request, job_num, item_num):
    """Return a given item's proof pdf."""
    job = Job.objects.get(id=job_num)
    workflow = job.workflow.name
    try:
        filepath = fs_api.get_item_preview_art(job_num, item_num)
        with open(filepath, "rb") as f:
            data = f.read()

        response = HttpResponse(data, content_type="application/pdf")
        response["Content-Disposition"] = (
            "attachment; filename=" + job_num + "-" + item_num + "_preview.pdf"
        )
        return response
    except Exception:
        return HttpResponse("No preview artwork available.")


def get_item_print_seps(request, job_num, item_num):
    """Return a given item's printable separations PDF."""
    job = Job.objects.get(id=job_num)
    workflow = job.workflow.name
    try:
        filepath = fs_api.get_item_print_seps(job_num, item_num)
        with open(filepath, "rb") as f:
            data = f.read()

        # Let's get the original filename from the path.
        fname = filepath.split("/")
        fname = fname[-1]

        response = HttpResponse(data, content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=" + fname
        return response
    except Exception:
        return HttpResponse("No printable separations available.")


def get_item_approval_scan(request, job_num, item_num):
    """Return a given item's proof pdf."""
    job = Job.objects.get(id=job_num)
    workflow = job.workflow.name
    try:
        filepath = fs_api.get_item_approval_pdf(job_num, item_num)
        with open(filepath, "rb") as f:
            data = f.read()

        response = HttpResponse(data, content_type="application/pdf")
        response["Content-Disposition"] = (
            "attachment; filename=" + job_num + "-" + item_num + "_approval.pdf"
        )
        return response
    except Exception:
        return HttpResponse("No approval scan available.")


def item_tiff_download_list(request, item_id):
    """Interface for viewing all TIFFs and information associated with given item."""
    item = Item.objects.get(id=item_id)
    try:
        item_tiffs = fs_api.list_item_tiffs(item.job.id, item.num_in_job)
    except fs_api.InvalidPath:
        item_tiffs = []
    except StopIteration:
        item_tiffs = []
    except fs_api.NoResultsFound:
        item_tiffs = []

    pagevars = {
        "job": item.job,
        "item": item,
        "item_tiffs": item_tiffs,
    }
    return render(
        request, "workflow/item/ajax/subview_tiff_download.html", context=pagevars
    )


def get_single_tiff(request, item_id, filename):
    """Download the selected TIFF."""
    item = Item.objects.get(id=item_id)
    filepath = fs_api.get_item_tiff_path(item.job.id, item.num_in_job, filename)
    with open(filepath, "rb") as f:
        data = f.read()

    response = HttpResponse(data, content_type="image/tiff")
    response["Content-Disposition"] = 'attachment; filename="' + str(filename) + '"'
    return response


def get_zipfile_tiff(request, item_id):
    """Download a zip file of all TIFFs."""
    item = Item.objects.get(id=item_id)

    # Platemaking is used to a certain file naming convention, handle that here.
    send_name = str(item.job.id) + "-" + str(item.num_in_job)
    if item.job.workflow.name == "Beverage":
        send_name = send_name + "-" + str(item.bev_nomenclature())
    if item.job.workflow.name == "Foodservice":
        if item.fsb_nine_digit:
            send_name = str(item.fsb_nine_digit) + "-" + send_name

    # This contains the raw contents of the zip archive containing the tiffs.
    zip_contents = fs_api.get_zip_all_tiffs(item.job.id, item.num_in_job)
    # Set the response up to return the zip with the correct mime type.
    response = HttpResponse(zip_contents, content_type="application/zip")
    # Headers change the file name and how the browser handles the download.
    response["Content-Disposition"] = (
        'attachment; filename="' + send_name + ".zip" + '"'
    )
    return response


@csrf_exempt
def item_billing_detail(request, item_id):
    """Display item billing details in the bottom pane."""
    item = Item.objects.get(id=item_id)
    pagevars = {
        "job": item.job,
        "item": item,
        "view": "billing",
    }
    return render(
        request, "workflow/item/ajax/subview_billing_detail.html", context=pagevars
    )


class InternalItemForm(ModelForm):
    """HUB only item data. Exemptions, etc..."""

    overdue_exempt_reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )
    file_out_exempt_reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )

    class Meta:
        model = Item
        fields = (
            "overdue_exempt",
            "overdue_exempt_reason",
            "file_out_exempt",
            "file_out_exempt_reason",
            "item_situation",
        )


@csrf_exempt
def item_internal_detail(request, item_id):
    """Display item details in the bottom pane."""
    item = Item.objects.get(id=item_id)
    if request.POST:
        form = InternalItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            # Create a carton SAP entry if needed.
            if item.job.check_sap_carton():
                item.job.do_sap_notification()
            return HttpResponse(JSMessage("Saved."))
        # End if itemform.is_valid()
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:
        form = InternalItemForm(instance=item)
        pagevars = {
            "job": item.job,
            "item": item,
            "form": form,
            "view": "internal",
        }
        return render(
            request, "workflow/item/ajax/subview_internal_detail.html", context=pagevars
        )


@csrf_exempt
def item_ink_data(request, item_id):
    """Display item details in the bottom pane."""
    # get the item
    item = Item.objects.get(id=item_id)
    # get the item spec from the item or, if it doesnt have one (beverage) then set to empty
    try:
        item_spec = item.get_item_spec()
    except Exception:
        item_spec = []

    # get all colors for that item
    totalItemColors = ItemColor.objects.filter(item=item).order_by("id")
    # this flag is for displaying ink coverage %'s, and is set to True to start (Dont show)
    hide_ink_coverage = True
    total_ink_coverage_percent = 0.0
    for item_color in totalItemColors:
        try:
            # get the inks coverage per color to 2 decimal places
            decimal = 100 * (
                float(item_color.coverage_sqin) / float(item_spec.total_print_area)
            )
            percentage = "%.2f" % round(decimal, 2)
            # set the ink coverage per color and add it to the total ink coverage
            item_color.percentage = float(percentage)
            # over 100% total coverage is ok, cause some colors will overlap
            total_ink_coverage_percent += float(percentage)
            # if we get any percentages we want to show them to set flag to False (Show)
            hide_ink_coverage = False
        except Exception:
            # if anything goes wrong then just pass
            pass

    item.hide_ink_coverage = hide_ink_coverage

    pagevars = {
        "job": item.job,
        "item": item,
        "view": "ink_data",
        "total_ink_coverage_percent": total_ink_coverage_percent,
        "inks_used": totalItemColors,
    }
    return render(request, "workflow/item/ajax/subview_ink_data.html", context=pagevars)


class ItemFormJDF(ModelForm):
    """Form for JDF related variables."""

    class Meta:
        model = Item
        fields = ("jdf_no_dgc", "jdf_no_step", "uses_pre_distortion")


@csrf_exempt
def item_jdf_detail(request, item_id):
    """Display item JDF details in the bottom pane."""
    item = Item.objects.get(id=item_id)
    form = ItemFormJDF(instance=item)
    jdf_errors = JobLog.objects.filter(item=item, type=JOBLOG_TYPE_JDF_ERROR).order_by(
        "-event_time"
    )

    pagevars = {
        "job": item.job,
        "item": item,
        "form": form,
        "view": "jdf",
        "jdf_errors": jdf_errors,
    }
    return render(
        request, "workflow/item/ajax/subview_jdf_detail.html", context=pagevars
    )


class AddItemColorForm(ModelForm):
    """Form used to add colors to an item manually"""

    definition = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name")
    )
    sequence = forms.ChoiceField(choices=SEQ_CHOICES)
    num_plates = forms.ChoiceField(choices=PLATE_QTY_CHOICES)
    screened = forms.BooleanField(required=False)

    class Meta:
        model = ItemColor
        fields = ("item", "definition", "sequence", "plate_code", "num_plates")


class AddItemColorFormCart(ModelForm):
    """Form used to edit colors to an item"""

    color = forms.IntegerField(min_value=00000000, max_value=99999999, required=True)
    sequence = forms.IntegerField(min_value=1, max_value=10, required=True)
    definition = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=True,
    )

    class Meta:
        model = ItemColor
        fields = ("definition", "sequence", "color")

    # Populate fields in the case of an instance.
    def __init__(self, *args, **kwargs):
        super(AddItemColorFormCart, self).__init__(*args, **kwargs)
        self.fields["definition"].label_from_instance = self.label_from_instance
        self.fields["color"].widget.attrs["style"] = "width:80px"

    @abstractstaticmethod
    def label_from_instance(self):
        return self.name


def add_itemcolor(request, item_id):
    """Add an ItemColor object to an item."""
    item = Item.objects.get(id=item_id)
    workflow = item.job.workflow.name

    if request.POST:
        if item.job.workflow.name == "Carton":
            form = AddItemColorFormCart(request.POST)
        else:
            form = AddItemColorForm(request.POST)
        if form.is_valid():
            if item.job.workflow.name == "Carton":
                color = ItemColor()
                color.item = item
                colorDef = ColorDefinition.objects.get(id=request.POST["definition"])
                if colorDef.name == "Match Color":
                    color.hexvalue = request.POST["changePicker"]
                    color.definition = colorDef
                    color.sequence = request.POST["sequence"]
                    color.color = request.POST["color"]
                else:
                    color.hexvalue = colorDef.hexvalue
                    color.definition = colorDef
                    color.sequence = request.POST["sequence"]
                    color.color = request.POST["color"]
                color.save()
                color.item.save()
            else:
                save_color = form
                save_color.save()
                # After saving the ID to the color definition,
                # Import the color name and hexvalue into the ItemColor, resave.
                color = ItemColor.objects.get(id=save_color.instance.id)
                lookup_color = ColorDefinition.objects.get(id=color.definition.id)
                color.color = lookup_color.name
                if form.cleaned_data["screened"]:
                    # Add "Screened" to the color name.
                    color.color += " Screened"
                color.hexvalue = lookup_color.hexvalue
                color.save()
                if color.item.job.workflow.name == "Beverage":
                    color.item.save()

            return HttpResponse(JSMessage("Edited."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:
        if item.job.workflow.name == "Carton":
            form = AddItemColorFormCart()
        else:
            form = AddItemColorForm()
        pagevars = {
            "item": item,
            "form": form,
        }
        return render(
            request, "workflow/item/ajax/add_itemcolor.html", context=pagevars
        )


class ItemColorForm(ModelForm):
    """Form used to edit colors to an item"""

    screened = forms.BooleanField(required=False)

    class Meta:
        model = ItemColor
        fields = ("definition", "sequence", "plate_code", "num_plates")

    # Populate fields in the case of an instance.
    def __init__(self, *args, **kwargs):
        super(ItemColorForm, self).__init__(*args, **kwargs)
        self.fields["definition"] = forms.ModelChoiceField(
            queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
            required=False,
        )
        if self.instance.id:
            self.fields["definition"] = forms.ModelChoiceField(
                queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
                initial=self.instance.definition.id,
            )
            self.fields["sequence"] = forms.ChoiceField(
                choices=SEQ_CHOICES, initial=self.instance.sequence
            )
            self.fields["num_plates"] = forms.ChoiceField(
                choices=PLATE_QTY_CHOICES, initial=self.instance.num_plates
            )


class ItemColorFormFSB(ModelForm):
    """Form used to edit colors to an item"""

    class Meta:
        model = ItemColor
        fields = ("plate_code",)


class ItemColorFormCart(ModelForm):
    """Form used to edit colors to an item"""

    color = forms.IntegerField(min_value=00000000, max_value=99999999, required=True)
    sequence = forms.IntegerField(min_value=1, max_value=10, required=True)
    definition = forms.ModelChoiceField(
        queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
        required=True,
    )

    class Meta:
        model = ItemColor
        fields = ("definition", "sequence", "color")

    # Populate fields in the case of an instance.
    def __init__(self, *args, **kwargs):
        super(ItemColorFormCart, self).__init__(*args, **kwargs)

        if self.instance.id:
            self.fields["definition"] = forms.ModelChoiceField(
                queryset=ColorDefinition.objects.filter(coating="C").order_by("name"),
                initial=self.instance.definition.id,
            )
            self.fields["definition"].label_from_instance = self.label_from_instance
            self.fields["sequence"].widget.value = self.instance.sequence
            self.fields["color"].widget.attrs["style"] = "width:80px"
            self.fields["color"].widget.value = self.instance.color

    # This function makes the color definition show as just the colordefinition name, overwriting the
    # __unicode__ function on the model
    @abstractstaticmethod
    def label_from_instance(self):
        return self.name


def change_itemcolor(request, color_id):
    """Form to change a color for an ItemColor object attached to an item."""
    color = ItemColor.objects.get(id=color_id)
    workflow = color.item.job.workflow.name

    if request.POST:
        if workflow == "Foodservice" or workflow == "Carton":
            if color.item.job.workflow.name == "Carton":
                form = ItemColorFormCart(request.POST, instance=color)
            else:
                form = ItemColorFormFSB(request.POST, instance=color)
        else:
            form = ItemColorForm(request.POST, instance=color)
        if form.is_valid():
            if color.item.job.workflow.name == "Carton":
                colorDef = ColorDefinition.objects.get(id=request.POST["definition"])
                if colorDef.name == "Match Color":
                    color.hexvalue = request.POST["changePicker"]
                    color.definition = colorDef
                    color.sequence = request.POST["sequence"]
                    color.color = request.POST["color"]
                else:
                    color.hexvalue = colorDef.hexvalue
                    color.definition = colorDef
                    color.sequence = request.POST["sequence"]
                    color.color = request.POST["color"]
                color.save()
            else:
                save_color = form
                save_color.save()
                # After saving the ID to the color definition,
                # Import the color name and hexvalue into the ItemColor, resave.
                color = ItemColor.objects.get(id=color_id)
                # Some colors like QPOs don't have color definitions. Skip those.
                if color.definition:
                    lookup_color = ColorDefinition.objects.get(id=color.definition.id)
                    color.color = lookup_color.name
                    # FSB colors won't have a field for screened so don't check for it.
                    if not workflow == "Foodservice":
                        if form.cleaned_data["screened"]:
                            # Add "Screened" to the color name.
                            color.color += " Screened"
                    color.hexvalue = lookup_color.hexvalue
                    color.save()
            return HttpResponse(JSMessage("Edited."))
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )

    else:
        if workflow == "Foodservice":
            form = ItemColorFormFSB(instance=color)
        elif workflow == "Carton":
            form = ItemColorFormCart(instance=color)
        else:
            if color.color.endswith(" Screened"):
                form = ItemColorForm(instance=color, initial={"screened": True})
            else:
                form = ItemColorForm(instance=color)

        pagevars = {
            "color": color,
            "form": form,
        }

        return render(
            request, "workflow/item/ajax/change_itemcolor.html", context=pagevars
        )


def delete_itemcolor(request, color_id):
    """Deletes a color on an item."""
    color = ItemColor.objects.get(id=color_id)
    color.delete()
    # Save item so Beverage nomenclature recalculates, then reload divs in AJAX.
    color.item.save()
    return HttpResponse(JSMessage("Deleted."))


def delete_item(request, item_id):
    """Deletes an item from a job."""
    item = Item.objects.get(id=item_id)
    item.delete_folder()
    item.delete()
    return HttpResponse(JSMessage("Item deleted."))


class ChargeForm(ModelForm):
    """Form for adding billing charges to an item."""

    def __init__(self, *args, workflow=None, **kwargs):
        super(ChargeForm, self).__init__(*args, **kwargs)
        # we pass in workflow here to filter charges so we dont add beverage to foodservice and visa versa
        if workflow is not None:
            self.fields["description"].queryset = ChargeType.objects.filter(
                workflow=workflow, active=True
            ).order_by("-category", "type")

    class Meta:
        model = Charge
        fields = "__all__"

    comments = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "3"}), required=False
    )


@csrf_exempt
def edit_billing(request, charge_id):
    """Form to edit a charge, and save the edits."""
    current_data = Charge.objects.get(id=charge_id)
    if request.POST:  # If edit form was submitted.
        # pass in workflow to filter the charges we can add to this item
        chargeform = ChargeForm(
            request.POST, instance=current_data, workflow=current_data.item.job.workflow
        )
        if chargeform.is_valid():
            chargeform.save()
            return HttpResponse(JSMessage("Edited."))
        else:
            for error in chargeform.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:  # If edit form was requested.
        # pass in workflow to filter the charges we can add to this item
        chargeform = ChargeForm(
            instance=current_data, workflow=current_data.item.job.workflow
        )
        permission = Permission.objects.get(codename="in_artist_pulldown")
        artists = User.objects.filter(
            is_active=True, groups__in=permission.group_set.all()
        ).order_by("username")
        current_artist = threadlocals.get_current_user()
        pagevars = {
            "chargeform": chargeform,
            "charge": current_data,
            "artists": artists,
            "current_artist": current_artist,
        }
        return render(
            request, "workflow/item/ajax/item_edit_charge.html", context=pagevars
        )


def delete_billing(request, charge_id):
    """Deletes a single charge on an item."""
    charge = Charge.objects.get(id=charge_id)
    charge.delete()
    return HttpResponse(JSMessage("Deleted."))


@csrf_exempt
def add_item_charge(request, item_id):
    """AJAX save to add a charge to a single item."""
    if request.POST:
        # Dont need to add workflow here because this takes us back to the main billing page
        chargeform = ChargeForm(request.POST)

        if chargeform.is_valid():
            charge = Charge()
            charge = chargeform
            charge.save()
            return HttpResponse(JSMessage("Added."))
        else:
            for error in chargeform.errors:
                return HttpResponse(
                    JSMessage("Invalid value for field: " + error, is_error=True)
                )
    else:
        item = Item.objects.get(id=item_id)
        # pass in workflow to filter the charges we can add to this item
        chargeform = ChargeForm(workflow=item.job.workflow)
        permission = Permission.objects.get(codename="in_artist_pulldown")
        artists = User.objects.filter(
            is_active=True, groups__in=permission.group_set.all()
        ).order_by("username")
        current_artist = threadlocals.get_current_user()

        # This overrides the options for charge description, filtering by workflow.
        charge_options = ChargeType.objects.filter(
            workflow=item.job.workflow, active=True
        ).order_by("-category", "type")

        pagevars = {
            "item": item,
            "chargeform": chargeform,
            "form": "test",
            "charge_options": charge_options,
            "artists": artists,
            "current_artist": current_artist,
        }

        return render(
            request, "workflow/item/ajax/item_add_charge.html", context=pagevars
        )


class RevisionForm(ModelForm):
    """Form for entering a revision for an item."""

    apply_to_all = forms.BooleanField(required=False)
    # Due date should default to five days from now.
    due_date = forms.DateField(widget=GCH_SelectDateWidget)

    class Meta:
        model = Revision
        fields = ("item", "due_date", "comments")

    def __init__(self, *args, **kwargs):
        super(RevisionForm, self).__init__(*args, **kwargs)
        # This needs to be set here and not in the class definition.
        """
        This set up checks the days between the current date and the date 
        of the revision. If it sees any weekends it skips over them. This way
        the default due date won't land on a weekend and the production artist
        will have 5 business days to work on the revision.
        """
        counter = 5
        current_day = date.today()
        # This section makes sure enough working days are given.
        while counter > 0:
            if current_day.isoweekday() == 6 or current_day.isoweekday() == 7:
                pass
            else:
                counter -= 1
            current_day += timedelta(days=1)
        # This section makes sure the due date isn't on the weekend.
        if current_day.isoweekday() == 6:
            current_day += timedelta(days=2)
        elif current_day.isoweekday() == 7:
            current_day += timedelta(days=1)
        else:
            pass
        self.fields["due_date"].initial = current_day


class RevisionFormBev(ModelForm):
    """Form for entering a revision for an item. Beverage also needs to
    add in the type of revision to calculate the cost.
    """

    apply_to_all = forms.BooleanField(required=False)
    # Due date should default to five days from now.
    due_date = forms.DateField(widget=GCH_SelectDateWidget)
    # Select from the 3 charge types for Beverage revisions.
    rev_charge_type = forms.ModelChoiceField(
        queryset=ChargeType.objects.filter(
            workflow__name="Beverage",
            type__in=(
                "Revision (Evergreen Absorbs)",
                "Simple Revision",
                "Average Revision",
                "Complex Revision",
                "Revision - No Charge",
            ),
        ),
        required=True,
    )

    class Meta:
        model = Revision
        fields = ("item", "due_date", "comments")

    def __init__(self, *args, **kwargs):
        super(RevisionFormBev, self).__init__(*args, **kwargs)
        # This needs to be set here and not in the class definition.
        """
        This set up checks the days between the current date and the date 
        of the revision. If it sees any weekends it skips over them. This way
        the default due date won't land on a weekend and the production artist
        will have 3 business days to work on the revision.
        """
        counter = 3
        current_day = date.today()
        # This section makes sure enough working days are given.
        while counter > 0:
            if current_day.isoweekday() == 6 or current_day.isoweekday() == 7:
                pass
            else:
                counter -= 1
            current_day += timedelta(days=1)
        # This section makes sure the due date isn't on the weekend.
        if current_day.isoweekday() == 6:
            current_day += timedelta(days=2)
        elif current_day.isoweekday() == 7:
            current_day += timedelta(days=1)
        else:
            pass
        self.fields["due_date"].initial = current_day


@csrf_exempt
def enter_revision(request, item_id, rev_id=None):
    """Form and AJAX save for entering a revision to 1 or multiple items. If a
    rev_id is passed then we're editing an existing revision.
    """
    item = Item.objects.get(id=item_id)

    # Check to see if we're editing an existing revision.
    if rev_id:
        revision = Revision.objects.get(id=rev_id)
    else:
        revision = None

    if request.POST:
        job_id = item.job.id
        # Handle Beverage revisions, which will need to capture a cost.
        if item.job.workflow.name == "Beverage":
            revisionform = RevisionFormBev(request.POST)
            if revisionform.is_valid():
                # Revision noted in Job Log.
                logthis = ""
                # Go ahead and get the charge description.
                description = ChargeType.objects.get(id=request.POST["rev_charge_type"])
                if "comments" in request.POST:
                    logthis = request.POST["comments"]
                if "apply_to_all" in request.POST:
                    # Should duplicate revision to each checked items in the items_checked array.
                    values = request.POST.getlist("items_checked")

                    all_items = Item.objects.filter(job=job_id)
                    for each_item in all_items:
                        if str(each_item.id) in values:
                            each_item.do_revision(logthis)
                            revision_for_item = revisionform.save(commit=False)
                            revision_for_item.id = None
                            revision_for_item.item = each_item
                            revision_for_item.save()
                            if description.type != "Revision - No Charge":
                                charge = Charge()
                                charge.item = each_item
                                charge.description = description
                                charge.amount = description.actual_charge()
                                charge.save()
                    return HttpResponse(JSMessage("Revisions Entered."))
                else:
                    item.do_revision(logthis)
                    # End Job Log entry.
                    revisionform.save()
                    if description.type != "Revision - No Charge":
                        charge = Charge()
                        charge.item = item
                        charge.description = description
                        charge.amount = description.actual_charge()
                        charge.save()
                    return HttpResponse(JSMessage("Revision Entered."))
            else:
                for error in revisionform.errors:
                    return HttpResponse(
                        JSMessage("Invalid value for field: " + error, is_error=True)
                    )
        # Handle Foodservice and Container revisions.
        else:
            revisionform = RevisionForm(request.POST, instance=revision)
            if revisionform.is_valid():
                # If we're editing a revision just save the changes.
                if revision:
                    # We should make note in the Job Log, too.
                    try:
                        # Grab matching joblog entry and edit it
                        joblog = JobLog.objects.filter(
                            item=revision.item,
                            type=13,
                            event_time__year=revision.creation_date.year,
                            event_time__month=revision.creation_date.month,
                            event_time__day=revision.creation_date.day,
                        ).order_by("-event_time")[0]
                        joblog.log_text = "Revision edited for item %s: %s" % (
                            revision.item.num_in_job,
                            request.POST["comments"],
                        )
                        joblog.save()
                    except Exception:
                        pass
                    revisionform.save()
                    return HttpResponse(JSMessage("Revision Updated."))
                else:
                    # Revision noted in Job Log.
                    if "comments" in request.POST:
                        logthis = request.POST["comments"]
                    if "apply_to_all" in request.POST:
                        # Should duplicate revision to each checked items in the items_checked array.
                        values = request.POST.getlist("items_checked")

                        all_items = Item.objects.filter(job=job_id)
                        for each_item in all_items:
                            if str(each_item.id) in values:
                                each_item.do_revision(logthis)
                                revision_for_item = revisionform.save(commit=False)
                                revision_for_item.id = None
                                revision_for_item.item = each_item
                                revision_for_item.save()
                        return HttpResponse(JSMessage("Revisions Entered."))
                    else:
                        item.do_revision(logthis)
                        # End Job Log entry.
                        revisionform.save()
                        return HttpResponse(JSMessage("Revision Entered."))
            else:
                for error in revisionform.errors:
                    return HttpResponse(
                        JSMessage("Invalid value for field: " + error, is_error=True)
                    )
    else:
        """
        Form to enter a revision for an item.
        """
        if item.job.workflow.name == "Beverage":
            revisionform = RevisionFormBev()
        else:
            revisionform = RevisionForm(instance=revision)

        all_items = Item.objects.filter(job=item.job)

        pagevars = {
            "item": item,
            "all_items": all_items,
            "revision": revision,
            "revisionform": revisionform,
            "form": "test",
        }

        return render(
            request, "workflow/item/ajax/item_add_revision.html", context=pagevars
        )


def delete_revision(request, rev_id):
    """Deletes a single charge on an item."""
    revision = Revision.objects.get(id=rev_id)
    revision.item.do_create_joblog_entry(
        JOBLOG_TYPE_ITEM_REVISION,
        "Revision has been deleted for item %s" % revision.item.num_in_job,
    )
    revision.delete()
    return HttpResponse(JSMessage("Deleted."))


def charge_lookup(request, charge_description, item_id, rush_days):
    """AJAX lookup for the base amount for a given charge type"""
    item = Item.objects.get(id=item_id)
    num_colors = item.itemcolor_set.all().count()
    charge_lookup = ChargeType.objects.get(id=charge_description)

    charge_info = {
        "actual_charge": charge_lookup.actual_charge(
            num_colors, item.quality, int(rush_days), item
        )
    }

    # Encode the dictionary and return it for sending.
    # TODO: clean this up to use JSMessage class
    return HttpResponse(json.dumps(charge_info))


def bev_nomenclature_lookup(
    request,
    size,
    printlocation,
    platepackage,
    bev_alt_code,
    bev_center_code,
    bev_liquid_code,
):
    """Lookup the beverage nomenclature based on the variables passed from AJAX."""
    # print size
    # print printlocation
    # print platepackage
    # print bev_alt_code
    # print bev_center_code
    # print bev_liquid_code
    return HttpResponse(JSMessage("Bev-Nomenclature"))


def item_thumbnail(request, item_id, width=155, generate_thumb=False):
    """Returns the binary data for the item's thumbnail."""
    item = get_object_or_404(Item, id=item_id)
    job_num = item.job.id
    item_num = item.num_in_job
    if generate_thumb:
        fs_api.make_thumbnail_item_finalfile(job_num, item_num, width=int(width))
    thumb_path = fs_api.get_thumbnail_item_finalfile(
        job_num, item_num, width=int(width)
    )
    if thumb_path:
        with open(thumb_path, "rb") as f:
            data = f.read()
        response = HttpResponse(data, content_type="image/png")
        response["Content-Disposition"] = "filename=%d-%d_thumb.png" % (
            job_num,
            item_num,
        )
        return response
    else:
        return HttpResponseNotFound("No thumbnail of this size found.")


def transfer_files_to_concord(request, item_id):
    """Sends item information to Concord"""
    try:
        item = Item.objects.get(id=item_id)
        item.transfer_files_to_concord()
        return HttpResponse(JSMessage("Saved."))
    except Exception as ex:
        return HttpResponse(
            JSMessage("An Error has occurred: " + str(ex), is_error=True)
        )
