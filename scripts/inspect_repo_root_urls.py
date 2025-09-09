import importlib
import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
try:
    mod = importlib.import_module("urls")
    up = getattr(mod, "urlpatterns", None)
    print(
        "imported module urls, urlpatterns type:",
        type(up),
        "len:",
        len(up) if up is not None else "None",
    )
    for i, p in enumerate(up[:20]):
        print(i, repr(p), getattr(p, "name", None), getattr(p, "pattern", None))
except Exception:
    import traceback

    traceback.print_exc()
