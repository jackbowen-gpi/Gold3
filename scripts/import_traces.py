"""Import modules and print exception type, message, and traceback for failures."""

import os
import sys
import traceback
from importlib import import_module

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
for p in (ROOT, os.path.dirname(ROOT)):
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
print("PYTHON", sys.executable)
try:
    import django

    print("Django", django.get_version())
    django.setup()
    print("django.setup OK")
except Exception:
    print("django.setup failed")
    traceback.print_exc()
for m in modules:
    print("\n==== IMPORT", m, "====")
    try:
        import_module(m)
        print("OK")
    except Exception as e:
        print("EXC TYPE:", type(e))
        print("EXC:", repr(e))
        print("TRACEBACK:")
        traceback.print_exc()
print("\nDONE")
