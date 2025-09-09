#!/usr/bin/env python
"""Archives jobs that have not seen activity for extended periods of time.

Removes symlinks from Active directories and moves them to the Archive dir.
"""

import time
from datetime import timedelta

# Setup the Django environment
import bin_functions
from django.utils import timezone

bin_functions.setup_paths()
import django

django.setup()
from gchub_db.apps.workflow.models import Job

# Back to the ordinary imports
from gchub_db.includes import fs_api

# Jobs with no activity for more than this number of days will be archived.
ARCHIVAL_CUTOFF_DATE = 180
# Jobs with no activity that are complete for more than this number of days will be archived.
COMPLETE_CUTOFF_DATE = 120


def main():
    """Find jobs that should be archived and perform archiving.

    Minimal wrapper for batch invocation.
    """
    jobs = Job.objects.filter(archive_disc="").order_by("id")

    archival_cutoff_date = timezone.now() - timedelta(days=ARCHIVAL_CUTOFF_DATE)
    complete_cutoff_date = timezone.now() - timedelta(days=COMPLETE_CUTOFF_DATE)
    print("Cutoff date:", archival_cutoff_date)

    counter = 0

    for job in jobs:
        last_joblog = job.job_set.all().order_by("-event_time")
        if last_joblog:
            last_joblog_date = last_joblog[0].event_time
            if last_joblog_date < archival_cutoff_date or (
                last_joblog_date < complete_cutoff_date and job.status == "Complete"
            ):
                print("Archiving", job)
                try:
                    job.delete_folder_symlink()
                except fs_api.NoResultsFound:
                    pass
                try:
                    job.delete_carton_items_subfolders()
                except Exception:
                    pass
                print(" - Symlink deleted.")
                job.archive_disc = "1"
                job.save()
                print(" - Entry saved.")
                job.create_folder_symlink(force_archive=True)
                print(" - Symlink created.")
                job.lock_folder()
                counter += 1
                time.sleep(0.1)

    print("Archiving of %d jobs is complete." % counter)


if __name__ == "__main__":
    main()
