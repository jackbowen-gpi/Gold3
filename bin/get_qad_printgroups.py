#!/usr/bin/env python
"""Retrieves and imports new jobs from eTools."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
# Back to the ordinary imports
from gchub_db.apps.qad_data import qad

qad.DEBUG = False
qad.import_new_records()
