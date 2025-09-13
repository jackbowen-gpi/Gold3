#!/usr/bin/python
import os
import sys

# Setup the Django environment
sys.path.append("../../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
# Back to the ordinary imports
from django.conf import settings

from gchub_db.apps.xml_io.jdf_reader import JDFReader

root_path = os.path.join(settings.MAIN_PATH, "apps", "xml_io", "tests", "jdfs")

jdf_list = next(os.walk(os.path.join(settings.MAIN_PATH, "apps", "xml_io", "tests", "jdfs")))[2]
jdf_list = [jdf for jdf in jdf_list if jdf not in [".DS_Store"]]

for jdf in jdf_list:
    file_path = os.path.join(root_path, jdf)
    print("JDF:", file_path)
    jr = JDFReader(file_path)
    if jr.has_aborted_tasks:
        print("-- ABORTED TASK DETECTED --")
        is_first_node = True
        for task in jr.jdf_tasks:
            if is_first_node:
                print("@ JDF FILE DESCRIPTION:", task.descriptive_name)
                print("@ END STATUS:", task.status)
                print("@ COMMENTS:", task.return_comments())
            else:
                print("\n\r   TASK:", task.descriptive_name)
                print("   Status:", task.status)
                print("   Comments:", task.return_comments())
                # print pool.comments
            is_first_node = False
        print("-- END RESULT: FAILED --")
    else:
        print("-- PASS: %s --" % jdf)
    # print jr.doc.toprettyxml()
