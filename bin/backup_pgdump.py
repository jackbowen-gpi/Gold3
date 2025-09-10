#!/usr/bin/env python
"""Backs up the Postgres database and removes outdated backups."""

import os

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import time
from subprocess import call

from django.conf import settings
from django.utils import timezone

BACKUP_DIR = os.path.join(settings.BACKUP_DIR, "pg_gold")


def dump_backup():
    """Runs pg_dump to a location based on values in settings.py. Make

    sure that pg_dump is in the path!
    """
    PG_DUMPALL_PATH = "/usr/bin/pg_dumpall"
    FILENAME = timezone.now().strftime("gchdb_%h%d_%Y-%Hh.backup")
    BACKUP_FILE = os.path.join(BACKUP_DIR, FILENAME)

    print("Backing up GCH Postgres database to: %s" % BACKUP_FILE)

    print("host: %s" % settings.DATABASES["default"]["HOST"])
    print("port: %s" % settings.DATABASES["default"]["PORT"])

    cmd_list = [
        PG_DUMPALL_PATH,
        "--host=%s" % (settings.DATABASES["default"]["HOST"]),
        "--port=%s" % (settings.DATABASES["default"]["PORT"]),
        "--username=postgres",
        "--superuser=postgres",
        "--file=%s" % (BACKUP_FILE),
    ]

    call(cmd_list)
    print("Backup cycle complete.")


def remove_old_backups():
    """Cycles out backups older than the tolerance defined in

    settings.py
    """
    # 86400 seconds in a day, see how long a life these get
    backup_life_secs = settings.BACKUP_LIFE_DAYS * 86400
    print("Remove expired backups...")

    for backup in next(os.walk(BACKUP_DIR))[2]:
        if backup == ".DS_Store":
            continue

        backup_path = os.path.join(BACKUP_DIR, backup)
        # Returns epoch time when file was last modified
        last_modified = os.path.getmtime(backup_path)
        # Calc how many seconds since it was last modified
        delta_secs = time.time() - last_modified

        # If mtime is higher than thresh, trash the file
        if delta_secs > backup_life_secs:
            print("Deleting: %s" % backup_path)
            os.remove(backup_path)
    print("Old backups removed.")


"""
Begin main program logic
"""
dump_backup()
remove_old_backups()
print("Backup script terminated successfully.")
