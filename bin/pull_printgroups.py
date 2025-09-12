#!/usr/bin/python
"""Import printgroups from etools for any job that does not already have the printgroup assigned in GOLD."""

import bin_functions

bin_functions.setup_paths()
from gchub_db.apps.workflow import etools
from gchub_db.apps.workflow.models import Job

job_set = Job.objects.exclude(workflow__name__in=("Beverage", "Container")).exclude(e_tools_id="")

for job in job_set:
    if not job.printgroup:
        cursor = etools._get_etools_field(job.e_tools_id, "Printgroup")
        print(cursor[0])
