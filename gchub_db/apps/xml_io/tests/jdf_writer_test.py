#!/usr/bin/python
import os
import sys

# Setup the Django environment
sys.path.append("../../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
# Back to the ordinary imports
from gchub_db.apps.workflow.models import Job
from gchub_db.apps.xml_io.jdf_writer import ItemJDF


def test_new_fsb_ffo_proof(item):
    """
    (ffo = final file out)
    Create JDF to:
    A) Tabular Step & Repeat using self.jdf_fsb_sr()
    B) Take resulting file from step A and use self.jdf_fsb_rip()
    """
    extra_vars = {
        "PLAFileList": {"Status": "Unavailable"},
        "TIFFList": {"Status": "Unavailable"},
    }

    sr_jdf = ItemJDF(item, {"SourceFileList": [item.path_to_file]}, extra_vars=extra_vars)

    sr_ticket = "/forktask/ForkTest"
    # print "SR TICKET", sr_ticket
    # <!--NODE: STEP AND REPEAT ONE-UP FILE - VARIABLE XXXSTEPTICKETXXX-->
    sr_jdf.add_task_node("Fork Test", "n0001", "1uplink", sr_ticket, "PLAFileList")
    sr_jdf.send_jdf()


i = Job.objects.get(id=56926).get_item_num(1)
test_new_fsb_ffo_proof(i)
