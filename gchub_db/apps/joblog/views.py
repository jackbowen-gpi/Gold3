"""JobLog Views"""

from django import forms
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from gchub_db.apps.joblog.app_defs import (
    JOBLOG_TYPE_CRITICAL,
    JOBLOG_TYPE_ERROR,
    JOBLOG_TYPE_ITEM_APPROVED,
    JOBLOG_TYPE_ITEM_FILED_OUT,
    JOBLOG_TYPE_ITEM_FORECAST,
    JOBLOG_TYPE_ITEM_PREFLIGHT,
    JOBLOG_TYPE_ITEM_PROOFED_OUT,
    JOBLOG_TYPE_ITEM_REJECTED,
    JOBLOG_TYPE_ITEM_REVISION,
    JOBLOG_TYPE_ITEM_SAVED,
    JOBLOG_TYPE_JDF,
    JOBLOG_TYPE_JDF_ERROR,
    JOBLOG_TYPE_JOBLOG_DELETED,
    JOBLOG_TYPE_NOTE,
    JOBLOG_TYPE_PRODUCTION_EDITED,
    JOBLOG_TYPE_WARNING,
)
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models import Job, PlateOrder, PlateOrderItem
from gchub_db.includes import general_funcs
from gchub_db.includes.gold_json import JSMessage


@csrf_exempt
def joblog_standard(request, job_id):
    """Render the main joblog display."""
    job = Job.objects.get(id=job_id)
    pagevars = {
        "job": job,
    }

    return render(
        request,
        "workflow/job/job_detail/upper_right/joblog_main.html",
        context=pagevars,
    )


def joblog_filtered(request, job_id, filter_type="default"):
    """Display joblog showing only timeline-related entries."""
    job = Job.objects.get(id=job_id)

    if filter_type == "jdf":
        joblog_recent = JobLog.objects.filter(Q(type=JOBLOG_TYPE_JDF) | Q(type=JOBLOG_TYPE_JDF_ERROR))
    elif filter_type == "comments":
        joblog_recent = JobLog.objects.filter(type=JOBLOG_TYPE_NOTE)
    elif filter_type == "production":
        joblog_recent = JobLog.objects.filter(Q(type=JOBLOG_TYPE_PRODUCTION_EDITED) | Q(type=JOBLOG_TYPE_ITEM_REJECTED))
    elif filter_type == "timeline":
        joblog_recent = JobLog.objects.filter(
            Q(type=JOBLOG_TYPE_ITEM_REVISION)
            | Q(type=JOBLOG_TYPE_ITEM_SAVED)
            | Q(type=JOBLOG_TYPE_ITEM_APPROVED)
            | Q(type=JOBLOG_TYPE_ITEM_FORECAST)
            | Q(type=JOBLOG_TYPE_ITEM_FILED_OUT)
            | Q(type=JOBLOG_TYPE_ITEM_PREFLIGHT)
            | Q(type=JOBLOG_TYPE_ITEM_PROOFED_OUT)
        )
    else:
        joblog_recent = JobLog.objects.filter(
            Q(type=JOBLOG_TYPE_NOTE)
            | Q(type=JOBLOG_TYPE_ITEM_REVISION)
            | Q(type=JOBLOG_TYPE_CRITICAL)
            | Q(type=JOBLOG_TYPE_ERROR)
            | Q(type=JOBLOG_TYPE_ITEM_REJECTED)
            | Q(type=JOBLOG_TYPE_WARNING)
        )

    joblog_recent = joblog_recent.order_by("-event_time").filter(job=job_id)
    pagevars = {
        "job": job,
        "joblog_recent": joblog_recent,
        "filter_type": filter_type,
    }

    return render(
        request,
        "workflow/job/job_detail/upper_right/joblog_block.html",
        context=pagevars,
    )


def joblog_fullview(request, job_id):
    """Show the Joblog in its entirety."""
    job = Job.objects.get(id=job_id)
    joblog_list = JobLog.objects.order_by("-event_time").filter(job=job_id)

    pagevars = {
        "job": job,
        "joblog_list": joblog_list,
        "page_title": "Job Log: %s" % (job),
    }

    return render(request, "joblog/joblog_full.html", context=pagevars)


