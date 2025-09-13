#!/usr/bin/python
"""Prepare beverage invoices by collecting billable charges and creating invoices."""

import datetime

import bin_functions
from django.utils import timezone

bin_functions.setup_paths()
import django

django.setup()
from datetime import timedelta

from django.template import loader

from gchub_db.apps.bev_billing.models import BevInvoice
from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow import app_defs as workflow_defs
from gchub_db.apps.workflow.models.general import Charge
from gchub_db.apps.workflow.models.job import Job
from gchub_db.includes import general_funcs


def create_invoice(job, charge_set, inactive, past=False):
    """Create the BevInvoice object for the set of charges."""
    # Create a new invoice linked to the job.
    new_invoice = BevInvoice(job=job)
    new_invoice.save()
    # Link each charge to be invoiced to the newly created invoice object.
    for charge in charge_set:
        charge.bev_invoice = new_invoice
        charge.save()
    # Send a notification to the job's analyst if it is billing
    # out as 45-day inactive.
    if inactive:
        mail_subject = "GOLD 45-Day Inactivity: %s" % job
        try:
            mail_send_to = []
            if job.salesperson:
                mail_send_to.append(job.salesperson.email)
            if mail_send_to:
                mail_body = loader.get_template("emails/bev_inactivity_invoicing.txt")
                mail_context = {"job": job}
                general_funcs.send_info_mail(mail_subject, mail_body.render(mail_context), mail_send_to)
        except Exception:
            # Email failed, sad. Probably a bad or nonexistent address.
            pass


# Establish dates to be used later in the script.
today = timezone.now().date()
day15time = today - timedelta(days=15)
start_date_search = today - timedelta(days=30)
start_45date = today - timedelta(days=45)
cutoff_date = datetime.date(2008, 5, 1)

# Find recent file out actions -- those jobs are likely ready for invoicing.
file_out_logs = (
    JobLog.objects.filter(
        type=joblog_defs.JOBLOG_TYPE_ITEM_FILED_OUT,
        item__job__workflow__name="Beverage",
        item__job__prepress_supplier__in=("OPT", "Optihue"),
        item__is_deleted=False,
        event_time__range=(start_date_search, today),
    )
    .exclude(job__id=99999)
    .exclude(item__job__status__in=("Cancelled"))
)


# List of all jobs with recent file outs.
job_list = []
for log in file_out_logs:
    if log.item.job not in job_list:
        job_list.append(log.item.job)

# Lists for sorting jobs marked as potential invoice candidates.
invoiceable_jobs = []
jobs_not_ready = []

# Only prepare invoices for jobs in which all items have been filed out OR
# the last item to file out took place 15 days ago, and there has been no
# activity on that item since.
for job in job_list:
    # print(job)
    items_not_filed = []
    invoiceable = True
    for item in job.item_set.all():
        # If an item has NOT been filed out and has not been deleted, then
        # don't invoice it yet.
        if not item.final_file_date() and not item.is_deleted:
            invoiceable = False
            items_not_filed.append(item)

    # Alternatively, if the last file out date was greater than 15 days ago,
    # proceed with preparing the invoice.
    if job.latest_final_file_date() < today - timedelta(days=15):
        invoiceable = True

    joblogs = []
    # for each item that has not been filed out in a job check for any revisions
    # or proof outs in the last 15 days and reset the 15 day counter
    for item in items_not_filed:
        jobLogsTemp = JobLog.objects.filter(
            item__workflow__name="Beverage",
            item=item,
            item__is_deleted=False,
            item__job__prepress_supplier__in=("OPT", "Optihue"),
            event_time__range=(day15time, today),
            type__in=(
                joblog_defs.JOBLOG_TYPE_ITEM_REVISION,
                joblog_defs.JOBLOG_TYPE_ITEM_PROOFED_OUT,
            ),
        ).exclude(
            item__job__status__in=(
                "Cancelled",
                "Hold",
            )
        )
        for log in jobLogsTemp:
            joblogs.append(log)

    # if there are any job logs then there has been activity so job
    # is not invoiceable
    if joblogs:
        invoiceable = False

    # Finally, build list of jobs that can be invoiced.
    if invoiceable:
        invoiceable_jobs.append(job)
    else:
        jobs_not_ready.append(job)

# Items which have had some sort of significant activity in the last 45 days.
# This will be used to determine which jobs are 'dead' and need to be invoiced.
items_45day_activity = (
    JobLog.objects.filter(
        item__workflow__name="Beverage",
        item__is_deleted=False,
        item__job__prepress_supplier__in=("OPT", "Optihue"),
        item__job__creation_date__range=(cutoff_date, start_45date),
        event_time__range=(start_45date, today),
        type__in=(
            joblog_defs.JOBLOG_TYPE_ITEM_FILED_OUT,
            joblog_defs.JOBLOG_TYPE_ITEM_APPROVED,
            joblog_defs.JOBLOG_TYPE_ITEM_REVISION,
            joblog_defs.JOBLOG_TYPE_ITEM_PROOFED_OUT,
            joblog_defs.JOBLOG_TYPE_ITEM_ADDED,
        ),
    )
    .exclude(
        item__job__status__in=(
            "Cancelled",
            "Hold",
        )
    )
    .values("item__job__id")
    .query
)

# Select charges with no invoice date with no activity in 45 days.
billable_inactivity_charges = (
    Charge.objects.filter(
        bev_invoice__isnull=True,
        item__is_deleted=False,
        item__workflow__name="Beverage",
        item__job__creation_date__range=(cutoff_date, start_45date),
        item__job__prepress_supplier__in=("OPT", "Optihue"),
    )
    .exclude(item__job__id__in=items_45day_activity)
    .exclude(
        item__job__status__in=(
            "Cancelled",
            "Hold",
        )
    )
)

# List 45-day inactive jobs separately for verification.
inactive_job_list = []
for charge in billable_inactivity_charges:
    # Add to list of inactive jobs.
    if charge.item.job not in inactive_job_list:
        inactive_job_list.append(charge.item.job)
    # Add to list of invoiceable jobs.
    if charge.item.job not in invoiceable_jobs:
        invoiceable_jobs.append(charge.item.job)

# Add to the list of invoiceable jobs any that are marked Closed-Bill to Customer
closed_bill_now_jobs = Job.objects.filter(
    workflow__name="Beverage",
    is_deleted=False,
    prepress_supplier__in=("OPT", "Optihue"),
    status=workflow_defs.JOB_STATUS_CLOSEDBTC,
)

for job in closed_bill_now_jobs:
    if job not in invoiceable_jobs and job.job_billable_charges_exist():
        invoiceable_jobs.append(job)

print("INVOICEABLE", len(invoiceable_jobs), invoiceable_jobs)
print("NOT READY", len(jobs_not_ready), jobs_not_ready)
print("INACTIVE", len(inactive_job_list), inactive_job_list)

# Now gather all charges attached to invoiceable jobs for processing.
billable_charges = Charge.objects.filter(item__job__in=invoiceable_jobs, bev_invoice__isnull=True, item__is_deleted=False)

# Fire off the command to create an invoice for the job and it's billable charges.
for job in invoiceable_jobs:
    # Invoice any charges for the jobs that are not already invoiced.
    job_charges = billable_charges.filter(item__job=job, bev_invoice__isnull=True)
    # Only create invoice if there are charges that have not been invoiced.
    if job_charges.count() != 0:
        print("INVOICING", job)
        if job in inactive_job_list:
            inactive = True
        else:
            inactive = False
        create_invoice(job, job_charges, inactive)
    else:
        print("!!!! NO CHARGES", job)
