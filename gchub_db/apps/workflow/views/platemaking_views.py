"""Platemaking and Plate Reordering Views"""

from datetime import timedelta

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from gchub_db.apps.workflow.models import (
    Item,
    ItemColor,
    Plant,
    Platemaker,
    PlateOrder,
    PlateOrderItem,
)
from gchub_db.includes import general_funcs
from gchub_db.includes.gold_json import JSMessage
from gchub_db.includes.widgets import GCH_SelectDateWidget


class PlateOrderSearchForm(forms.Form):
    """Search form for finding plate orders to reorder."""

    job = forms.IntegerField(min_value=1, max_value=99999, required=False)
    size = forms.CharField(required=False)
    plant = forms.ModelChoiceField(queryset=Plant.objects.all().order_by("name"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(PlateOrderSearchForm, self).__init__(*args, **kwargs)
        self.fields["plant"] = forms.ModelChoiceField(
            queryset=Plant.objects.filter(workflow__name__in=("Beverage",)).order_by("name"),
            required=False,
        )


class PlateOrderSubmitForm(ModelForm):
    """Form used for reordering plates by quantity."""

    quantity1 = forms.IntegerField(max_value=99, min_value=0, required=False)
    quantity2 = forms.IntegerField(max_value=99, min_value=0, required=False)
    quantity3 = forms.IntegerField(max_value=99, min_value=0, required=False)
    quantity4 = forms.IntegerField(max_value=99, min_value=0, required=False)
    quantity5 = forms.IntegerField(max_value=99, min_value=0, required=False)
    quantity6 = forms.IntegerField(max_value=99, min_value=0, required=False)
    instructions = forms.CharField(widget=forms.Textarea(attrs={"rows": "4"}), required=False)
    date_needed = forms.DateField(
        widget=GCH_SelectDateWidget,
        initial=general_funcs._utcnow_naive().date() + timedelta(days=3),
    )

    class Meta:
        model = PlateOrder
        fields = "__all__"


@login_required
def plate_reorder_search(request):
    """Return most recent result matching search criteria"""
    pagevars = {
        "page_title": "Plate Reorder Search Form",
        "form": PlateOrderSearchForm(request),
        "display": "search",
    }

    search_page = render(request, "workflow/platemaking/plate_order_search.html", context=pagevars)

    if request.GET:
        form = PlateOrderSearchForm(request, request.GET)
        if form.is_valid():
            # Call the result view directly for display.
            return PlateReorderSearchResults.as_view()(request)
        else:
            # Errors in form data, return the form with messages.
            for error in form.errors:
                return HttpResponse(JSMessage("Invalid value for field: " + error, is_error=True))
            # return search_page
    else:
        # No POST data, return an empty form.
        return search_page


class PlateReorderList(ListView):
    """Return all pending and completed plate orders."""

    queryset = PlateOrder.objects.filter(
        item__job__workflow__name="Beverage",
        item__job__temp_platepackage__platemaker__name="Shelbyville",
        new_order=False,
    ).order_by("-date_entered", "-id")
    paginate_by = 50
    template_name = "workflow/platemaking/plate_order_list.html"

    def get_context_data(self, **kwargs):
        context = super(PlateReorderList, self).get_context_data(**kwargs)
        context["page_title"] = "Pending and Complete Plate Reorders"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def mark_plateorder_invoiced(request, order_id):
    """Mark the given plate order object as being invoiced today."""
    order = PlateOrder.objects.get(id=order_id)
    order.invoice_date = general_funcs._utcnow_naive().date()
    order.save()

    return HttpResponse(JSMessage("Updated."))


class PlateReorderSearchResults(ListView):
    """Return all pending and completed plate orders."""

    paginate_by = 25
    template_name = "workflow/platemaking/plate_order_search.html"

    # Searching and filtering.
    def get_queryset(self):
        workflow = Site.objects.get(name="Beverage")
        qset = PlateOrder.objects.filter(
            item__job__workflow=workflow,
            item__job__temp_platepackage__platemaker__name="Shelbyville",
        )

        s_job_num = self.request.GET.get("job", "")
        if s_job_num != "":
            qset = qset.filter(item__job__id__icontains=s_job_num.strip())

        s_item_size = self.request.GET.get("size", "")
        if s_item_size != "":
            qset = qset.filter(item__bev_item_name__icontains=s_item_size.strip())

        s_plant = self.request.GET.get("plant", "")
        if s_plant != "":
            qset = qset.filter(item__printlocation__plant=s_plant)

        return qset.order_by("-date_entered")

    def get_context_data(self, **kwargs):
        context = super(PlateReorderSearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Plate Reorder Search Form"
        context["display"] = "results"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


@login_required
def plate_reorder_form(request, order_id):
    """Form for reordering an existing Plate Order"""
    order = PlateOrder.objects.get(id=order_id)
    item = Item.objects.get(id=order.item.id)
    item_colors = ItemColor.objects.filter(item=item)

    pagevars = {
        "page_title": "Plate Reorder Search Form",
        "display": "results",
        "order": order,
        "item": item,
        "item_colors": item_colors,
        "form": PlateOrderSubmitForm(),
    }

    return render(request, "workflow/platemaking/plate_order_form.html", context=pagevars)


def plate_reorder_submit(request, item_id):
    """Handles the submission of a plate reorder request"""
    item = get_object_or_404(Item, id=item_id)
    item_colors = ItemColor.objects.filter(item=item_id)

    form = PlateOrderSubmitForm(request.POST)

    if form.is_valid():
        # make sure that order is not for all zero plates
        # this array is to save the new orders so they can be created all at once later
        newPlateArr = []
        all_zero_order = True
        for i in range(len(item_colors)):
            form_num = i + 1
            new_plate = PlateOrderItem()
            new_plate.color = item_colors[i]
            if "quantity%s" % form_num in request.POST and request.POST["quantity%s" % form_num] != "":
                new_plate.quantity_needed = int(request.POST["quantity%s" % form_num])
            else:
                new_plate.quantity_needed = 0
            if new_plate.quantity_needed > 0:
                # if someone ordered above zero plates then switch the boolean here to save the plate order
                all_zero_order = False
                # only make an item order if it is over 0
                newPlateArr.append(new_plate)
        # make sure that someone did not order all zeros
        if not all_zero_order:
            # If there is an order, save the form which creates the object in DB and then update it
            # with the order information
            form.save()
            new_order = PlateOrder.objects.get(id=form.instance.id)
            new_order.requested_by = request.user
            new_order.new_order = False
            # only save the new order if someone actually wants a positive number of plates
            for plate in newPlateArr:
                plate.order = new_order
                plate.save()

            new_order.save()

            # Prepare an email notification.
            mail_subject = "GOLD Plate Reorder Confirmation: %s" % item.bev_nomenclature()
            mail_body = loader.get_template("emails/on_plate_reorder_submit.txt")
            econtext = {"item": item, "new_order": new_order}
            mail_send_to = [request.user.email]
            # If the plant is Kalamazoo some other folks need to be copied.
            if item.printlocation.plant.name == "Kalamazoo":
                group_members = User.objects.filter(groups__name="EmailEverpackPlatemaking", is_active=True)
                for user in group_members:
                    mail_send_to.append(user.email)
            general_funcs.send_info_mail(mail_subject, mail_body.render(econtext), mail_send_to)

            return HttpResponse(JSMessage("Saved."))
        else:
            return HttpResponse(JSMessage("At least one item quantity has to be greater than 0", is_error=True))
    else:
        # Form is invalid, show an error.
        for error in form.errors:
            return HttpResponse(JSMessage("Invalid value specified: " + error, is_error=True))


class Platemaking(ListView):
    """Display plate orders based on platemaker."""

    paginate_by = 25
    template_name = "workflow/platemaking/platemaking.html"

    # Searching and filtering.
    def get_queryset(self):
        platemaker = self.kwargs["platemaker"]
        qset = PlateOrder.objects.filter(stage2_complete_date__isnull=True).order_by("-id")
        # Unless user can see "All", filter by platemaker.
        if platemaker.lower() != "all":
            platemaker_obj = Platemaker.objects.get(name=platemaker)
            if platemaker.lower() == "kenton":
                qset = qset.filter(
                    item__platepackage__platemaker__name__in=(
                        platemaker,
                        "Accugraphics",
                    )
                )
            else:
                qset = qset.filter(item__platepackage__platemaker=platemaker_obj)
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(Platemaking, self).get_context_data(**kwargs)
        context["page_title"] = "Platemaking Orders"
        context["platemaker"] = self.kwargs["platemaker"]
        context["pending"] = True
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context

    # Require the user to be logged in to GOLD to view.
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Platemaking, self).dispatch(*args, **kwargs)


class PlatemakingCompleted(ListView):
    """Display plate orders based on platemaker."""

    paginate_by = 25
    template_name = "workflow/platemaking/platemaking.html"

    # Searching and filtering.
    def get_queryset(self):
        platemaker = self.kwargs["platemaker"]
        qset = PlateOrder.objects.filter(stage2_complete_date__isnull=False).order_by("-date_entered", "-id")
        # Unless user can see "All", filter by platemaker.
        if platemaker.lower() != "all":
            qset = qset.filter(item__platepackage__platemaker__name=platemaker).order_by("-stage2_complete_date", "-id")
        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(PlatemakingCompleted, self).get_context_data(**kwargs)
        context["page_title"] = "Platemaking Orders"
        context["platemaker"] = self.kwargs["platemaker"]
        context["pending"] = False
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context

    # Require the user to be logged in to GOLD to view.
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlatemakingCompleted, self).dispatch(*args, **kwargs)


def platemaking_canceled(request, order_id):
    """
    Used to cancel plate orders. Gathers up all the plate order items and
    deletes them first. That may be an unnecessary step. I dunno.
    """
    order = PlateOrder.objects.get(id=order_id)
    orderitems = PlateOrderItem.objects.filter(order=order)
    for x in orderitems:
        x.delete()
    order.delete()
    return HttpResponse(JSMessage("Order canceled."))


def platemaking_handle(request, order_id, step):
    order = PlateOrder.objects.get(id=order_id)

    # Step 1 checked off for Films Complete
    if step == "1":
        order.stage1_complete_date = general_funcs._utcnow_naive().date()
        order.save()
        return HttpResponse(JSMessage("Saved."))
    # Step 2 checked off for Plates Complete -
    # This will also cause the Plate Order to no longer show
    # in the Platemaking To-Do list.
    if step == "2":
        order.stage2_complete_date = general_funcs._utcnow_naive().date()
        order.save()
        return HttpResponse(JSMessage("Saved."))
    else:
        return HttpResponse(JSMessage("Some kind of error happened.", is_error=True))
