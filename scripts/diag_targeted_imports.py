"""
Attempt imports for a list of target modules and print full tracebacks to stdout.
"""

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

print("PYTHON:", sys.executable)
try:
    import django

    print("Django", django.get_version())
    django.setup()
    print("django.setup OK")
except Exception:
    print("django.setup failed")
    traceback.print_exc()

for mod in modules:
    print("\n---- TRY", mod, "----")
    try:
        import_module(mod)
        print("OK", mod)
    except Exception:
        print("ERROR", mod)
        traceback.print_exc()

print("\nDone")
