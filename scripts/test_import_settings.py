import importlib
import sys

print("sys.path[0]=", sys.path[0])
try:
    m = importlib.import_module("gchub_db.test_settings")
    print("imported gchub_db.test_settings:", getattr(m, "__file__", None))
except Exception as e:
    print("import failed:", e)
