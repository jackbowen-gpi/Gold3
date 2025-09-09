"""Job and Item search views"""

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render

from gchub_db.apps.workflow.models import ColorWarning


class WarningModelForm(forms.ModelForm):
    class Meta:
        model = ColorWarning
        fields = (
            "definition",
            "qpo_number",
            "active",
            "dismissed",
            "dismissal_notes",
            "notes",
        )

    def __init__(self, *args, **kwargs):
        super(WarningModelForm, self).__init__(*args, **kwargs)
        self.fields["qpo_number"].widget.attrs["placeholder"] = "Ex: QPO1234"


def add_warning(request):
    errors = []
    warningForm = WarningModelForm()

    if request.POST:
        warningForm = WarningModelForm(request.POST)
        if warningForm.is_valid():
            try:
                # Check and see if a colorwarning with this definition exists already
                warning = ColorWarning.objects.get(
                    definition=warningForm.cleaned_data["definition"]
                )
                errors.append(
                    "Pantone Color - A warning for this color definition already exists"
                )
            except Exception:
                # If there is no color warning then create it
                warningForm.save()
                httpresp = HttpResponseRedirect(
                    "/workflow/color_warning/color_warning/"
                )
                return httpresp
        else:
            for error in warningForm.errors:
                errors.append(error)

    pagevars = {"page_title": "Color Warnings", "form": warningForm, "errors": errors}

    return render(
        request, "workflow/color_warning/add_color_warning.html", context=pagevars
    )


def edit_warning(request, warning_id):
    errors = []
    warning = ColorWarning.objects.get(id=warning_id)

    if request.POST:
        warningForm = WarningModelForm(request.POST, instance=warning)
        if warningForm.is_valid():
            # check to see what warning/definition we are editing
            oldWarning = ColorWarning.objects.filter(id=warning_id)
            # check to see what new warning we want to change to
            newWarning = ColorWarning.objects.filter(
                definition=warningForm.cleaned_data["definition"]
            )
            """
            There are three cases here
            Can edit: If the new and old warnings are the same or if the new warning does not exist
            Can not edit: If the new warning does exist already and is not the old warning
            """
            # len(newWarning) > 0 just checks to make sure we got a new value
            if len(newWarning) > 0:
                # if we got a new value it has to be the same as the old one to edit it.
                if newWarning[0].definition.id == oldWarning[0].definition.id:
                    # If the warning is being dismissed then set active to false.
                    if warningForm.cleaned_data["dismissed"]:
                        warningForm = warningForm.save(commit=False)
                        warningForm.active = False
                        warningForm.save()
                    else:
                        warningForm.save()
                    httpresp = HttpResponseRedirect(
                        "/workflow/color_warning/color_warning/"
                    )
                    return httpresp
                else:
                    # if it is the same as an exisiting warning, throw an error - no duplicates allowed
                    errors.append(
                        "Pantone Color - A warning for this color definition already exists"
                    )
            else:
                # Color warning was not found and we are creating a new one
                warningForm.save()
                httpresp = HttpResponseRedirect(
                    "/workflow/color_warning/color_warning/"
                )
                return httpresp
        else:
            for error in warningForm.errors:
                errors.append(error)
    else:
        warningForm = WarningModelForm(instance=warning)

    page_vars = {
        "page_title": "Edit Color Warnings",
        "warning": warning,
        "form": warningForm,
        "errors": errors,
        "body_wrap_color": "transparent",
    }

    # context_instance = RequestContext(request, {"body_wrap_color": "transparent"})
    return render(
        request, "workflow/color_warning/edit_color_warning.html", context=page_vars
    )


def view_warning(request, warning_id):
    warning = ColorWarning.objects.get(id=warning_id)

    page_vars = {
        "page_title": "View Color Warning",
        "warning": warning,
    }

    return render(
        request, "workflow/color_warning/view_color_warning.html", context=page_vars
    )


def color_warning(request):
    warning_list = ColorWarning.objects.all()

    errors = []
    if len(warning_list) == 0:
        errors.append("There are no Color Warnings")

    pagevars = {
        "page_title": "Color Warnings",
        "warnings": warning_list,
        "errors": errors,
    }

    return render(
        request, "workflow/color_warning/color_warning.html", context=pagevars
    )
