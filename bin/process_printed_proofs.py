#!/usr/bin/env python
"""See what's been proofed by AE/FlexRIP."""

import os
import time

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
from datetime import datetime, timedelta
from xml.dom import minidom

from django.conf import settings
from django.utils import timezone

from gchub_db.apps.workflow.models import Item, ProofTracker

"""
Variables
"""
# Turns on print statements for troubleshooting.
show_your_work = False
# Path to the hot folder.
xml_file_path = settings.PRINTED_PROOFS_DIR
# Used to check for old XML files
month_ago = timezone.now() - timedelta(31)


"""
Begin main program logic
"""
for file in next(os.walk(xml_file_path))[2]:
    if file.startswith("JOB_") and file.endswith(".xml"):
        if show_your_work:
            print("Working on %s..." % file)

        # Check the files modification date. The dates stored within the XML
        # are too inconsistent.
        try:
            print_date_string = time.ctime(os.path.getmtime(os.path.join(xml_file_path, file)))
            print_date = datetime.strptime(print_date_string, "%a %b %d %H:%M:%S %Y")
            # Skip XML older than a month.
            if month_ago > print_date:
                continue
        except Exception:
            if show_your_work:
                print("   Print date not found. Skipping.")
            continue

        # Now read the XML.
        try:
            xml = minidom.parse(os.path.join(xml_file_path, file))
        except Exception:
            if show_your_work:
                print("   XML read failed. Skipping.")
            continue

        # Check if the print job was cancelled and bail out if it was.
        cancelled_status = xml.getElementsByTagName("Cancelled")
        if cancelled_status:
            if show_your_work:
                print("   Cancelled. Skipping.")
            continue

        # Get the copy count.
        try:
            copycount = xml.getElementsByTagName("CopyCount")[0].firstChild.data
        except Exception:
            if show_your_work:
                print("   Copy count not found. Skipping.")
            continue

        # Get the job and item numbers. They're in one of the Title tags.
        try:
            titles = xml.getElementsByTagName("Title")

            # Read through and look for the title tag where type="String"
            for title in titles:
                if title.getAttribute("type") == "string":
                    # This should be the file name.
                    jobitemnum = title.firstChild.data.split()[0]
                    # Separate the item number from the job number.
                    jobnum = jobitemnum.split("-")[0]
                    num_in_job = jobitemnum.split("-")[1]
        except Exception:
            if show_your_work:
                print("   Job number not found. Skipping.")
            continue

        # Get the proofer used
        workflows = xml.getElementsByTagName("Workflow")
        proofer = None

        for workflow in workflows:
            try:
                proofer = workflow.getElementsByTagName("Description")[0].firstChild.data
            except Exception:
                pass

        # Print all the data we've gathered.
        if show_your_work:
            print("   %s-%s = %s copie(s) (%s) %s" % (jobnum, num_in_job, copycount, print_date, proofer))

        # Look up the item in GOLD.
        try:
            item = Item.objects.get(job__id=jobnum, num_in_job=num_in_job)
        except Exception:
            if show_your_work:
                print("   Item not found in GOLD. Skipping.")
            continue

        """
        In this next section we see if a tracker already exists by looking for
        one with the same item and xml_filename. xml_filenames do get re-used
        but the chances of a name getting re-used and then applied to the same
        item at a later date are very low.
        """

        # See if there's already a record for this proof. Create one if not.
        try:
            proof_tracker = ProofTracker.objects.get(item=item, xml_filename=file)
        except Exception:
            proof_tracker = False
        if not proof_tracker:
            tracker = ProofTracker(
                item=item,
                creation_date=print_date,
                copies=copycount,
                xml_filename=file,
                proofer=proofer,
            )
            tracker.save()
            if show_your_work:
                print("   ...tracker created.")
