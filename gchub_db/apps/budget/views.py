"""Job and Item search views"""

import calendar
import time
from datetime import date

from django.shortcuts import render

from gchub_db.apps.budget import billing_funcs
from gchub_db.apps.workflow.models import ChargeType


def billing_home(request):
    """Billing Home Page"""
    # Calculate current month and year.
    current_time = time.localtime()
    year_num = current_time[0]
    month_num = current_time[1]

    # Figure out what the previous month was.
    if month_num == 1:
        last_month_num = 12
        last_year = year_num - 1
    else:
        last_month_num = month_num - 1
        last_year = year_num

    # Get full billing report for current month and previous month.
    current_month_report = billing_funcs.monthly_report(month_num, year_num)
    previous_month_report = billing_funcs.monthly_report(last_month_num, last_year, activity=False, billable=False)

    # array of years used to display yearly reports
    start_year = 2008
    current_year = date.today().year
    years_to_display = []
    while start_year <= current_year:
        years_to_display.append(current_year)
        # make sure to put the years in backwards so you start at current
        current_year = current_year - 1

    pagevars = {
        "page_title": "GCHUB Billing Main",
        "month_num": month_num,
        "years_to_display": years_to_display,
        "month_num_google": month_num - 1,
        "last_month_num": last_month_num,
        "month_name": calendar.month_name[month_num],
        "year_num": year_num,
        "last_year": last_year,
        "current_month_report": current_month_report,
        "previous_month_report": previous_month_report,
    }

    return render(request, "budget/billing_home.html", context=pagevars)


def yearly_report(request, year_num):
    """Gather YTD data for current year."""
    year_num = int(year_num)
    yearly_report = {}

    # Run billing reports for months 1-12 if the given year.
    month_iter = 1
    while month_iter < 13:
        get_report = billing_funcs.monthly_report(
            month_iter,
            year_num,
            type="yearly",
            activity=False,
            billable=False,
        )
        yearly_report[month_iter] = get_report
        month_iter = month_iter + 1

    pagevars = {
        "page_title": "GCHUB Billing Yearly Report",
        "yearly_report": yearly_report,
        "year_num": year_num,
    }

    return render(request, "budget/yearly_report.html", context=pagevars)


def monthly_by_plant(request, year_num, month_num, workflow, datatype):
    """Display total amounts per plant."""
    year_num = int(year_num)
    month_num = int(month_num)

    if datatype == "Billable":
        # Return the billable charge qset for given month and workflow.
        data = billing_funcs.get_billable_data(year_num, month_num, workflow)
        charge_set = data["charges"]
        total = data["total"]

    if datatype == "Invoiced":
        # Return the billable charge qset for given month and workflow.
        data = billing_funcs.get_invoiced_data(year_num, month_num, workflow)
        charge_set = data["charges"]
        total = data["total"]

    # Sort qset by plant, return totals into a dictionary.
    plant_dict = {}
    for charge in charge_set:
        try:
            try:
                # If dictionary key already exists, just add to the total.
                plant_dict[charge.item.printlocation.plant.name]["total_charges"] += charge.amount
            except KeyError:
                # If dictionary key does not exist, create it using the charge
                # amount as the initial value.
                plant_dict[charge.item.printlocation.plant.name] = {
                    "total_charges": charge.amount,
                }
        # No plant assigned, store it here on the Unspecified key.
        except AttributeError:
            try:
                # If dictionary key already exists, just add to the total.
                plant_dict["Unspecified"]["total_charges"] += charge.amount
            except KeyError:
                # If dictionary key does not exist, create it using the charge
                # amount as the initial value.
                plant_dict["Unspecified"] = {
                    "total_charges": charge.amount,
                }

    pagevars = {
        "page_title": "GCHUB Monthly Billing - Plant View",
        "total": total,
        "month_name": calendar.month_name[month_num],
        "year": year_num,
        "workflow": workflow,
        "plant_list": plant_dict,
        "summary": datatype,
    }

    return render(request, "budget/monthly_billing_details.html", context=pagevars)


def line_item_monthly(request, year_num, month_num, workflow, datatype):
    """Line item charges for given search."""
    year_num = int(year_num)
    month_num = int(month_num)

    if datatype == "Billable":
        # Return the billable charge qset for given month and workflow.
        data = billing_funcs.get_billable_data(year_num, month_num, workflow)
        charge_set = data["charges"]
        total = data["total"]

    pagevars = {
        "page_title": "GCHUB Monthly Billing - Line Item View",
        "total": total,
        "charge_set": charge_set,
        "month_name": calendar.month_name[month_num],
        "year": year_num,
        "workflow": workflow,
        "summary": datatype,
    }

    return render(request, "budget/monthly_line_items.html", context=pagevars)


def display_pricing_tables(request, workflow):
    """Display pricing tables for a given workflow -- price at # of colors, etc..."""
    charge_set = ChargeType.objects.filter(workflow__name=workflow, active=True).order_by("-category__id")
    charge_data = {}
    for type in charge_set:
        rush_charges = {}
        if type.rush_type == "NONE":
            rush_range = 1
        elif type.rush_type == "FSBMULTL":
            rush_range = 3
        else:
            rush_range = 9
        for rush_days in range(0, rush_range):
            bycolor_charges = {}
            if type.adjust_for_colors:
                ink_range = 9
            else:
                ink_range = 2
            for ink in range(1, ink_range):
                bycolor_charges[ink] = type.actual_charge(num_colors=ink, rush_days=rush_days)
            rush_charges[rush_days] = bycolor_charges
        charge_data[type] = rush_charges
    print(charge_data)
    pagevars = {
        "page_title": "GCHUB Billing - Pricing Tables",
        "charge_data": charge_data,
        "workflow": workflow,
        "ink_numbers": (1, 2, 3, 4, 5, 6, 7, 8),
    }

    return render(request, "budget/display_pricing_tables.html", context=pagevars)
