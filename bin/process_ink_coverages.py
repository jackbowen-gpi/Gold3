#!/usr/bin/env python
"""Monitor the ink coverage folder, parse ink coverage XML files, and import data into the database."""

import os
import shutil
import sys
import time

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
# Back to the ordinary imports
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils import timezone

from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.apps.workflow.models import ItemColor, Job
from gchub_db.apps.xml_io.ink_coverage_reader import (
    InkCoverageDocument,
    InkCoverageException,
)

# While True, print out some misc. information. Otherwise run silently.
DEBUG = False
# When True, send JobLog and Growl notifications about errors.
SEND_ERROR_NOTIFICATIONS = True
# When True, raise exceptions rather than send notifications.
STICKEMUP = False
# If this is true, moving files in and out of the queue, processing, and invalid
# directories happens.
MOVE_FILES = True
# When this is True, successfully processed files are deleted and not retained.
DELETE_PROCESSED_FILES = True
# settings.INK_COVERAGE_DIR = '/Users/gtaylor/gchub_db/ic_test'
PROCESSING_DIR = os.path.join(settings.INK_COVERAGE_DIR, "processing")
PROCESSED_DIR = os.path.join(settings.INK_COVERAGE_DIR, "processed")
INVALID_DIR = os.path.join(settings.INK_COVERAGE_DIR, "invalid")


def move_file_to_invalid(xmfile_fullpath, error_msg, job):
    """Moves an XML file to the invalid directory and routes the error message

    to the joblog and Growl.
    """
    if SEND_ERROR_NOTIFICATIONS and error_msg and job:
        # Note the error in the joblog for the item's job.
        job.do_create_joblog_entry(joblog_defs.JOBLOG_TYPE_ERROR, error_msg)

        # Strip all HTML tags out for Growl.
        growl_error_msg = "".join(BeautifulSoup(error_msg, "lxml").findAll(text=True))
        # Notify the artist via Growl pop-up.
        job.growl_at_artist(
            "Ink Coverage Error: %s %s" % (job.id, job.name),
            growl_error_msg,
            pref_field="growl_hear_jdf_processes",
        )
    # Print it out to the console.
    print("ERROR:", error_msg)

    if MOVE_FILES:
        xmfile = os.path.basename(xmfile_fullpath)
        # Move to the invalid directory for later review.
        dest_path = os.path.join(INVALID_DIR, xmfile)
        shutil.move(xmfile_fullpath, dest_path)


"""----------------
    Begin Logic
----------------"""
# List of ink coverage XML files in the ink coverage root directory waiting
# to be processed.
coverage_list = next(os.walk(settings.INK_COVERAGE_DIR))[2]
coverage_list = [xfile for xfile in coverage_list if xfile not in [".DS_Store"]]
if DEBUG:
    print("Coverage Files:", coverage_list)

