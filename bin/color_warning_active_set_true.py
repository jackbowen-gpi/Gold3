#!/usr/bin/env python
"""Activate color warning records that are inactive and not dismissed."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
from gchub_db.apps.workflow.models import ColorWarning

print("Getting all color_warnings")

# possibly get the ones that are false with a filter
color_warnings = ColorWarning.objects.filter(active=False, dismissed=False)

print("analyzing " + str(len(color_warnings)) + " color_warnings")

for color_warning in color_warnings:
    color_warning.active = True
    print("setting active to True for colorWarning: " + str(color_warning.id))
    color_warning.save()

print("finished")
