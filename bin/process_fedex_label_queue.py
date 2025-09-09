#!/usr/bin/env python
"""Looks through the Fedex label queue and prints labels as needed."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
from gchub_db.apps.fedexsys.models import Shipment

"""
Begin main program logic
"""
# If there is no label print date, the label needs to be printed.
label_shipments = Shipment.objects.filter(date_label_printed=None)

for shipment in label_shipments:
    shipment.print_label()

    if shipment.is_international():
        # International labels get two copies.
        shipment.print_label()
        shipment.print_label()
