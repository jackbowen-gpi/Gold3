import importlib
import sys

print("sys.path[0]=", sys.path[0])
try:
    m = importlib.import_module("gchub_db.test_settings")
    print("OK", m.__file__)
except Exception as e:
    print("ERR", type(e).__name__, e)
