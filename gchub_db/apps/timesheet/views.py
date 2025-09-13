# -*- coding: utf-8 -*-
"""
Module gchub_db\apps\timesheet\views.py
"""

from __future__ import unicode_literals

import math
from datetime import timedelta

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission, User
from django.forms import ChoiceField, DateField, IntegerField, ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from gchub_db.apps.timesheet.models import TimeSheet
from gchub_db.apps.workflow.models import Job
from gchub_db.includes import general_funcs
from gchub_db.middleware import threadlocals

HOUR_CHOICES = (
    (0, "0"),
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (4, "4"),
    (5, "5"),
    (6, "6"),
    (7, "7"),
    (8, "8"),
    (9, "9"),
    (10, "10"),
    (11, "11"),
    (12, "12"),
)

# The values of the minutes will be fractions of an hour for easy totaling.
MIN_CHOICES = (
    (0, "00"),
    (0.08, "05"),
    (0.17, "10"),
    (0.25, "15"),
    (0.33, "20"),
    (0.42, "25"),
    (0.5, "30"),
    (0.58, "35"),
    (0.67, "40"),
    (0.75, "45"),
    (0.83, "50"),
    (0.92, "55"),
)


class TimeSheetForm(ModelForm):
    """Form used to fill out timesheets."""

    # Add an extra field to ask the artist for the job number.
    jobnum = IntegerField(required=False)
    # Let the user select hours and minutes.
    hour = ChoiceField(choices=HOUR_CHOICES)
    min = ChoiceField(choices=MIN_CHOICES)

    class Meta:
        model = TimeSheet
        fields = ["artist", "date", "jobnum", "category", "hour", "min", "comments"]

    # Set some default values.
    def __init__(self, *args, **kwargs):
        super(TimeSheetForm, self).__init__(*args, **kwargs)
        # Limit the choice of artists to Clemson artists.
        permission = Permission.objects.get(codename="in_artist_pulldown")
        artists = User.objects.filter(is_active=True, groups__in=permission.group_set.all()).order_by("username")
        self.fields["artist"].queryset = artists
        # Make the date default to today (UTC-naive via helper).
        today = general_funcs._utcnow_naive().date()
        self.fields["date"].initial = today.strftime("%m/%d/%Y")
        self.fields["jobnum"].label = "Job Number"
        self.fields["jobnum"].widget.attrs.update({"autofocus": "autofocus"})
        self.fields["hour"].label = "Hours"
        self.fields["min"].label = "Minutes"
        self.fields["comments"].help_text = "(Limit 500 characters.)"
        self.fields["category"].queryset = self.fields["category"].queryset.order_by("order")

    def clean(self):
        """Make the comments field required if the user selects the misc category."""
        category = self.cleaned_data.get("category")
        comments = self.cleaned_data.get("comments")

        hours = self.cleaned_data.get("hour")
        mins = self.cleaned_data.get("min")

        if hours == "0" and mins == "0":
            msg = "You must add some amount of time for this entry."
            self.add_error("min", msg)

        if category:
            if category.name == "Misc" and not comments:
                msg = "Comments required for 'Misc' category."
                self.add_error("comments", msg)

    def clean_jobnum(self):
        """Make sure there's a job that matches the number the user entered."""
        jobnum = self.cleaned_data["jobnum"]

        # Check if a jobnumber was entered.
        if jobnum is not None:  # This will also catch if jobnum = 0.
            try:
                job = Job.objects.get(id=jobnum)
            except Exception:
                job = False
            # Raise an error if there isn't a job that matches that number.
            if not job:
                raise forms.ValidationError("No such job found.")

        return jobnum


class TimeSheetReportForm(forms.Form):
    """
    Form used when users want to view time sheet entries from a specific date
    range.
    """

    start_date = DateField()
    end_date = DateField()


