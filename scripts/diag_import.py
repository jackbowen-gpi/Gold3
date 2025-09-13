import importlib
import os
import sys

repo_root = os.path.abspath(os.path.dirname(__file__) + "..")
repo_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
inner_pkg_dir = os.path.join(repo_root, "gchub_db")
parent = os.path.dirname(repo_root)
for p in (inner_pkg_dir, repo_root, parent):
    if p in sys.path:
        sys.path.remove(p)
sys.path.insert(0, parent)
sys.path.insert(0, repo_root)
sys.path.insert(0, inner_pkg_dir)
print("sys.path[0:5] =", sys.path[0:5])
try:
    m = importlib.import_module("gchub_db")
    print("gchub_db module:", getattr(m, "__file__", None))
except Exception as e:
    print("import gchub_db failed:", e)
try:
    ts = importlib.import_module("gchub_db.test_settings")
    print("imported test_settings from", ts.__file__)
except Exception as e:
    print("import test_settings failed:", e)
