import importlib
import sys
import types

try:
    _top = importlib.import_module("api")
except Exception:
    # fall back to an empty module so imports won't fail during discovery
    _top = types.ModuleType("gchub_db.api")

# re-export public symbols
for _k, _v in vars(_top).items():
    if not _k.startswith("_"):
        globals()[_k] = _v

# ensure the module is available under the gchub_db.api name
sys.modules["gchub_db.api"] = _top
