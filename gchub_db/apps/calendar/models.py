"""Calender application - tracks events, vacation usage"""

import datetime

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models

# A listing for Event mode's event type.
EVENT_TYPES = (
    ("VA", "Vacation - Full Day"),
    ("HV", "Vacation - Half Day"),
    ("OV", "Office Visit"),
    ("OM", "Office Meeting"),
    ("BT", "Business Trip"),
    ("SD", "Sick Day"),
    ("SH", "Sick Half-Day"),
    ("HO", "Holiday"),
    ("LA", "Leave of Absence"),
    ("DA", "Doctor Appt."),
    ("OO", "Out of Office"),
)


class Event(models.Model):
    """An individual Event to be displayed on the calendar."""

    description = models.CharField(max_length=200)
    type = models.CharField(choices=EVENT_TYPES, max_length=2)
    event_date = models.DateField("Event Date")
    employee = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    limit_to_group = models.ManyToManyField(Group, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def event_icon(self):
        """Icon for given event."""
        retval = "calendar.png"
        if self.type == "VA" or self.type == "HV":
            retval = "car.png"
        elif self.type == "OV":
            retval = "user_suit.png"
        elif self.type == "OM":
            retval = "group.png"
        elif self.type == "BT":
            retval = "map.png"
        elif self.type == "SD" or self.type == "SH":
            retval = "bug.png"
        elif self.type == "HO":
            retval = "cake.png"
        elif self.type == "DA":
            retval = "pill.png"
        elif self.type == "LA":
            retval = "status_away.png"
        elif self.type == "OO":
            retval = "door_out.png"

        return settings.MEDIA_URL + "img/icons/" + retval

    def calendar_html(self):
        """Return HTML for the month calendar view."""
        if self.type in ("HV", "SH"):
            short_description = "(1/2)"
        elif self.type in ("HO", "OV", "OM"):
            short_description = self.description
        else:
            short_description = ""

        employee = self.employee.first_name
        if self.type in ("HO", "OV", "OM"):
            employee = None

        if employee:
            employee_html = " [" + employee + "]"
        else:
            employee_html = ""

        html = short_description + employee_html
        return html

    def event_day(self):
        """Retrieves just the day of an event."""
        event_day = self.event_date.day

        return event_day

    def can_delete(self):
        """Return True if the event can be deleted."""
        if datetime.date.today() < self.event_date:
            return True
        else:
            return False

    def get_event_line_html(self):
        """Returns a line of HTML to show the event, mostly for the front page."""
        event_name = self.get_type_display()

        # Office visits don't have an employee.
        if self.type != "OV":
            employee = "%s - " % self.employee
        else:
            employee = ""

        # Add an icon to highlight Office Meetings.
        if self.type == "OM":
            icon = '<img src="%s" style="vertical-align: text-bottom" />' % self.event_icon()
        else:
            icon = ""

        return "%s <strong><em>%s</em></strong> - %s%s" % (
            icon,
            event_name,
            employee,
            self.description,
        )

    def overload(self):
        """
        Return True if the event is a vacation and there are already 3 vacation
        days (or half vacation days) scheduled on that date.
        """
        vac_types = ["VA", "HV"]
        vacations = Event.objects.filter(type__in=vac_types, event_date=self.event_date)
        if self.type in vac_types and vacations.count() >= 3:
            return True
        else:
            return False

    def five_consecutive(self, userid, event_length):
        """
        This function is called when a new event is added that crawls to the right
        and the left of a new event and counts the consecutive days in either direction
        makeing sure that more than 5 consecutive days are not requested without a manager
        """
        vac_types = ["VA", "HV"]

        # get the user we are analyzing
        user = User.objects.get(id=userid)

        # array for consecutive days
        vacay_days = []
        event_start = datetime.datetime.strptime(self.event_date, "%Y-%m-%d")
        # add the desired days to the vacay array
        for x in range(int(event_length)):
            vacay_days.append(event_start)
        # start the count from the last day of the event so that all preceding days are included
        day_counter = event_length - 1
        days_consecutive = True
        # FORWARD LOOP checks for consecutive days in front of start date
        while days_consecutive:
            # advance the counter and check the next consecutive day
            day_counter += 1
            temp_date = event_start + datetime.timedelta(days=day_counter)
            # make sure we are not checking weekends
            day_check = temp_date.isoweekday()
            if day_check == 6 or day_check == 7:
                # make sure that if we fall on a weekday we advance one so that we dont count it
                if event_length > 1:
                    day_counter += 1
                continue
            events = Event.objects.filter(
                type__in=vac_types,
                employee=user,
                event_date=temp_date.strftime("%Y-%m-%d"),
            )
            # make sure the day has an event (start false) to break out of while loop we find a consecutive event
            days_consecutive = False
            for event in events:
                # if they day has an event then add to array and set consecutive flag to true
                days_consecutive = True
                vacay_days.append(event)
        # BACKWARD LOOP checks for consecutive days in front of start date
        # reset the counters / flags
        days_consecutive = True
        day_counter = 0
        while days_consecutive:
            # advance the counter and check the previous consecutive day
            day_counter += 1
            temp_date = event_start - datetime.timedelta(days=day_counter)
            # make sure we are not checking weekends
            day_check = temp_date.isoweekday()
            if day_check == 6 or day_check == 7:
                continue
            events = Event.objects.filter(
                type__in=vac_types,
                employee=user,
                event_date=temp_date.strftime("%Y-%m-%d"),
            )
            # make sure the day has an event (start false) to break out of while loop unless we find another consecutive event
            days_consecutive = False
            for event in events:
                # if they day has an event then add to array and set consecutive flag to true
                days_consecutive = True
                vacay_days.append(event)
        # if more than 5 consecutive days then throw error
        if self.type in vac_types and len(vacay_days) > 5:
            return True
        else:
            return False

    def ten_in_month(self, userid, event_length):
        """
        This function gets called when a new event is added and counts all events by that
        user in the same month as the requested event  so make sure they arnt requesting
        more than 10 without a manager
        """
        vac_types = ["VA", "HV"]
        vacay_days_cumulative = []

        # get the user we are checking
        user = User.objects.get(id=userid)
        event_start = datetime.datetime.strptime(self.event_date, "%Y-%m-%d")
        # add the requested vacation days to the array
        for x in range(int(event_length)):
            vacay_days_cumulative.append(event_start)
        # get the event month and query for all vacations by that user in that month
        event_month = event_start.month
        event_year = event_start.year
        events = Event.objects.filter(
            type__in=vac_types,
            employee=user,
            event_date__month=event_month,
            event_date__year=event_year,
        )

        for event in events:
            vacay_days_cumulative.append(event)
        # if more than 10 vacation days then throw error
        if self.type in vac_types and len(vacay_days_cumulative) > 10:
            return True
        else:
            return False

    def __str__(self):
        """String representation."""
        return self.description

    class Meta:
        ordering = ["-date_added"]
