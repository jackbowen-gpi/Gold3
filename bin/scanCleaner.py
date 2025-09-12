#!/usr/bin/env python
"""Clean the Scans folder by deleting files older than one month."""

import datetime
import os

# Setup the Django environment
import bin_functions

from gchub_db.includes import general_funcs

bin_functions.setup_paths()
from django.conf import settings

print("Starting")

# Directory to use
basePath = os.path.join(settings.DROPFOLDERS_DIR, "Scans")
today = general_funcs._utcnow_naive()

mounted = os.path.exists(basePath)
if mounted:
    # list and iterate through all of the files
    for file in os.listdir(basePath):
        filePath = os.path.join(basePath, file)
        if os.path.isfile(filePath):
            # make sure that none of the files are hidden files
            if file[0] != ".":
                dateModified = datetime.datetime.utcfromtimestamp(os.path.getmtime(filePath))

                # comepare today to the dateMod and get the lifetime
                lifetime = today - dateModified
                if lifetime.days > 30:
                    # remove any files that are older than 30 days
                    os.remove(filePath)

            else:
                print("Hidden file, Do not delete: " + str(file))
        else:
            print("Folder, Do not delete: " + str(file))
else:
    print("Folder is not mounted!")


print("Done")
