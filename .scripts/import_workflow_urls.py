r"""
Module .scripts\import_workflow_urls.py
"""

import os
import sys
import traceback

sys.path.insert(0, os.getcwd())
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

print("starting django.setup")
import django

try:
    django.setup()
    print("django.setup done")
except Exception:
    print("django.setup failed")
    traceback.print_exc()

try:
    import gchub_db.apps.workflow.urls as wf_urls

    print(
        "imported workflow.urls, urlpatterns len",
        len(getattr(wf_urls, "urlpatterns", [])),
    )
except Exception:
    print("EXCEPTION importing workflow.urls:")
    traceback.print_exc()