class AddNoteForm(ModelForm):
    """Form for adding a note. Now setup as ModelForm to allow instance editing."""

    class Meta:
        model = JobLog
        fields = ("log_text",)

    log_text = forms.CharField(widget=forms.Textarea)


def joblog_add_note(request, job_id):
    """Add a note to the job log."""
    job = Job.objects.get(id=job_id)

    if request.POST and request.user and request.user.is_authenticated:
        noteform = AddNoteForm(request.POST)
        if noteform.is_valid():
            note = JobLog()
            note.job = job
            note.user = request.user
            note.type = JOBLOG_TYPE_NOTE
            note.log_text = noteform.cleaned_data["log_text"]
            note.save()
            return HttpResponseRedirect(reverse("joblog_filtered_default", args=[job_id]))
        else:
            for error in noteform.errors:
                return HttpResponse(JSMessage("Invalid value for field: " + error, is_error=True))
    else:
        noteform = AddNoteForm()

        pagevars = {
            "form": noteform,
        }
        return render(
            request,
            "workflow/job/job_detail/upper_right/note_new.html",
            context=pagevars,
        )


def joblog_edit_note(request, log_id):
    """Edit a note in the job log."""
    log = JobLog.objects.get(id=log_id)
    job = Job.objects.get(id=log.job.id)

    if request.POST and request.user and request.user.is_authenticated:
        noteform = AddNoteForm(request.POST, instance=log)
        if noteform.is_valid():
            note = noteform
            note.log_text = noteform.cleaned_data["log_text"]
            note.save()
            return HttpResponseRedirect(reverse("joblog_filtered_default", args=[job.id]))
        else:
            for error in noteform.errors:
                return HttpResponse(JSMessage("Invalid value for field: " + error, is_error=True))
    else:
        noteform = AddNoteForm(instance=log)

        pagevars = {
            "form": noteform,
            "edit": True,
        }

        return render(
            request,
            "workflow/job/job_detail/upper_right/note_new.html",
            context=pagevars,
        )


def joblog_delete_note(request, log_id):
    """Allows a user to delete only their comments."""
    log = JobLog.objects.get(id=log_id)

    # Getting the assigned job id for this comment so that when the page refreshes it will show
    # all of the previous job log information.
    job = Job.objects.get(id=log.job.id)
    log.delete()
    return HttpResponseRedirect(reverse("joblog_filtered_default", args=[job.id]))


