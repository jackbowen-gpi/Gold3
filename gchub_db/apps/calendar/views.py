"""
Module gchub_db\apps\\calendar\views.py
"""

from __future__ import division

import calendar
import time
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission, User
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from gchub_db.apps.calendar.models import EVENT_TYPES, Event
from gchub_db.includes.gold_json import JSMessage
from gchub_db.middleware import threadlocals

HOUR_CHOICES = (
    ("", ""),
    ("07", "7 am"),
    ("08", "8 am"),
    ("09", "9 am"),
    ("10", "10 am"),
    ("11", "11 am"),
    ("12", "12 pm"),
    ("13", "1 pm"),
    ("14", "2 pm"),
    ("15", "3 pm"),
    ("16", "4 pm"),
    ("17", "5 pm"),
    ("18", "6 pm"),
    ("19", "7 pm"),
)

MIN_CHOICES = (
    ("", ""),
    ("00", ":00"),
    ("15", ":15"),
    ("30", ":30"),
    ("45", ":45"),
)


# Avoid database access at import time; resolve permission-based query lazily.
def _get_artist_permission():
    try:
        return Permission.objects.get(codename="in_artist_pulldown")
    except Exception:
        return None


def _get_clemson_artist_qs():
    perm = _get_artist_permission()
    if perm is None:
        # Return an empty queryset when DB or auth tables aren't ready yet.
        return User.objects.none()
    return User.objects.filter(groups__in=perm.group_set.all()).order_by("username").filter(is_active=True)


class ModelEventForm(ModelForm):
    class Meta:
        model = Event
        fields = ("type", "description", "event_date", "employee")


class NewEventForm(ModelEventForm):
    eventlength = forms.IntegerField(initial="1", help_text="Number of days the event lasts.", required=True)
    email_notice = forms.BooleanField(required=False)
    time_start_hour = forms.ChoiceField(choices=HOUR_CHOICES, required=False)
    time_start_min = forms.ChoiceField(choices=MIN_CHOICES, required=False)
    time_end_hour = forms.ChoiceField(choices=HOUR_CHOICES, required=False)
    time_end_min = forms.ChoiceField(choices=MIN_CHOICES, required=False)
    # Use a lazy queryset so form construction doesn't trigger DB access at import time.
    employee_override = forms.ModelChoiceField(queryset=_get_clemson_artist_qs(), required=False)


@login_required
def month_overview(request, year_num, month_num):
    """Display joblog showing only timeline-related entries."""
    # Create a calendar with the first day of the week being Sunday.
    cal = calendar.Calendar(6)
    current_time = time.localtime()

    year_num = int(year_num)
    month_num = int(month_num)

    if month_num == 1:
        last_month_num = 12
        last_year = year_num - 1
    else:
        last_month_num = month_num - 1
        last_year = year_num

    if month_num == 12:
        next_month_num = 1
        next_year = year_num + 1
    else:
        next_month_num = month_num + 1
        next_year = year_num

    # If no year or month is specified, use the current date.
    if year_num is None:
        year_num = current_time[0]
    if month_num is None:
        month_num = current_time[1]

    isthismonth = False
    if year_num == current_time[0]:
        if month_num == current_time[1]:
            isthismonth = True

    current_day = current_time[2]

    events_for_month = Event.objects.filter(event_date__year=year_num, event_date__month=month_num)

    vacation_used_full = Event.objects.filter(employee__username=request.user.username, type="VA", event_date__year=year_num).count()
    vacation_used_half = Event.objects.filter(employee__username=request.user.username, type="HV", event_date__year=year_num).count()
    vacation_used = vacation_used_full + (vacation_used_half / 2)

    sick_used_full = Event.objects.filter(employee__username=request.user.username, type="SD", event_date__year=year_num).count()
    sick_used_half = Event.objects.filter(employee__username=request.user.username, type="SH", event_date__year=year_num).count()
    sick_used = sick_used_full + (sick_used_half / 2)

    # Return a list of weeks in the month. Each week is represented by a list
    # of days represented by integers. If a day is equal to 0, it isn't in
    # the current month. See the HTML for how this works.
    weeks = cal.monthdayscalendar(year_num, month_num)

    pagevars = {
        "page_title": "Month Overview",
        "events_for_month": events_for_month,
        "isthismonth": isthismonth,
        "current_day": current_day,
        "month_num": month_num,
        "month_name": calendar.month_name[month_num],
        "year": year_num,
        "week_list": weeks,
        "last_month": last_month_num,
        "last_month_name": calendar.month_name[last_month_num],
        "last_year": last_year,
        "next_month": next_month_num,
        "next_month_name": calendar.month_name[next_month_num],
        "next_year": next_year,
        "vacation_used": vacation_used,
        "vacation_total": request.user.profile.total_vacation,
        "sick_used": sick_used,
        "sick_total": request.user.profile.total_sick,
    }

    return render(request, "calendar/month_view.html", context=pagevars)


