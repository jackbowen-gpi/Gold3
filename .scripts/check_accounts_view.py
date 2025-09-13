r"""
Module .scripts\check_accounts_view.py
"""

import os
import sys
import traceback

sys.path.insert(0, os.getcwd())
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))

import django

try:
    django.setup()
    print("django.setup ok")
except Exception:
    print("django.setup failed")
    traceback.print_exc()

import importlib
import importlib.util
import inspect

modname = "gchub_db.apps.accounts.views"
print("\nInspecting module spec for", modname)
spec = importlib.util.find_spec(modname)
print("spec=", spec)
if spec:
    print("origin=", getattr(spec, "origin", None))
    print("submodule_search_locations=", getattr(spec, "submodule_search_locations", None))

try:
    mod = importlib.import_module(modname)
    print("\nImported module:", mod, "type=", type(mod))
    print("has index?", hasattr(mod, "index"))
    if hasattr(mod, "index"):
        print("index obj:", getattr(mod, "index"))
        try:
            import inspect

            print("index source (first 200 chars):")
            print(inspect.getsource(mod.index)[:200])
        except Exception:
            pass
    else:
        print(
            "module dir keys sample:",
            [k for k in dir(mod) if not k.startswith("_")][:50],
        )
except Exception:
    print("import_module failed:")
    traceback.print_exc()

# Try to locate accounts/views.py file and show first 40 lines
import os

acc_views_file = os.path.join(os.getcwd(), "gchub_db", "apps", "accounts", "views.py")
print("\nChecking file path", acc_views_file)
if os.path.exists(acc_views_file):
    with open(acc_views_file, "r", encoding="utf-8") as f:
        data = f.read().splitlines()
    print("file exists, lines=", len(data))
    print("\n".join(data[:40]))
else:
    print("views.py file not found")

# Check devadmin user
try:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    username = "devadmin"
    u = User.objects.filter(username=username).first()
    if u:
        print("\nDEVADMIN FOUND: username=%s, is_superuser=%s, is_staff=%s" % (u.username, u.is_superuser, u.is_staff))
        try:
            perms = u.user_permissions.count()
            print("explicit user_permissions count:", perms)
        except Exception:
            pass
    else:
        print("\nDEVADMIN not found")
except Exception:
    print("\nFailed to query users:")
    traceback.print_exc()