for xmfile in coverage_list:
    """
    Move the XML file from the root ink coverage directory into the processing
    directory. This is done so that if the script is somehow executed in
    very quick succession, the ink coverage isn't parsed twice. There's stil
    a very slim chance of a double process, but the script would need to
    be double executed without any delay whatsoever.
    """
    xmfile_fullpath = os.path.join(settings.INK_COVERAGE_DIR, xmfile)

    if MOVE_FILES:
        # Move the file out of the queue directory to prevent double processing.
        dest_path = os.path.join(PROCESSING_DIR, xmfile)
        shutil.move(xmfile_fullpath, dest_path)
        xmfile_fullpath = os.path.join(PROCESSING_DIR, xmfile)

    if DEBUG:
        print("-> Reading:", xmfile_fullpath)

    """
    If we encounter an exception, that particular file needs to be dealt with,
    rather than abort the entire script run. For that reason, we enclose
    everything below in the try/catch block so that the other items may be
    processed even if one is invalid.
    """
    try:
        # Read the coverage file in.
        doc = InkCoverageDocument(xmfile_fullpath, debug=DEBUG)
        job = Job.objects.get(id=doc.get_job_number())
        try:
            item_num = doc.get_item_number()
            item = job.get_item_num(item_num)

            # Store the path to the PDF file on the Item.
            item.path_to_file = doc.get_pdf_path()
            print("@> Path to file:", item.path_to_file)
            item.save()

            """
            Here we are going to check for a specific item color (4695-C) because
            we have extra in a warehouse somewhere we are trying to use up. Also
            we can use any LAB values that match below so we are also checking all
            of the colors for being within that amount
            """
            # get the current year and if it is 2017 then...
            now = timezone.now()
            if str(now.year) == "2017" and job.workflow.name == "Foodservice":
                # surplus color is what color will be checked against for other jobs
                surplusColor = "4695-C"
                # get the itemcolors for the job and if it matches 4695-C send sana an email
                # so she can try and pair the extra ink that was ordered and use it up
                # before it goes bad
                specific_itemcolor = ItemColor.objects.filter(
                    item=item, definition__name="4695", definition__coating="C"
                )
                # If the LAB values are within a certain range as well then the ink can be used
                LAB = False
                itemcolors = ItemColor.objects.filter(item=item)
                for itemcolor in itemcolors:
                    try:
                        cdefA = itemcolor.definition.lab_a
                        cdefB = itemcolor.definition.lab_b
                        cdefL = itemcolor.definition.lab_l
                        # check if they are an int or a float and then compare
                        if (
                            isinstance(cdefL, float) or isinstance(cdefL, int)
                        ) and 15.64 < cdefL < 35.66:
                            if (
                                isinstance(cdefA, float) or isinstance(cdefA, int)
                            ) and 7.70 < cdefA < 27.72:
                                if (
                                    isinstance(cdefB, float) or isinstance(cdefB, int)
                                ) and 3.74 < cdefB < 23.76:
                                    LAB = True
                    except Exception:
                        pass
                if specific_itemcolor or LAB:
                    mail_send_to = []
                    group_members = User.objects.filter(
                        groups__name="EmailGCHubManager", is_active=True
                    )
                    for user in group_members:
                        mail_send_to.append(user.email)
                    mail_from = "Gold - Clemson Support <%s>" % settings.EMAIL_SUPPORT
                    mail_subject = "Ink Match on job %s" % job
                    mail_body = loader.get_template("emails/ink_match.txt")
                    mail_context = {
                        "size": item,
                        "item": item.num_in_job,
                        "job": job,
                        "color": surplusColor,
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

        except IndexError:
            error_msg = (
                "An ink coverage was sent for %s-%s, but no such item exists in GOLD."
                % (job.id, item_num)
            )
            move_file_to_invalid(xmfile_fullpath, error_msg, job)
            continue

        if DEBUG:
            print("@> PDF Path:", doc.get_pdf_path())
            print("@> Job #:", job.id)
            print("@> Item #:", doc.get_item_number())
            print("@> Inks:", doc.get_ink_str_list())

        if not item.printlocation:
            error_msg = (
                "An ink coverage was sent for %s-%s, but lacks a print location. Please set one and re-send the ink coverage."
                % (job.id, item_num)
            )
            move_file_to_invalid(xmfile_fullpath, error_msg, job)
            continue

        # dims_ok, error_msg = doc.compare_dimensions(item)
        # if not dims_ok:
        #    move_file_to_invalid(xmfile_fullpath, error_msg, job)
        #    continue

        doc.import_disclaimer(item)
        # Import all of the values for the item.
        doc.import_itemcolors(job, item)
    except IOError:
        # Something bad happened, move the coverage file to the invalid
        # directory for later review.
        error_msg = "Ink coverage error:", sys.exc_info()
        move_file_to_invalid(xmfile_fullpath, error_msg, job)
        continue
    except InkCoverageException as instance:
        error_msg = instance.message
        move_file_to_invalid(xmfile_fullpath, error_msg, job)
        continue
    except Exception as ex:
        print(str(ex))
        try:
            if STICKEMUP:
                raise
            error_msg = "An unexpected error has occured during ink coverage processing. Please contact support."
            print("Unexpected error:", sys.exc_info())
            move_file_to_invalid(xmfile_fullpath, error_msg, job)
        except Exception:
            if STICKEMUP:
                raise
            # Something weird has happened, oh well. Maybe a bad file name
            # or an invalid file type.
            if MOVE_FILES:
                dest_path = os.path.join(INVALID_DIR, xmfile)
                shutil.move(xmfile_fullpath, dest_path)
            print("Unexpected error:", sys.exc_info())
        continue
    else:
        # Everything was fine, get rid of the old ink coverage.
        if DELETE_PROCESSED_FILES:
            os.remove(xmfile_fullpath)
        elif MOVE_FILES:
            # We're not deleting files, send them to the processed directory.
            dest_path = os.path.join(PROCESSED_DIR, xmfile)
            shutil.move(xmfile_fullpath, dest_path)
    # Put a slight pause in here to keep JDF files for the same item
    # from overwriting each other. One second should be plenty to alter the timestamp.
    time.sleep(1)

# Doneskates.
sys.exit(0)
