import importlib
import importlib.util
import os
import traceback

pkg = importlib.import_module("gchub_db.apps.fedexsys")
print("fedexsys __path__ =", getattr(pkg, "__path__", None))
for p in getattr(pkg, "__path__", []):
    print("\nListing", p)
    try:
        print(os.listdir(p))
    except Exception:
        traceback.print_exc()

# Try to load by filepath
candidate = os.path.join(list(pkg.__path__)[0], "test_models.py")
print("\nCandidate path =", candidate, "exists=", os.path.exists(candidate))
try:
    spec = importlib.util.spec_from_file_location(
        "gchub_db.apps.fedexsys.test_models", candidate
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("\nLoaded module via spec OK: ", mod)
except Exception:
    traceback.print_exc()
