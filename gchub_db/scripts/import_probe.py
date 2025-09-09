import importlib
import sys

sys.path.insert(0, "C:/Dev/Gold")
for name in ("gchub_db.test_settings", "gchub_db.gchub_db.test_settings"):
    try:
        m = importlib.import_module(name)
        print("OK", name, "->", getattr(m, "__file__", "<builtin>"))
    except Exception as e:
        print("ERR", name, type(e).__name__, e)
