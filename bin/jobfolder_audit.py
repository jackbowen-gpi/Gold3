#!/usr/bin/python
"""Audit job folders on disk and report inconsistencies to GOLD."""
import os

import bin_functions

bin_functions.setup_paths()
import django

django.setup()
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from gchub_db.apps.workflow.models import *

"""
!!! Make sure wherever this script is run that the job storage directory is
mounted with admin privileges. Some older job folders appear empty otherwise.

This script checks for missing or empty job folders. A missing or empty job
folder is a sign that a user accidentally deleted something. In that case the
missing jobs will need to be restored from backup ASAP since our backups have a
limited file retention window.

We check for empty job folders because that's a sign that something was deleted
through the junction points in active and archive. The empty folder gets left
behind.
"""

empty_folders = []
missing_folders = []
errors = []

# These are empty jobs that have been checked before and deemed "okay as-is".
ignore_list = [
    63207,
    51748,
    51733,
    49743,
    49730,
    48801,
    48772,
    47799,
    46982,
    43461,
    43391,
    41395,
    40853,
    40722,
    40720,
    40717,
    40709,
    40708,
    40704,
    40703,
    40702,
    40701,
    40246,
    38749,
    38634,
    38632,
    38631,
    38589,
    38552,
    38550,
    38548,
    38544,
    38529,
    38524,
    38517,
    38502,
    38466,
    38462,
    38454,
    38446,
    38423,
    38418,
    38417,
    37668,
    37207,
    37153,
    37124,
    37066,
    36934,
    36889,
    36871,
    36454,
    35445,
    35389,
    35365,
    34609,
    34306,
    34153,
    34131,
    34031,
    34011,
    34001,
    33964,
    33917,
    33778,
    33730,
    33699,
    33615,
    33581,
    33579,
    33565,
    33561,
    33560,
    33554,
    33552,
    33550,
    33525,
    33512,
    33508,
    33492,
    33481,
    33480,
    33475,
    33471,
    33448,
    33402,
    33399,
    33341,
    33233,
    33229,
    33193,
    33192,
    33162,
    33149,
    33132,
    33109,
    33047,
    33030,
    33028,
    33017,
    32964,
    32960,
    32959,
    32945,
    32944,
    32885,
    32881,
    32866,
    32832,
    32831,
    32828,
    32825,
    32813,
    32780,
    32770,
    32761,
    32754,
    32752,
    32747,
    32735,
    32727,
    32719,
    32703,
    32677,
    32675,
    32674,
    32673,
    32665,
    32658,
    32655,
    32622,
    32605,
    32557,
    32531,
    32495,
    32488,
    32487,
    32477,
    32473,
    32463,
    32462,
    32461,
    32438,
    32410,
    32402,
    32381,
    32270,
    32040,
    32022,
    31872,
    31818,
    31701,
    31544,
    31487,
    31433,
    31432,
    31383,
    31337,
    31164,
    31112,
    30515,
    30052,
    42694,
    41533,
    41439,
    40795,
    40576,
    38355,
    38091,
    37991,
    37951,
    37949,
    37947,
    37925,
    37696,
    37438,
    37421,
    37310,
    37133,
    37125,
    36990,
    36801,
    36775,
    36494,
    36424,
    36330,
    36093,
    36073,
    35940,
    35939,
    35833,
    35831,
    35785,
    35704,
    35675,
    35669,
    35600,
    35552,
    35399,
    34766,
    33902,
    33453,
    33364,
    33121,
    33106,
    33105,
    33094,
    33083,
    33058,
    33000,
    32981,
    32896,
    32895,
    32869,
    32790,
    32490,
    32291,
    32231,
    32163,
    32149,
    32127,
    32124,
    32104,
    32081,
    32059,
    32037,
    32031,
    32025,
    32001,
    31991,
    31985,
    31891,
    31830,
    31798,
    31648,
    31633,
    31598,
    31572,
    31523,
    31013,
    30899,
    30871,
    30854,
    30838,
    30653,
    30650,
    30575,
    30492,
    30307,
    30158,
    30041,
    30035,
    842,
    756,
    742,
    693,
    659,
    652,
    644,
    643,
    552,
    489,
    442,
    391,
    358,
    309,
    288,
    201,
    172,
    129,
    119,
    5,
    826,
    605,
    590,
    543,
    530,
    164,
    73,
    57,
    55,
    41,
    32,
    19,
    15,
    6,
]

# Ignore jobs from these prepress suppliers. They never had job folders.
prepress_ignore = ["Phototype", "Schawk", "Southern Graphics"]

# Gather all the jobs.
jobs = Job.objects.all().order_by("-id").exclude(prepress_supplier__in=prepress_ignore)
# Ignore the old container jobs.
jobs = jobs.exclude(workflow__name="Container")
# Ignore anything on the ignore list.
jobs = jobs.exclude(id__in=ignore_list)

# Testing
# hi=46530
# low=46530
# jobs=Job.objects.filter(id__range=(low, hi)).order_by('-id')

# Check the job folder for each one.
for job in jobs:
    folder = job.get_folder()
    # Check if the folder exists.
    try:
        if os.path.exists(folder):
            # If the folder exists check if it's empty.
            if not os.listdir(folder):
                empty_folders.append(job.id)
                print("Empty folder for %s" % job.id)
        else:
            # If there's no folder check to see if there are even any items
            # entered for this job. If no items are entered it can be ignored.
            items = Item.objects.filter(job__id=job.id)
            if items:
                # If there are items entered then flag it.
                missing_folders.append(job.id)
                print("No folder found for %s" % job.id)
    except Exception:
        # Note if the script has trouble checking certain jobs.
        errors.append(job.id)
        print("Error reading %s" % job.id)

# Send an email if anything is missing.
if empty_folders or missing_folders or errors:
    mail_send_to = [settings.EMAIL_SUPPORT]
    mail_from = "Gold - Clemson Support <%s>" % settings.EMAIL_SUPPORT
    mail_subject = "JobFolder audit results"
    mail_body = loader.get_template("emails/jobfolder_audit_email.txt")
    mail_context = {
        "empty_folders": empty_folders,
        "missing_folders": missing_folders,
        "errors": errors,
    }
    # send the email
    msg = EmailMultiAlternatives(
        mail_subject, mail_body.render(mail_context), mail_from, mail_send_to
    )
    msg.content_subtype = "html"
    msg.send()
    print("Email sent.")

print("Job folder audit complete.")
