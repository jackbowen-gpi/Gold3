import importlib
import sys
import types

try:
    _top = importlib.import_module("depends")
except Exception:
    _top = types.ModuleType("gchub_db.depends")

for _k, _v in vars(_top).items():
    if not _k.startswith("_"):
        globals()[_k] = _v

sys.modules["gchub_db.depends"] = _top
