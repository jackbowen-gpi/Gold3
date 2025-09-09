#!/usr/bin/env python
"""Utilities for working with JDF files and related processes."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from gchub_db.apps.workflow.models import Job

j = Job.objects.get(id=56210)
i = j.get_item_num(1)
jdf = i.genxml_jdf_fsb_ffo()
# jdf = i.genxml_jdf_bev_workflow()
print(jdf.get_xml_doc_string(pretty=True))
# i.do_jdf_fsb_ffo()
i.do_jdf_bev_workflow()
