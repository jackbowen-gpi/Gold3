#!/usr/bin/env python
"""
UPDATE

It was decided that we no longer want QAD to auto-sync corrugated specs with
GOLD due to things like rounding errors in QAD. This functionality has been
disabled but left in GOLD just in case we need to dust it off again later.

~~~~~~~

This script syncs GOLD's BoxItemSpec objects to what is in the corporate
data warehouse.

NOTE: Only specs with non-null width, length, and height values are transferred.
A lot of the times, a spec has an entry in the corporate tables, but has no
spec data associated with it.
"""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports

# Disabled
# import_fsb_corrugated_specs()
