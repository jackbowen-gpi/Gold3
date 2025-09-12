#!/usr/bin/env python
"""Sends updates to ETools."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
from gchub_db.apps.workflow import etools

# Back to the ordinary imports
from gchub_db.apps.workflow.models import Job

jobs_needing_updates = Job.objects.filter(workflow__name="Foodservice", needs_etools_update=True, id__lt=99999)[:30]
for job in jobs_needing_updates:
    print("Sending updates for %s" % job)
    try:
        etools.push_job(job)
    except Exception:
        print("ERROR: %s" % job)
