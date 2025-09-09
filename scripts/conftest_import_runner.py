import importlib
import os
import sys
import traceback

print("ENV PYTHONPATH=", os.environ.get("PYTHONPATH"))
print("CWD=", os.getcwd())
print("sys.path[0:6]=", sys.path[0:6])
try:
    m = importlib.import_module("gchub_db.conftest")
    print("Imported conftest:", m)
except Exception:
    traceback.print_exc()
    # Inspect spec for nested package
    try:
        import importlib.util

        spec = importlib.util.find_spec("gchub_db.gchub_db")
        print("spec for gchub_db.gchub_db =", spec)
    except Exception:
        traceback.print_exc()
