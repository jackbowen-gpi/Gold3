#!/usr/bin/env python
"""Process the Auto FTP upload queue and upload ready tiffs to the Fusion Flexo FTP site."""

import sys

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
# Back to the ordinary imports
from traceback import format_exc
from django.conf import settings

try:
    import pysftp
    PYSFTP_AVAILABLE = True
except ImportError:
    PYSFTP_AVAILABLE = False
    print("Warning: pysftp not available - Auto FTP will run in mock mode only")

from gchub_db.apps.auto_ftp.models import AutoFTPTiff
from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.includes import fs_api


def joblog_error(job_or_item, message, kill_script=False):
    """Joblogs a job or item-related error message.

    kill_script: (int) 1 to kill with generic UNIX error code,
    2 for command line error code.
    """
    job_or_item.do_create_joblog_entry(joblog_defs.JOBLOG_TYPE_ERROR, message)
    print(message)
    if kill_script:
        sys.exit(kill_script)


def perform_mock_upload(item, upload):
    """Mock upload function for development - just logs that upload would have happened."""
    print(f"MOCK: Would upload item {item.num_in_job} ({item.bev_nomenclature()}) to FTP")
    
    # Create the joblog entry to simulate successful upload
    item.do_create_joblog_entry(
        joblog_defs.JOBLOG_TYPE_FTP,
        "Item %d has been uploaded to FTP (MOCK MODE)." % item.num_in_job,
    )


def perform_upload(item, sftp, upload):
    """Uploads the specified Item's tiff and proof files."""
    # Used to track whether the upload was completely successful.
    error_present = False

    try:
        # Set up the zip file name using beverage nomenclature.
        send_name = (
            str(item.job.id)
            + "-"
            + str(item.num_in_job)
            + "-"
            + str(item.bev_nomenclature())
            + ".zip"
        )

        # Create and upload the zip file.
        zip_contents = fs_api.get_ftp_plate_files(item.job.id, item.num_in_job)
        zip_contents.seek(0)
        sftp.putfo(zip_contents, send_name)
    except Exception:
        error_msg = "Item %d tiff failed to upload due to error:\n%s" % (
            item.num_in_job,
            format_exc(),
        )
        joblog_error(item, error_msg)
        error_present = True

    """
    If the error_present flag has been set to True, warn them that something
    has gone wrong.
    """
    if not error_present:
        item.do_create_joblog_entry(
            joblog_defs.JOBLOG_TYPE_FTP,
            "Item %d has been uploaded to FTP." % item.num_in_job,
        )
    else:
        item.do_create_joblog_entry(
            joblog_defs.JOBLOG_TYPE_WARNING,
            "Item %d has partially or completely failed to upload." % item.num_in_job,
        )


"""--------------------------------------------------------------------------
Begin main application logic
--------------------------------------------------------------------------"""

# Check if Auto FTP is enabled and pysftp is available
auto_ftp_enabled = getattr(settings, 'AUTO_FTP_ENABLED', True)

if not auto_ftp_enabled or not PYSFTP_AVAILABLE:
    if not auto_ftp_enabled:
        print("Auto FTP is disabled in settings. Processing queue in mock mode...")
    if not PYSFTP_AVAILABLE:
        print("pysftp library not available. Processing queue in mock mode...")
    
    uploads = AutoFTPTiff.objects.filter(date_processed__isnull=True)
    
    for upload in uploads:
        # Take this thing off the queue to prevent double processing.
        upload.mark_as_processed()

        # Reference to the upload's job
        job = upload.job
        prospects = upload.items.all()

        # Make sure the items have been final filed out.
        ready_items = [prospect for prospect in prospects if prospect.final_file_date]

        if not ready_items:
            print("No items are ready for proofing and FTP'ing yet.")
            continue

        print("Mock Processing Items:")
        for sent_item in ready_items:
            print("* %s (%s)" % (sent_item, sent_item.bev_nomenclature()))
            # Handle the mock upload
            perform_mock_upload(sent_item, upload)
    
    print("Mock Auto FTP processing complete.")
    sys.exit(0)

# Original FTP processing code (when AUTO_FTP_ENABLED=True)
uploads = AutoFTPTiff.objects.filter(date_processed__isnull=True)

for upload in uploads:
    sdict = upload.get_settings_dict()
    # Disable sftp hostkey.
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # Connect and login to the FTP server.
    sftp = pysftp.Connection(
        host=sdict["HOST"],
        username=sdict["USERNAME"],
        password=sdict["PASSWORD"],
        cnopts=cnopts,
    )
    # Navigate to the root directory.
    sftp.chdir(sdict["ROOT_DIR"])

    # Take this thing off the queue to prevent double processing.
    upload.mark_as_processed()

    # Reference to the upload's job
    job = upload.job
    prospects = upload.items.all()

    # Make sure the items have been final filed out.
    ready_items = [prospect for prospect in prospects if prospect.final_file_date]

    if not ready_items:
        print("No items are ready for proofing and FTP'ing yet.")
        continue

    print("Sending Items:")
    for sent_item in ready_items:
        print("* %s (%s)" % (sent_item, sent_item.bev_nomenclature()))
        # Handle the uploading here using the existing ftp connection.
        perform_upload(sent_item, sftp, upload)
    # Clean up gracefully
    sftp.close()

sys.exit()
