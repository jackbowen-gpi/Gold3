r"""
Module .scripts\debug_import_urls.py
"""

import os
import sys
import traceback

# Ensure repo root is on sys.path
sys.path.insert(0, os.getcwd())

print("CWD", os.getcwd())
print("PYTHONPATH[0]", sys.path[0])
import os

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

try:
    import config.urls as repo_urls

    patterns = getattr(repo_urls, "urlpatterns", None)
    if patterns is None:
        print("Imported urls but found no urlpatterns")
    else:
        print("Imported urls ok, urlpatterns len", len(patterns))
        for i, p in enumerate(patterns):
            try:
                name = getattr(p, "name", None)
            except Exception:
                name = "<err>"
            print(i, type(p), "name=", name, "repr=", p)
except Exception:
    print("EXCEPTION during import of repo-root urls:")
    traceback.print_exc()
