#!/usr/bin/env python
"""Backs up server-related settings on Mac Server installs."""

import os
import sys
from socket import gethostname
from subprocess import call

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
from django.conf import settings

try:
    from gchub_db.bin.conf.backup_service_list_mac import SERVICES
except ImportError:
    print("No services to back up. Should be under conf/backup_service_list_mac.py")
    sys.exit()

hostname = gethostname()
SETTINGS_DIR = os.path.join(settings.BACKUP_DIR, "settings", hostname)
try:
    os.mkdir(SETTINGS_DIR)
except OSError as inst:
    # Directory already exists, but fail silently.
    if inst.errno == 17:
        pass

print("Backing up %s server settings..." % hostname)

for service in SERVICES:
    service_file = os.path.join(SETTINGS_DIR, service)
    print(service_file)
    call(["sudo", "serveradmin", "settings", service], stdout=open(service_file, "w"))
print("Server backup complete.")
