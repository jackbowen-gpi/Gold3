#!/usr/bin/env python
"""Retrieve and store Foodservice Corrugated specifications from the corporate MSSQL server via ODBC."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from gchub_db.apps.auto_corrugated import fs_odbc

fs_odbc.DEBUG = False
fs_odbc.test()
