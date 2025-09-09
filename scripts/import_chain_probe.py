import importlib
import traceback

names = [
    "gchub_db",
    "gchub_db.apps",
    "gchub_db.apps.fedexsys",
    "gchub_db.apps.fedexsys.test_models",
]
for n in names:
    print("\nIMPORT ->", n)
    try:
        m = importlib.import_module(n)
        print("OK:", m, "file=", getattr(m, "__file__", None))
    except Exception:
        traceback.print_exc()
        break
