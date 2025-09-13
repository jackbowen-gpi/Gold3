import os
import sys
import traceback

# Ensure environment is the same as the manual runs
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

print("PYTHONPATH[0:4]=", sys.path[0:4])
print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))

try:
    import pytest

    print("pytest imported, running...")
    rc = pytest.main(["-q"])
    print("pytest finished, rc=", rc)
except Exception:
    traceback.print_exc()
    sys.exit(2)
