#!/usr/bin/env python
"""Locks job folders under JobStorage once they are marked for archival."""

import time

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from gchub_db.apps.workflow.models import Job

archived_jobs = Job.objects.exclude(archive_disc="").order_by("-id")

for job in archived_jobs:
    job.lock_folder()
    time.sleep(0.1)
