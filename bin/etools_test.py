#!/usr/bin/env python
"""Tests ETools stuff."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from gchub_db.apps.workflow import etools

etools.DEBUG = True
cursor = etools.get_job_by_request_id("104790")

for ejob in cursor:
    etools._set_etools_job_status(ejob.Request_ID, "New")

# for column in cursor.description:
#    print column
