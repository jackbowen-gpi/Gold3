#!/usr/bin/env python
"""Check processed JDFs for success or failure and create joblog entries on failure."""

import os
import shutil
import sys

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
# Back to the ordinary imports
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.template import loader
from django.utils import timezone

from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models import Job
from gchub_db.apps.xml_io.jdf_reader import JDFReader
from gchub_db.includes import general_funcs

# While True, print out some misc. information. Otherwise run silently.
DEBUG = False
# While True, move files to processed and error when appropriate.
MOVE_FILES = True
# If this is True, send errors to the artist and make joblog entries when bad stuff happens.
SEND_ERROR_NOTIFICATIONS = True
# This is Backstage's processed directory where it tosses JDFs once it's done
# parsing them and adding the AuditPool tags to the tasks for us to read.
PROCESSED_DIR = os.path.join(settings.JDF_ROOT, "processed")
# We'll move any of the processed JDFs that have errors in them to this
# directory for later review.
ERROR_DIR = os.path.join(settings.JDF_ROOT, "errors")

if DEBUG:
    print("-> Scanning", PROCESSED_DIR)


def ColorKeyErrorMonitor(item):
    """Notify on recent Color Key related errors for the provided item."""
    an_hour_ago = timezone.now() - timedelta(hours=1)
    recent_errors = JobLog.objects.filter(job=item.job_id, log_text__icontains="Keys", event_time__gte=an_hour_ago)
    if recent_errors:
        mail_subject = "Shelbyville Color Keys Failure: %s" % item.job
        mail_send_to = []
        group_members = User.objects.filter(groups__name="EmailGCHubColorManagement", is_active=True)
        for user in group_members:
            mail_send_to.append(user.email)
        mail_body = loader.get_template("emails/ckfail.txt")
        mail_context = {"item": item}
        general_funcs.send_info_mail(mail_subject, mail_body.render(mail_context), mail_send_to)


# List of JDF files in the Processed directory waiting for review.
jdf_list = next(os.walk(PROCESSED_DIR))[2]
jdf_list = [jdf for jdf in jdf_list if jdf not in [".DS_Store"]]


def move_to_error_folder(filepath, error_msg, item):
    """Move an XML file to the error directory and route the error message to joblog and Growl."""
    if SEND_ERROR_NOTIFICATIONS and error_msg and job:
        # Note the error in the joblog for the item's job.
        item.job.do_create_joblog_entry(joblog_defs.JOBLOG_TYPE_JDF_ERROR, error_msg)

        # Notify the artist via Growl pop-up.
        item.job.growl_at_artist(
            "JDF Error: JDF error on %s-%s %s" % (item.job.id, item.num_in_job, item.job.name),
            error_msg,
            pref_field="growl_hear_jdf_processes",
        )
    # Print it out to the console.
    print("ERROR:", error_msg)

    if MOVE_FILES:
        filename = os.path.basename(filepath)
        dest_path = os.path.join(ERROR_DIR, filename)
        shutil.move(filepath, dest_path)


class TaskAborted(Exception):
    """This is thrown when a Backstage error is encountered."""

    pass


# Look through the waiting list of files and determine if they launched
# and executed successfully.
for xmfile in jdf_list:
    xmfile_fullpath = os.path.join(PROCESSED_DIR, xmfile)

    if DEBUG:
        print("#> Reading:", xmfile_fullpath)

    """
    If we encounter an exception, that particular file needs to be dealt with,
    rather than abort the entire script run. For that reason, we enclose
    everything below in the try/catch block so that the other items may be
    processed even if one is invalid.
    """
    try:
        # Parse the file, return a minidom document.
        jdf = JDFReader(xmfile_fullpath)
        # print jdoc.toprettyxml()

        job_num = jdf.job_num
        item_in_job = jdf.item_num_in_job
        print("--> Job %s item %s" % (job_num, item_in_job))

        job = Job.objects.get(id=job_num)
        item = job.get_item_num(item_in_job)

        if jdf.has_aborted_tasks:
            # One or more sub-task in the JDF has been aborted.
            print("!> ABORTED TASK DETECTED")
            is_first_node = True
            for task in jdf.jdf_tasks:
                if is_first_node:
                    task_debug_output = task.return_comments()
                    print("@ JDF FILE DESCRIPTION:", task.descriptive_name)
                    print("@ END STATUS:", task.status)
                    print("@ COMMENTS:", task_debug_output)
                    # Create a JobLog entry to let the user know something bad happened.
                    log_text = "JDF task resulted in an error:<br />%s" % (task_debug_output)
                    move_to_error_folder(xmfile_fullpath, log_text, item)
                    # Send email if related to Color Keys
                    ColorKeyErrorMonitor(item)
                else:
                    print("\n\r   TASK:", task.descriptive_name)
                    print("   Status:", task.status)
                    print("   Comments:", task.return_comments())
                is_first_node = False
            print("!> END RESULT: TASK FAILED")

            # END IF JDF HAS ABORTED TASKS
            raise TaskAborted()
    except Exception:
        # Something really bad happened, move the JDF to the error
        # directory for later review.
        print("Unexpected JDF read error for %s: %s" % (xmfile, sys.exc_info()))
        move_to_error_folder(xmfile_fullpath, sys.exc_info(), item)
    else:
        print("--> JDF was processed successfully.")
        if job.workflow.name == "Beverage":
            print("--> Beverage job found, triggering Tiff_to_PDF proof generation.")
            # Check ticket name. Certain tickets shouldn't trigger tiff2pdf.
            try:
                jdf = JDFReader(xmfile_fullpath)
                ae_params = jdf.doc.getElementsByTagName("eg:BackStageTaskParams")[0]
                ticket_name = ae_params.getAttribute("eg:TicketName")
            except Exception:
                ticket_name = "Unknown"
            # If the ticket isn't a "Workflow" task type attempt tiff to pdf.
            if ticket_name.startswith("/swft/Beverage Smart Step and RIP"):
                print("--> Tiff_to_PDF generation started.")
                try:
                    item.do_tiff_to_pdf()
                except IOError:
                    # Usually means it can't find the die tiff.
                    log_text = "Die tiff missing for %s-%s" % (
                        item.job.id,
                        item.num_in_job,
                    )
                    move_to_error_folder(xmfile_fullpath, log_text, item)
                    continue
            else:
                print("--> Tiff_to_PDF proof generation skipped due to ticket name.")

        # All's well, get rid of the file.
        if MOVE_FILES:
            os.remove(xmfile_fullpath)
