#!/usr/bin/env python
"""Looks for Item objects in need of thumbnailing."""

# Setup the Django environment
import bin_functions
from django.utils import timezone

bin_functions.setup_paths()
import django

django.setup()
from gchub_db.apps.workflow.models import Item
from gchub_db.includes import fs_api

"""
Begin main program logic
"""
# If there is no processed date, the job hasn't even started rendering.
pending_thumbnails = Item.objects.filter(is_queued_for_thumbnailing=True, job__archive_disc="")[:10]

for item in pending_thumbnails:
    print("Thumbnailing %d-%d" % (item.job.id, item.num_in_job))
    try:
        fs_api.make_thumbnail_item_finalfile(item.job.id, item.num_in_job)
        # Thumbnailing was successful. Only timestamp it when we get a
        # thumbnail generated.
        item.time_last_thumbnailed = timezone.now()
    except fs_api.NoResultsFound:
        print(" - Failed to find final file")
    except fs_api.InvalidPath:
        print(" - Invalid path")
    except OSError:
        print(" - OSError caught.")
    except Exception:
        print(" - Some other error occurred.")

    item.is_queued_for_thumbnailing = False
    item.save()
