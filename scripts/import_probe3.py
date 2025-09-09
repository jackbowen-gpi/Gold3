import importlib
import importlib.util
import sys

print("original sys.path[0:4]=", sys.path[0:4])
inner = r"C:\Dev\Gold\gchub_db\gchub_db"
print("inserting inner package dir:", inner)
sys.path.insert(0, inner)
print("new sys.path[0:4]=", sys.path[0:4])
try:
    m = importlib.import_module("gchub_db.apps.fedexsys.test_models")
    print("imported module:", m)
except Exception:
    import traceback

    traceback.print_exc()
