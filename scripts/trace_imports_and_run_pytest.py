import importlib.abc
import importlib.util
import os
import sys
import traceback


class TraceFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        print("FIND_SPEC ->", fullname)
        try:
            importlib.util.find_spec(fullname)
        except Exception as e:
            print("  find_spec EXCEPTION for", fullname, e)
        # Don't interfere: return None to let normal import machinery handle it
        return None


sys.meta_path.insert(0, TraceFinder())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

print("Starting pytest...")
try:
    import pytest

    rc = pytest.main(["-k", "not none"])
    print("pytest rc=", rc)
except Exception:
    traceback.print_exc()
    sys.exit(2)

print("Done")
