import importlib.util
import os
import sys

print("CWD:", os.getcwd())
print("sys.path[0:6]=", sys.path[0:6])
print("PYTHONPATH=", os.environ.get("PYTHONPATH"))

spec = importlib.util.find_spec("gchub_db")
print("gchub_db spec:", spec)
if spec:
    print("gchub_db origin:", spec.origin)

p = r"C:\Dev\Gold\gchub_db\gchub_db\apps\fedexsys\test_models.py"
print("exists target file:", os.path.exists(p), p)
print("listing dir:", os.listdir(os.path.dirname(p)))
