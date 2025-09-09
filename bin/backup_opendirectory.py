#!/usr/bin/env python
"""Backs up Open Directory stuff, generates an ldif."""

import os
from socket import gethostname
from subprocess import call

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()

from django.conf import settings

hostname = gethostname()
SETTINGS_DIR = os.path.join(settings.BACKUP_DIR, "ldap")
try:
    os.makedirs(SETTINGS_DIR)
except OSError as inst:
    # Directory already exists, but fail silently.
    if inst.errno == 17:
        pass

print("Backing up %s open directory data...")

backup_file = os.path.join(SETTINGS_DIR, "ldap.ldif")
print("Writing to %s..." % backup_file)
call(["sudo", "slapcat"], stdout=open(backup_file, "w"))
print("LDAP backup complete.")
