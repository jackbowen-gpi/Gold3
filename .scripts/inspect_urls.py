r"""
Module .scripts\inspect_urls.py
"""

import os
import importlib
import traceback
import sys
import pathlib

# Ensure repo root is on sys.path so 'gchub_db' package can be imported
repo_root = str(pathlib.Path(__file__).resolve().parents[1])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

try:
    urls = importlib.import_module("gchub_db.urls")
    urlpatterns = getattr(urls, "urlpatterns", None)
    if urlpatterns is None:
        print("urlpatterns: NONE")
    else:
        print("urlpatterns_len", len(urlpatterns))
        for i, p in enumerate(urlpatterns[:60]):
            name = getattr(p, "name", None) if hasattr(p, "name") else None
            try:
                repr_p = repr(p)
            except Exception:
                repr_p = "<repr error>"
            print(i, type(p), repr_p[:200], "name=", name)
    print("OK")
except Exception:
    traceback.print_exc()
    print("IMPORT_ERROR")
