#!/usr/bin/python
"""Transfer job folders between file servers and create junction points."""

import shutil

import bin_functions

bin_functions.setup_paths()
from gchub_db.apps.workflow.models import Job

"""
!!!Destination must be mounted with admin privilages first!

!!!Production dir must be mounted to create j-points via hotfolders.

Transfer job folders from the old file server to the new one. Might want to do
this in small chunks. There's not a good way to interrupt the script with a
keyboard command.
"""

hi = 71721
low = 71721

# Start with the newest first
jobs = Job.objects.filter(id__range=(low, hi)).order_by("-id")
for job in jobs:
    # Set source
    source = "/Volumes/Promise/JobStorage/%s" % job.id
    print("Source:%s" % source)

    # Set destination
    dest = "/Volumes/JobStorage/%s" % job.id
    print("Destination:%s" % dest)

    # Attempt to copy
    try:
        print("Copying %s" % job)
        shutil.copytree(source, dest)
    except Exception:
        print("ERROR! %s" % job.id)
        try:
            # Write the errors to a text file.
            file = open("transfer_errors.txt", "a")
            file.write("%s \n" % job.id)
            file.close()
        except Exception:
            pass

    # Make the junction point
    if job.archive_disc:
        print("Creating j-point in archive.")
        # If the job is archived then force archive for create_folder_symlink
        job.create_folder_symlink(True)
    else:
        print("Creating j-point.")
        job.create_folder_symlink()