def joblog_delete_log(request, log_id):
    """Removes an event from the JobLog, creates an additional event about the deletion."""
    log = JobLog.objects.get(id=log_id)

    # check to see if we are deleting a plate order from a job that has been filed out
    # by checking the log type (15 is a filed out job)
    if int(log.type) == 15:
        # get the plate order for this job
        try:
            plate_order = PlateOrder.objects.filter(item=log.item)[0]
        except Exception:
            plate_order = None

        # check to make sure that we got a plate order for that item
        if plate_order:
            # if plate order has not been completed then get the plate order items and delete them and the plate order
            if not plate_order.stage2_complete_date:
                plate_order_items = PlateOrderItem.objects.filter(order=plate_order)
                # delete each plate order item
                for item in plate_order_items:
                    item.delete()
                # delete the plate order
                plate_order.delete()

                # finally get the template for notifications that new plates were ordered and the old ones deleted
                mail_body = loader.get_template("emails/deleted_plate_order_resubmit.txt")
            else:
                # if the new plates have already been created then get the template for the notification that a new order will be created
                mail_body = loader.get_template("emails/completed_plate_order_resubmit.txt")

            # find the right email group and send notification mail to them
            mail_subject = "GOLD Plate Reorder Confirmation: %s" % log.item.bev_nomenclature()
            econtext = {"job_number": log.job, "plate_order_item": log.item}

            mail_send_to = []
            if log.item.platepackage:
                for contact in log.item.platepackage.platemaker.contacts.all():
                    mail_send_to.append(contact.email)

            if len(mail_send_to) > 0:
                general_funcs.send_info_mail(mail_subject, mail_body.render(econtext), mail_send_to)

        # If a file out is deleted then we need to delete the forecast (log type 25) for the item and email a bunch of people,
        try:
            # I broke these statements up to make sure that the order of operations is 1 - get the forecast, 2 - save
            # log of what we are doing, 3 - change the old forecast so they happen in that order.

            # Get the forecase for the current item.
            forecast = JobLog.objects.get(item=log.item, job=log.job, type=JOBLOG_TYPE_ITEM_FORECAST)

            # If the code gets here then we have the forecast for the current item then create a new joblog
            # mentioning that we have gotten the old forcast and removed it because the item was un-final-filed.
            delete_forecast = JobLog()
            delete_forecast.job = log.job
            delete_forecast.item = log.item
            delete_forecast.type = JOBLOG_TYPE_NOTE
            delete_forecast.user = request.user
            delete_forecast.log_text = "Removed Forecast for item: " + str(log.item.num_in_job) + " - " + str(log.item)
            delete_forecast.save()

            # If the code gets here then we have successfully made a note that we are deleting the old forcast. We
            # are actually just changing it to JOBLOG_TYPE_NOTE so that it can be forecasted again but still have a record
            # of the old joblog. Save the old forecast with the new type and move on.
            forecast.type = JOBLOG_TYPE_NOTE
            forecast.save()

        except Exception as ex:
            print("Error: %s." % (str(ex)))

        # Send a notification email for FSB items.
        if log.item.job.workflow.name == "Foodservice":
            mail_body = loader.get_template("emails/delete_file_out.txt")
            # find the right email group and send notification mail to them
            mail_subject = "Action Required: Item Approval/Final File Canceled"
            econtext = {
                "item": log.item,
                "itemnum": log.item.num_in_job,
                "job": log.job,
            }

            mail_send_to = []
            # add Donna
            group_members = User.objects.filter(groups__name="EmailGCHubNewItems", is_active=True)
            for user in group_members:
                mail_send_to.append(user.email)

            # add the csr/salesperson
            if log.job.salesperson:
                mail_send_to.append(log.job.salesperson.email)
            if log.job.csr:
                mail_send_to.append(log.job.csr.email)
            # add plant people
            if log.item.printlocation == "Kenton":
                group_members = User.objects.filter(groups__name="EmailKenton", is_active=True)
                for user in group_members:
                    mail_send_to.append(user.email)
            if log.item.printlocation == "Visalia":
                group_members = User.objects.filter(groups__name="EmailVisalia", is_active=True)
                for user in group_members:
                    mail_send_to.append(user.email)
            if log.item.printlocation == "Shelbyville":
                group_members = User.objects.filter(groups__name="EmailShelbyville", is_active=True)
                for user in group_members:
                    mail_send_to.append(user.email)
            if log.item.printlocation == "Clarksville":
                group_members = User.objects.filter(groups__name="EmailClarksville", is_active=True)
                for user in group_members:
                    mail_send_to.append(user.email)
            if log.item.printlocation == "Pittston":
                group_members = User.objects.filter(groups__name="EmailPittston", is_active=True)
                for user in group_members:
                    mail_send_to.append(user.email)
            # add demand planners
            group = Group.objects.get(name="FSB Demand Planning")
            for user in group.user_set.all():
                mail_send_to.append(user.email)

            if log.item.platepackage:
                for contact in log.item.platepackage.platemaker.contacts.all():
                    mail_send_to.append(contact.email)

            if len(mail_send_to) > 0:
                general_funcs.send_info_mail(mail_subject, mail_body.render(econtext), mail_send_to)

    # Create new log about the deletion of the given log.
    delete_log = JobLog()
    delete_log.job = log.job
    delete_log.item = log.item
    delete_log.type = JOBLOG_TYPE_JOBLOG_DELETED
    delete_log.user = request.user
    delete_log.log_text = "Job log entry deleted: " + log.log_text + ". " + str(log.event_time) + " - " + str(log.user) + "."
    delete_log.save()
    # Delete the job log.
    log.delete()

    try:
        delete_log.item.update_item_status()
    except Exception:
        pass

    return HttpResponse(JSMessage("Log Deleted."))
