#!/usr/bin/env python
"""Backs up the WIKI Postgres database and removes outdated WIKI backups."""

import os

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
from subprocess import call

from django.utils import timezone

BACKUP_DIR = "/mnt/Backup/pg_wiki/"
WIKI_DATABASE_HOST = "172.23.8.65"
WIKI_DATABASE_PORT = "5432"


def dump_backup():
    """Runs pg_dump to a location based on values in settings.py.

    Make sure that pg_dump is in the path!
    """
    PG_DUMPALL_PATH = "/usr/bin/pg_dumpall"
    FILENAME = timezone.now().strftime("wiki_%h%d_%Y-%Hh.backup")
    BACKUP_FILE = os.path.join(BACKUP_DIR, FILENAME)

    print("Backing up WIKI Postgres database to: %s" % BACKUP_FILE)

    cmd_list = [
        PG_DUMPALL_PATH,
        "--host=%s" % (WIKI_DATABASE_HOST),
        "--port=%s" % (WIKI_DATABASE_PORT),
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
    file_arr = []

    print("Remove expired backups...")

    for backup in next(os.walk(BACKUP_DIR))[2]:
        if backup == ".DS_Store":
            continue

        backup_path = os.path.join(BACKUP_DIR, backup)
        # Returns epoch time when file was last modified
        current_modified = os.path.getmtime(backup_path)

        # make an array of all files in the backup folder from newest to oldest
        if file_arr:
            for x in range(len(file_arr)):
                temp_modified = os.path.getmtime(file_arr[x])
                if current_modified > temp_modified:
                    # file is newer, insert into list
                    file_arr.insert(x, backup_path)
                    break
                else:
                    # file is older, add it on the end
                    file_arr.append(backup_path)
        else:
            # first file in the array
            file_arr.append(backup_path)

    # Go through the array of files in the backup folder and delete all but the newest 3
    for x in range(len(file_arr)):
        if x > 2:
            print("Deleting: %s" % file_arr[x])
            os.remove(file_arr[x])

    print("Old backups removed.")


"""
Begin main program logic
"""
dump_backup()
remove_old_backups()
print("Backup script terminated successfully.")
