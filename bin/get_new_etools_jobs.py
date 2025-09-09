#!/usr/bin/env python
"""Retrieves and imports new jobs from eTools."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
# Back to the ordinary imports
from gchub_db.apps.workflow import etools

etools.DEBUG = False
etools.import_new_jobs()