@login_required
def home(request, user_id=None):
    """
    Main page for timesheets. If a user ID is provided then a manager is
    reviewing and employee's timesheet entries and we show some different
    elements.

    By default this function "starts" at today's date and works backwards X
    number of days. So try not to be confused when the "start" date is more
    recent than the "end" date.
    """
    # Get the user we're reviewing for.
    if user_id:  # A manager is reviewing an employee's timesheet entries.
        user = User.objects.get(id=user_id)
        # Use this flag to hide and show stuff in the template.
        is_manager = True
    else:  # An employee is reviewing their own timesheet entries.
        user = threadlocals.get_current_user()
        is_manager = False

    # Different titles and greeting messages are shown for employees and managers.
    if user_id:
        title = "Timesheets for %s" % user.first_name
        message = "Review %s %s's timesheets." % (user.first_name, user.last_name)
    else:
        title = "My Timesheets"
        message = "Manage your timesheets here."

    # Default to 14 days back from today on the initial page load.
    start_date = general_funcs._utcnow_naive().date()
    days_back_target = 14
    end_date = start_date - timedelta(days=days_back_target - 1)
    reportform = TimeSheetReportForm(
        initial={
            "start_date": start_date.strftime("%m/%d/%Y"),
            "end_date": end_date.strftime("%m/%d/%Y"),
        }
    )

    # Custom start and end dates submitted. Remember we work BACK from the
    # start date so start date is more recent.
    if request.POST:
        reportform = TimeSheetReportForm(request.POST)
        if reportform.is_valid():
            # Read choices from the form.
            start_date = reportform.cleaned_data.get("start_date")
            end_date = reportform.cleaned_data.get("end_date")
            # See how many days we need to go back from the start date.
            time_diff = start_date - end_date + timedelta(days=1)
            days_back_target = time_diff.days

    # Master list. Each entry will be the data for a given date.
    timesheets_by_date = []

    # Iterate back through our days and gather the date, timesheet entries, and
    # total hours for each.
    for days_back in range(0, days_back_target):
        # Make a list of todays data.
        # We'll append in this order: date, timesheet_queryset, total hours.
        todays_data = []
        # Get and append today's date.
        todays_date = start_date - timedelta(days=days_back)
        todays_data.append(todays_date)
        # Get the user's timesheets for this date.
        timesheets = TimeSheet.objects.filter(artist=user, date=todays_date).order_by("id")
        todays_data.append(timesheets)
        # Total up the hours
        total = 0
        for entry in timesheets:
            total += entry.hours
        todays_data.append(total)
        # Add todays data to the master list.
        timesheets_by_date.append(todays_data)

    # Pass today and yesterday's dates so they can be flagged in the template.
    today_check = general_funcs._utcnow_naive().date()
    yesterday_check = general_funcs._utcnow_naive().date() - timedelta(days=1)

    pagevars = {
        "page_title": title,
        "message": message,
        "is_manager": is_manager,
        "timesheets_by_date": timesheets_by_date,
        "today_check": today_check,
        "yesterday_check": yesterday_check,
        "reportform": reportform,
    }

    return render(request, "timesheet/home.html", context=pagevars)


@login_required
def add(request, timesheet_id=None):
    """Page for entering timesheets."""
    # Editing an existing time sheet entry if a timesheet_id was passed.
    try:
        timesheet = TimeSheet.objects.get(id=timesheet_id)
        page_title = "Edit Timesheet Entry"
        if timesheet.job:
            jobnum = timesheet.job.id
        else:
            jobnum = None
        # Split the hours into separate hours and minutes for the form fields.
        min_split = math.modf(timesheet.hours)[0]
        hour_split = int(math.modf(timesheet.hours)[1])
        edit_flag = True
    except Exception:
        timesheet = None
        page_title = "Add Timesheet Entry"
        jobnum = None
        min_split = None
        hour_split = None
        edit_flag = False

    if request.method == "POST":
        form = TimeSheetForm(request.POST, instance=timesheet)
        if form.is_valid():
            form = form.save(commit=False)
            if request.POST.get("jobnum"):
                form.job = Job.objects.get(id=request.POST.get("jobnum"))
            # Total up the hours and minutes.
            form.hours = float(request.POST.get("hour")) + float(request.POST.get("min"))
            form.save()
            if "SubmitAdditional" in request.POST:
                return HttpResponseRedirect(reverse("timesheet_add"))
            else:
                return HttpResponseRedirect(reverse("timesheet_home"))

    else:
        # Default the artist to the current user.
        user = threadlocals.get_current_user()
        form = TimeSheetForm(
            initial={
                "artist": user,
                "jobnum": jobnum,
                "hour": hour_split,
                "min": min_split,
            },
            instance=timesheet,
        )

    # Need to pass the timesheet ID for the delete function.
    if timesheet:
        timesheet_id = timesheet.id
    else:
        timesheet_id = None

    pagevars = {
        "page_title": page_title,
        "form": form,
        "edit_flag": edit_flag,
        "timesheet_id": timesheet_id,
    }

    return render(request, "timesheet/add.html", context=pagevars)


@login_required
def delete(request, timesheet_id):
    """View for deleting timesheets."""
    timesheet = TimeSheet.objects.get(id=timesheet_id)
    timesheet.delete()
    return HttpResponseRedirect(reverse("timesheet_home"))
