#!/usr/bin/env python
"""Quick smoke-test to convert a TIFF to PDF for a specific item."""

import bin_functions

bin_functions.setup_paths()
from gchub_db.apps.workflow.models import Job

j = Job.objects.get(id=57507)
i = j.get_item_num(1)
i.do_tiff_to_pdf()
