import os
import sys

sys.path.insert(0, "C:/Dev/Gold")
os.environ["PYTHONPATH"] = os.environ.get("PYTHONPATH", "")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.gchub_db.test_settings"
import pytest

rc = pytest.main(["gchub_db/gchub_db/apps/legacy_support/tests/test_smoke_legacy_support.py", "-q"])
print("pytest rc=", rc)
