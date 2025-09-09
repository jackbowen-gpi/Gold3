#!/usr/bin/env python
"""This script syncs GOLD's color database with Esko's bg_cms_data share.

It keeps GOLD's color accuracy tracking via CAT Scanner up to date with the
latest Esko colorbook standards.
"""

import sys

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from gchub_db.apps.color_mgt.models import ColorDefinition
from gchub_db.includes.esko_color.colorbook_reader import EskoColorBook


def sync_colorbook(cb_name, coating):
    """Sync a colorbook into GOLD for the given coating.

    cb_name is the identifier for the Esko colorbook. coating indicates which
    coating variant to target (e.g., 'U' or 'C').
    """
    cbook = EskoColorBook("FSB_Pantone_Uncoated")
    esko_color_names = cbook.get_color_name_list()
    esko_set = set(esko_color_names)

    gold_color_names = ColorDefinition.objects.filter(coating=coating).values_list(
        "name", flat=True
    )
    gold_set = set(gold_color_names)

    # In GOLD but not Esko.
    colors_to_delete = gold_set - esko_set
    # In Esko but not GOLD.
    # print esko_set - gold_set

    gold_colors_to_delete = ColorDefinition.objects.filter(name__in=colors_to_delete)
    print("DELETE FROM GOLD")
    print(gold_colors_to_delete)
    for col in gold_colors_to_delete:
        print("%s - %d" % (col, col.itemcolor_set.count()))


sync_colorbook("FSB_Pantone_Uncoated", "U")

# Doneskates.
sys.exit(0)
