"""Error Tracking Views"""

from datetime import date

from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import render

from gchub_db.apps.error_tracking.models import Error
from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models import Item
from gchub_db.includes.gold_json import JSMessage


class ErrorForm(ModelForm):
    class Meta:
        model = Error
        fields = "__all__"


def error_tracking_home(request, year=False):
    """Home page for Error tracking system"""
    if not year:
        today = date.today()
        year = today.year

    # Get the most recent errors to display up front.
    error_list = Error.objects.filter(reported_date__year=year).order_by("-id")

    # Get all the errors for this year so we can do some stats.
    yearly_errors = Error.objects.filter(reported_date__year=year)
    errors_reported = yearly_errors.count()

    # Count errors per workflow.
    fsb_errors_reported = yearly_errors.filter(job__workflow__name="Foodservice").count()
    bev_errors_reported = yearly_errors.filter(job__workflow__name="Beverage").count()
    con_errors_reported = yearly_errors.filter(job__workflow__name="Container").count()

    # Get total number of file outs so we can check the percentage of error.
    file_outs = JobLog.objects.filter(type=joblog_defs.JOBLOG_TYPE_ITEM_FILED_OUT, event_time__year=year)

    num_file_outs = file_outs.count()
    fsb_file_outs = file_outs.filter(job__workflow__name="Foodservice").count()
    bev_file_outs = file_outs.filter(job__workflow__name="Beverage").count()
    con_file_outs = file_outs.filter(job__workflow__name="Container").count()

    if errors_reported and num_file_outs:
        error_percentage = 100 - (float(errors_reported) / num_file_outs) * 100
    else:
        error_percentage = 100
    if fsb_errors_reported and fsb_file_outs:
        fsb_error_percentage = 100 - (float(fsb_errors_reported) / fsb_file_outs) * 100
    else:
        fsb_error_percentage = 100
    if bev_errors_reported and bev_file_outs:
        bev_error_percentage = 100 - (float(bev_errors_reported) / bev_file_outs) * 100
    else:
        bev_error_percentage = 100
    if con_errors_reported and con_file_outs:
        con_error_percentage = 100 - (float(con_errors_reported) / con_file_outs) * 100
    else:
        con_error_percentage = 100

    # array of years used to display yearly reports
    start_year = 2008
    current_year = date.today().year
    years_to_display = []
    while start_year <= current_year:
        years_to_display.append(current_year)
        # make sure to put the years in backwards so you start at current
        current_year = current_year - 1

    pagevars = {
        "page_title": "Error Tracking Home",
        "error_list": error_list,
        "year": year,
        "years_to_display": years_to_display,
        "num_file_outs": num_file_outs,
        "error_percentage": error_percentage,
        "errors_reported": errors_reported,
        "fsb_errors_reported": fsb_errors_reported,
        "bev_errors_reported": bev_errors_reported,
        "con_errors_reported": con_errors_reported,
        "fsb_file_outs": fsb_file_outs,
        "bev_file_outs": bev_file_outs,
        "con_file_outs": con_file_outs,
        "fsb_error_percentage": fsb_error_percentage,
        "bev_error_percentage": bev_error_percentage,
        "con_error_percentage": con_error_percentage,
    }

    return render(request, "error_tracking/home.html", context=pagevars)


def error_tracking_add(request, item_id):
    """Add error to Error Tracking System"""
    # Get the item object that the error will be tagged to.
    item = Item.objects.get(id=item_id)

    if request.POST:
        form = ErrorForm(request.POST)
        if form.is_valid():
            form.save()
            return error_tracking_home(request)
        else:
            for error in form.errors:
                return HttpResponse(
                    JSMessage(
                        "Uh-oh, there's an invalid value for field: " + error,
                        is_error=True,
                    )
                )
    else:
        form = ErrorForm()

        pagevars = {
            "form": form,
            "item": item,
            "page_title": "Report Error",
        }

        return render(request, "error_tracking/add.html", context=pagevars)


def error_tracking_delete(request, error_id):
    """Delete the given error report."""
    error = Error.objects.get(id=error_id)
    error.delete()

    return error_tracking_home(request)
