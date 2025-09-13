"""
Detailed import diagnostic for specific modules that failed earlier.
Prints full tracebacks to stdout so caller can tee to a file.
"""

import os
import sys
import traceback
from importlib import import_module

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PARENT = os.path.dirname(ROOT)
for p in (ROOT, PARENT):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.test_settings")

modules = [
    "gchub_db.apps.admin_log.urls",
    "gchub_db.apps.art_req.urls",
    "gchub_db.apps.auto_ftp.urls",
    "gchub_db.apps.catscanner.models",
    "gchub_db.apps.legacy_support.urls",
    "gchub_db.apps.legacy_support.models",
    "gchub_db.apps.manager_tools.models",
    "gchub_db.apps.queues.urls",
    "gchub_db.apps.software.urls",
    "gchub_db.apps.video_player.models",
    "gchub_db.apps.workflow.urls",
]

print("PYTHON:", sys.executable)
print("ROOT:", ROOT)
print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))

try:
    import django

    print("Django version:", django.get_version())
    django.setup()
    print("django.setup() succeeded")
except Exception:
    print("django.setup() failed")
    traceback.print_exc()

for modname in modules:
    print("\n---- IMPORT", modname, "----")
    try:
        import_module(modname)
        print("OK", modname)
    except Exception:
        print("ERROR importing", modname)
        traceback.print_exc()

print("\nDone")
