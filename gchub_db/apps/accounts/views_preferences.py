"""The following views are part of the user preferences section."""

from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from gchub_db.apps.accounts.models import UserProfile


def preferences(request):
    """Change User Preferences/Account Settings"""
    # This is pretty empty right now, but maybe it won't be in the future.
    pagevars = {}

    return render(request, "preferences/preferences.html", context=pagevars)


class ContactInfoForm(forms.ModelForm):
    """Form used to edit contact information"""

    # User fields - saved to the User model manually
    first_name = forms.CharField(max_length=150, required=False, label="First Name")
    last_name = forms.CharField(max_length=150, required=False, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    # Username is display-only, not included in form fields

    def __init__(self, request, *args, **kwargs):
        """
        This form takes an additional request argument in order to populate the
        fields from both User and UserProfile models.
        """
        super(ContactInfoForm, self).__init__(instance=request.user.profile, *args, **kwargs)
        # Populate the User fields
        self.fields["first_name"].initial = request.user.first_name
        self.fields["last_name"].initial = request.user.last_name
        self.fields["email"].initial = request.user.email

    class Meta:
        model = UserProfile
        fields = ("phone_number",)


def contact_info(request):
    """Change contact info."""
    if request.POST:
        form = ContactInfoForm(request, request.POST)
        if form.is_valid():
            # Save the UserProfile fields
            form.save()

            # Save the User fields manually
            user = form.instance.user
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            # Username is not editable, so we don't update it
            user.save()

            messages.add_message(request, messages.INFO, "Contact info updated.")
            return HttpResponseRedirect(reverse("preferences"))
    else:
        form = ContactInfoForm(request)

    pagevars = {"form": form, "user": request.user}
    return render(request, "preferences/contact_info.html", context=pagevars)
