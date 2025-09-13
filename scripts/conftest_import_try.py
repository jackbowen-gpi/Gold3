import importlib
import traceback

try:
    print("importing gchub_db.conftest")
    importlib.import_module("gchub_db.conftest")
    print("conftest imported OK")
except Exception:
    traceback.print_exc()

try:
    print("\nimporting gchub_db.settings")
    importlib.import_module("gchub_db.settings")
    print("settings imported OK")
except Exception:
    traceback.print_exc()
