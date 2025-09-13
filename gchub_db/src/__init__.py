import importlib
import sys
import types

try:
    _top = importlib.import_module("src")
except Exception:
    _top = types.ModuleType("gchub_db.src")

for _k, _v in vars(_top).items():
    if not _k.startswith("_"):
        globals()[_k] = _v

sys.modules["gchub_db.src"] = _top
