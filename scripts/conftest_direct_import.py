import importlib
import importlib.util
import os
import sys
import traceback

# Force inner package dir as canonical
inner = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gchub_db"))
if inner not in sys.path:
    sys.path.insert(0, inner)
print("sys.path[0]=", sys.path[0])
print("importlib.find_spec gchub_db =", importlib.util.find_spec("gchub_db"))
try:
    m = importlib.import_module("gchub_db.conftest")
    print("imported", m)
except Exception:
    traceback.print_exc()
