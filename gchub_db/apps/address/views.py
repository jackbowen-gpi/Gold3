"""Address Views"""

from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.list import ListView

from gchub_db.apps.address.models import Contact
from gchub_db.includes import general_funcs
from gchub_db.includes.gold_json import JSMessage


class ContactForm(ModelForm):
    """Address management form."""

    class Meta:
        model = Contact
        exclude = ("workflow",)


class AddressSearchForm(forms.Form):
    """Form to search through address directory."""

    last_name = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    job_title = forms.CharField(required=False)
    address1 = forms.CharField(required=False)
    address2 = forms.CharField(required=False)
    company = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(required=False)
    country = forms.CharField(required=False)
    zip_code = forms.CharField(required=False)
    phone = forms.CharField(required=False)


@login_required
def address_home(request):
    """Menu page for the Address/Directory"""
    pagevars = {
        "page_title": "Address Main Page",
    }

    return render(request, "address/address_home.html", context=pagevars)


# change this to be the search results
def view_contact(request, contact_id):
    """View address"""
    contact = Contact.objects.get(id=contact_id)
    pagevars = {
        "page_title": "Address Search Results",
        "contact": contact,
    }

    return render(request, "address/view_address.html", context=pagevars)


def edit_contact(request, contact_id):
    """Saves edited contact data."""
    current_data = Contact.objects.get(id=contact_id)
    if request.method == "POST":  # save form
        contactform = ContactForm(request.POST, instance=current_data)
        if contactform.is_valid():
            contactform.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in contactform.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:  # present form
        contactform = ContactForm(instance=current_data)
        pagevars = {
            "page_title": "Address Edit",
            "contact": current_data,
            "contactform": contactform,
        }

        return render(request, "address/address_edit.html", context=pagevars)


def attach_address(request, contact_id):
    """Copies data from address model to workflow/jobaddress model"""
    contact = Contact.objects.get(id=contact_id)

    pagevars = {
        "page_title": "Attach Contact to Job",
        "contact": contact,
    }

    return render(request, "address/attach_contact.html", context=pagevars)


def new_address(request):
    """New Address add form, plus AJAX save of that form."""
    if request.POST:
        contactform = ContactForm(request.POST)
        if contactform.is_valid():
            contact = Contact()
            contact = contactform
            contact.save()
            return HttpResponse(JSMessage("Saved."))
        else:
            for error in contactform.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        contactform = ContactForm()
        pagevars = {
            "page_title": "Add New Contact",
            "contactform": contactform,
        }

        return render(request, "address/address_add.html", context=pagevars)


def delete_address(request, contact_id):
    """Delete an address from the main directory."""
    contact = Contact.objects.get(id=contact_id)
    contact.delete()
    return HttpResponse(JSMessage("Deleted."))


@login_required
def search_address(request):
    """Displays the directory search form."""
    pagevars = {
        "page_title": "Address Search",
        "form": AddressSearchForm(),
    }
    # This is the search page to be re-displayed if there's a problem or no
    # POST data.
    search_page = render(request, "address/search_form.html", context=pagevars)

    if request.GET:
        form = AddressSearchForm(request.GET)
        if form.is_valid():
            # It's easier to store a dict of the possible lookups we want, where
            # the values are the keyword arguments for the actual query.
            qdict = {
                "last_name": "last_name__icontains",
                "first_name": "first_name__icontains",
                "job_title": "job_title__icontains",
                "company": "company__icontains",
                "city": "city__icontains",
                "state": "state__icontains",
                "country": "country__icontains",
                "address1": "address1__icontains",
                "address2": "address2__icontains",
                "zip_code": "zip_code__icontains",
                "phone": "phone__icontains",
            }

            # Then we can do this all in one step instead of needing to call
            # 'filter' and deal with intermediate data structures.
            q_objs = [
                Q(**{qdict[k]: form.cleaned_data[k]})
                for k in qdict.keys()
                if form.cleaned_data.get(k, None)
            ]
            search_results = (
                Contact.objects.select_related().filter(*q_objs).order_by("last_name")
            )

            # Call the result view directly for display.
            return AddressSearchResults.as_view(queryset=search_results)(request)
        else:
            # Errors in form data, return the form with messages.
            return search_page
    else:
        # No POST data, return an empty form.
        return search_page


class AddressSearchResults(ListView):
    """Displays job search results."""

    model = Contact
    paginate_by = 25
    template_name = "address/search_results.html"

    def get_context_data(self, **kwargs):
        context = super(AddressSearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Address Search Results"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context
