"""
Module .scripts\test_lazy_accounts_view.py
"""

import os
import sys

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

from importlib import import_module
from django.test import RequestFactory

# mimic lazy_view behavior
module_name = "gchub_db.apps.accounts.views"
func_name = "index"

try:
    mod = import_module(module_name)
    print("module imported, attrs:", dir(mod)[:20])
    view = getattr(mod, func_name)
    print("found attribute directly")
except Exception as e:
    print("direct getattr failed, trying file load fallback:", type(e), e)
    import importlib.util
    import os

    spec = importlib.util.find_spec(module_name)
    print("spec", spec)
    if spec and spec.origin and spec.origin.endswith("__init__.py"):
        pkg_init = spec.origin
        accounts_dir = os.path.dirname(os.path.dirname(pkg_init))
        candidate = os.path.join(accounts_dir, "views.py")
        print("candidate", candidate, "exists=", os.path.exists(candidate))
        if os.path.exists(candidate):
            spec2 = importlib.util.spec_from_file_location(module_name + "_file", candidate)
            mod2 = importlib.util.module_from_spec(spec2)
            spec2.loader.exec_module(mod2)
            print("mod2 attrs sample:", dir(mod2)[:20])
            view = getattr(mod2, func_name)
            print("found attribute in file-loaded module", view)

# call the view with a dummy request to ensure it returns
import django

try:
    # Avoid starting autoreload/development server; only call setup()
    django.setup()
except Exception:
    pass
rf = RequestFactory()
req = rf.get("/")
if "view" in globals():
    try:
        resp = view(req)
        print("view returned", type(resp), getattr(resp, "status_code", None))
    except Exception as ex:
        print("calling view raised", type(ex), ex)
else:
    print("view not found")
