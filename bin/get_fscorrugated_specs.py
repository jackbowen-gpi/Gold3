#!/usr/bin/env python
"""Retrieve Foodservice Corrugated specs from MSSQL via ODBC."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from gchub_db.apps.auto_corrugated import fs_odbc

fs_odbc.DEBUG = False
fs_odbc.test()
