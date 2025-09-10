#!/usr/bin/env python
"""Reads ColorKeyJDF queue, searches for items with no processed date."""

import glob
import os
import os.path

# Setup the Django environment
import bin_functions
from django.utils import timezone

bin_functions.setup_paths()
import django

django.setup()
# Back to the ordinary imports
from django.conf import settings
from django.contrib.auth.models import User
from django.template import loader

from gchub_db.apps.queues.models import ColorKeyQueue
from gchub_db.includes import general_funcs

# While True, emit extra details.
DEBUG = False

# Get the list of pending queue entries
pending_items = ColorKeyQueue.objects.filter(date_processed__isnull=True)

# we only want to grab one item at a time each run so break after the first entry
for entry in pending_items:
    # Do the deed
    if DEBUG:
        print("Processing %s..." % (entry.item))

    jdf_queue_path = settings.JDF_ROOT
    file_name = "%s-%s-%s.jdf" % (
        entry.item.job.id,
        entry.item.num_in_job,
        timezone.now().strftime("%d_%m-%H_%M_%S"),
    )
    try:
        fileNameArr = file_name.split("-")
        checkFileName = fileNameArr[0] + "-" + fileNameArr[1] + "*"
    except Exception:
        checkFileName = file_name

    """
    glob checks filenames and allows for wildcard searches (returning an array of matches)
    so that we can see if any jobs exist for an item/job

    this will check the number of attempts to process this and send an email if there are 5 or more.
    most likely indicating that something is wrong
    """
    entry.number_of_attempts += 1
    entry.save()
    if glob.glob(os.path.join(jdf_queue_path, checkFileName)):
        if entry.number_of_attempts == 5:
            mail_subject = "Duplicate ColorKey JDF attempt for Item: %s" % entry.item
            mail_body = loader.get_template("emails/duplicate_color_keys_jdf.txt")
            mail_context = {"entry": entry}
            mail_send_to = []
            for admin in settings.ADMINS:
                mail_send_to.append(admin[1])
            group_members = User.objects.filter(
                groups__name="EmailGCHubColorManagement", is_active=True
            )
            for user in group_members:
                mail_send_to.append(user.email)
            general_funcs.send_info_mail(
                mail_subject, mail_body.render(mail_context), mail_send_to
            )
        # if there is an issue at least try and process the next one
        continue
    else:
        # if an entry is processed then break cause we want to do one at a time
        entry.process()
        break

if DEBUG:
    print("Queue watcher is finished with rounds.")
