#!/usr/bin/env python
"""Quick test harness for the make_template command during development."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from gchub_db.apps.workflow.models import Job

j = Job.objects.get(id=55817)
i = j.get_item_num(1)
# print "/home/gtaylor/dev/gchub_db/bin/make_template "
# "'/Volumes/Production/templates/beverage/halfgallon-fitment.pdf' "
# "'/Volumes/JobStorage/53363/Final Files/53363-1 70F-710-213-53363/53363-1 Template.pdf' "
# "'H' '' '70910 00040' 'crosshairs' '5' '3124' '' '286' '' '123' '' '185' '' 'Black'"
i.do_bev_make_die(test_mode=True, debug=True, old_marks=False)