def event_view(request, event_id):
    """Display details of the day's events."""
    event = Event.objects.get(id=event_id)
    events = Event.objects.filter(event_date=event.event_date)

    pagevars = {
        "event": event,
        "page_title": "Daily Events",
        "events": events,
    }

    return render(request, "calendar/event_view.html", context=pagevars)


def event_delete(request, event_id):
    """Delete the given event."""
    event = Event.objects.get(id=event_id)
    year_num = event.event_date.year
    month_num = event.event_date.month

    event.delete()
    messages.success(request, "You have deleted an event from the calendar.")

    return month_overview(request, year_num, month_num)


def event_add(request, year_num="0", month_num="0", day_num="0"):
    """AJAX save an event to the calendar."""
    # This section checks to see if the current user is a manager. Managers
    # can do a few things regular users can't.
    management = ["James_McCracken", "Sana_Davis", "Shelly_Congdon"]
    user = threadlocals.get_current_user()
    manager = False
    if str(user) in management:
        manager = True

    if request.POST:
        eventform = NewEventForm(request.POST)

        # Make sure the user isn't taking more than 5 consecutive vacation days.
        if request.POST["type"] == "VA" and int(request.POST["eventlength"]) > 5 and not manager:
            message = (
                "Sorry, you need approval from your manager to schedule a vacation that long. Please speak to your manager first."
            )
            return HttpResponse(JSMessage(message, is_error=True))

        # Make sure the user isn't scheduling vacation on a busy day.
        check_event = Event()
        check_event.event_date = request.POST["event_date"]
        check_event.type = request.POST["type"]
        if check_event.overload() and not manager:
            message = (
                "Sorry, there are already too many vacations scheduled for %s. Please speak to your manager first."
                % check_event.event_date
            )
            return HttpResponse(JSMessage(message, is_error=True))

        if eventform.is_valid():
            # Make sure the user isn't taking more than 5 consecutive vacation days.
            if check_event.five_consecutive(request.POST["employee"], int(request.POST["eventlength"])) and not manager:
                message = (
                    "Sorry, you need approval from your manager to schedule "
                    "a vacation over 5 consecutive days. Please speak to your manager first."
                )
                return HttpResponse(JSMessage(message, is_error=True))

            # Make sure the user isn't taking more than 10 vacation days in one month.
            if check_event.ten_in_month(request.POST["employee"], int(request.POST["eventlength"])) and not manager:
                message = "Sorry, you have 10 or more vacations scheduled for this month already. Please speak to your manager first."
                return HttpResponse(JSMessage(message, is_error=True))

            event = Event()
            event = eventform
            newevent = event.save()
            type = event.cleaned_data["type"]
            event_length = int(request.POST["eventlength"])
            description = event.cleaned_data["description"]
            notice = event.cleaned_data["email_notice"]
            start_time_hour = event.cleaned_data["time_start_hour"]
            start_time_min = event.cleaned_data["time_start_min"]
            end_time_hour = event.cleaned_data["time_end_hour"]
            end_time_min = event.cleaned_data["time_end_min"]
            employee_override = str(event.cleaned_data["employee_override"])
            repeater = 1
            dater = event.cleaned_data["event_date"]
            date = str(dater)
            date = date.replace("-", "")

            # Send Manager an email if vacation, leave, doctor, or out.
            if type == "VA" or type == "HV" or type == "LA" or type == "DA" or type == "OO":
                # remapped models.py EVENT_TYPES tuple as a dict
                legend = {
                    "VA": "Vacation - Full Day",
                    "HV": "Vacation - Half Day",
                    "OV": "Office Visit",
                    "OM": "Office Meeting",
                    "BT": "Business Trip",
                    "SD": "Sick Day",
                    "SH": "Sick Half-Day",
                    "HO": "Holiday",
                    "LA": "Leave of Absence",
                    "DA": "Doctor Appt.",
                    "OO": "Out of Office",
                }
                events = Event.objects.filter(event_date=dater)
                # build the day's events into a string for plaintext email sending
                statement = ""
                for each in events:
                    statement += "%s: %s (%s)\r\n" % (
                        legend[each.type],
                        str(each.employee).replace("_", " "),
                        each.description,
                    )
                # assign email contents
                # convert "employee" to a string and get rid of the underscores
                user = str(event.cleaned_data["employee"]).replace("_", " ")
                # manager email goes next
                mail_send_to = []
                group_members = User.objects.filter(groups__name="EmailGCHubManager", is_active=True)
                for manager in group_members:
                    mail_send_to.append(manager.email)
                mail_from = "Gold - Clemson Support <%s>" % settings.EMAIL_SUPPORT
                mail_subject = "New Calendar event for %s" % user
                mail_body = loader.get_template("emails/calendar_email.txt")
                mail_context = {
                    "event": legend[type],
                    "user": user,
                    "description": description,
                    "date": dater,
                    "event_length": event_length,
                    "id": newevent.id,
                    "statement": statement,
                }
                # send the email
                msg = EmailMultiAlternatives(
                    mail_subject,
                    mail_body.render(mail_context),
                    mail_from,
                    mail_send_to,
                )
                msg.content_subtype = "html"
                msg.send()

            # Used when managers assigns an event to another employee
            if employee_override != "None":
                override = User.objects.get(username=employee_override)
                cal = Event.objects.all()[0]
                cal.employee = override
                cal.save()

            if start_time_min == "":
                start_time_min = "00"
            if end_time_min == "":
                end_time_min = "00"

            if start_time_hour != "":
                start_12HourClock = convertTime(start_time_hour, start_time_min)
                description += " @ %s" % start_12HourClock
                if end_time_hour != "":
                    end_12HourClock = convertTime(end_time_hour, end_time_min)
                    description += " - %s" % end_12HourClock
                this_event = Event.objects.all()[0]
                this_event.description = description
                this_event.save()

            if notice:
                if int(month_num) < 10:
                    month_num = "0" + str(month_num)

                if int(day_num) < 10:
                    day_num = "0" + str(day_num)

                if start_time_hour == "":
                    start_time_hour = "08"
                if end_time_hour == "":
                    end_time_hour = "18"
                start_time = start_time_hour + start_time_min
                end_time = end_time_hour + end_time_min

                user = event.cleaned_data["employee"]

                # The type is a nested tuple... ie. (('VA', 'Full Vacation'), ('DO', 'Doctor Appoint.'))
                # Loop through the outter tuple
                # Then check for the event type in the tuple list & pull the counter-part
                event_type = EVENT_TYPES
                for x in event_type:
                    if type in x:
                        event = x[1]
                        break

                filename = "event%s.ics" % date
                data = loader.get_template("emails/calendar_event.ics")
                mail_context = {
                    "email": user.email,
                    "date": date,
                    "event_type": event,
                    "event_descript": description,
                    "time_start": start_time,
                    "time_end": end_time,
                }
                # Create an email message for attaching the invite to.
                mail_list = []
                group_members = User.objects.filter(groups__name="EmailGCHubEmployees", is_active=True)
                for user in group_members:
                    mail_list.append(user.email)

                email = EmailMessage("Office Event Notice", description, user.email, mail_list)
                # Attach the file and specify type.
                email.attach(filename, data.render(mail_context), "text/calendar")
                # Poof goes the mail.
                email.send(fail_silently=False)

            if event_length > 1:
                while repeater < event_length:
                    event_mult = Event()
                    curr_date = eventform.cleaned_data["event_date"] + timedelta(days=repeater)
                    # See if this is a weekday.
                    day_check = curr_date.isoweekday()
                    if day_check == 6 or day_check == 7:  # If this a weekend.
                        repeater = repeater + 1
                        event_length = event_length + 1
                    else:  # This is a weekday.
                        event_mult.event_date = curr_date
                        event_mult.type = eventform.cleaned_data["type"]
                        # Used when manager assigns vacations for other people.
                        if employee_override != "None":
                            event_mult.employee = User.objects.get(username=employee_override)
                        else:
                            event_mult.employee = eventform.cleaned_data["employee"]

                        event_mult.description = eventform.cleaned_data["description"]
                        # Make sure there aren't already too many vacations on this date.
                        if event_mult.overload() and not manager:
                            message = (
                                "Sorry, there are already too many vacations scheduled for %s. Please speak to your manager first."
                                % event_mult.event_date
                            )
                            return HttpResponse(JSMessage(message, is_error=True))
                        else:
                            event_mult.save()
                        repeater = repeater + 1
            messages.success(request, "Your event has been added to the calendar.")
            return HttpResponse(JSMessage("Event Added."))
        else:
            for error in eventform.errors:
                return HttpResponse(JSMessage("Invalid value for field: " + error, is_error=True))
    else:
        eventform = NewEventForm()

        pagevars = {
            "year": year_num,
            "month": month_num,
            "day": day_num,
            "eventform": eventform,
            "manager": manager,
        }

        return render(request, "calendar/add_event.html", context=pagevars)


def convertTime(hour, min):
    if hour < "12":
        return "%s:%s a.m. " % (hour, min)
    else:
        if hour > "12":
            hour = int(hour) - 12
        return "%s:%s p.m. " % (hour, min)
