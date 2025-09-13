#!/usr/bin/env python
"""Send email reminders for proofs sitting for 15+ days."""

import datetime
from datetime import timedelta

# Setup the Django environment
import bin_functions
from django.utils import timezone

bin_functions.setup_paths()
import django

django.setup()
# Back to the ordinary imports
from django.template import loader

from gchub_db.apps.joblog.app_defs import (
    JOBLOG_TYPE_ITEM_APPROVED,
    JOBLOG_TYPE_ITEM_FILED_OUT,
    JOBLOG_TYPE_ITEM_PROOFED_OUT,
    JOBLOG_TYPE_JOBLOG_DELETED,
)
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models import Revision
from gchub_db.includes.general_funcs import send_info_mail

# Establish dates.
today = datetime.date.today()
# Start sending reminders for proofs before this day.
reminder_start_time = today + timedelta(days=-15)
# Don't send reminders for proofs sent more than this many days ago. We don't
# want an email going out for a job that's been idle for 2 years, for example.
reminder_end_time = reminder_start_time + timedelta(days=-15)

# Get all items proofed out within date range.
proofed_events = JobLog.objects.filter(
    type=JOBLOG_TYPE_ITEM_PROOFED_OUT,
    event_time__range=(reminder_end_time, reminder_start_time),
    item__job__workflow__name="Foodservice",
)


print("Proof out events:", proofed_events.count())

# Create empty list to store items that ultimately meet qualifications.
jobs_for_reminders = {}

for event in proofed_events:
    # If item has been approved, filed out or deleted, no reminder.
    if JobLog.objects.filter(
        item=event.item,
        type__in=(
            JOBLOG_TYPE_ITEM_APPROVED,
            JOBLOG_TYPE_ITEM_FILED_OUT,
            JOBLOG_TYPE_JOBLOG_DELETED,
        ),
    ):
        continue
    # If item has a pending revision, no reminder.
    elif Revision.objects.filter(item=event.item, complete_date__isnull=True):
        continue

    # If the loop has made it this far, and the job is still active, then
    # send out a reminder.
    elif (
        event.item.job.status == "Active"
        and reminder_end_time < event.item.current_proof_date().date() < reminder_start_time
        and event.item.proof_reminder_email_sent is None
    ):
        # Just here for convenience.
        job_num = event.item.job.id
        # If this key is not accessible below, create it and instantiate
        # an empty list to store reminder items.
        try:
            # See if the key exists for this job.
            jobs_for_reminders[job_num]
        except KeyError:
            # The key for this job doesn't exist yet, create it as an empty list.
            jobs_for_reminders[job_num] = []

        # Add the item to a list, keyed as per its job number.
        # Also make sure that the item is not not already in the list.
        if event.item not in jobs_for_reminders[job_num]:
            jobs_for_reminders[job_num].append(event.item)

# Now we'll want to send out one email per job and list which items have
# not yet been returned. Then set a bool. field in the item model that indicates
# that a reminder email has been set and not to send another one.
print("Jobs to send out reminders for:", len(jobs_for_reminders))
for job_num, items in list(jobs_for_reminders.items()):
    salesperson = items[0].job.salesperson
    job = items[0].job
    # print "%s %s %s" % (job_num, salesperson, items)

    mail_subject = "GOLD Proof Reminder: %d %s" % (job.id, job.name)
    mail_body = loader.get_template("emails/idle_proof_reminder.txt")
    econtext = {
        "items": items,
        "job": job,
        "salesperson": salesperson,
        "item_count": len(items),
    }
    mail_send_to = [salesperson.email]
    send_info_mail(mail_subject, mail_body.render(econtext), mail_send_to, fail_silently=True)

    # Set the proof_reminder_email_sent field on the item to prevent
    # future repeats of the email.
    for item in items:
        item.proof_reminder_email_sent = timezone.now()
        item.save()
