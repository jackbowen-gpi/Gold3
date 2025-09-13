r"""
Module .scripts\check_try_includes.py
"""

import os
import sys
import re
import traceback

sys.path.insert(0, os.getcwd())
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

import django

try:
    django.setup()
except Exception:
    traceback.print_exc()

p = os.path.join(os.getcwd(), "urls.py")
text = open(p, "r", encoding="utf-8").read()
print("urls.py head:\n", text[:400])

# find occurrences of _try_include(regex, "module.path")
mods = re.findall(r"_try_include\(\s*[^,]+,\s*['\"]([^'\"]+)['\"]\s*\)", text)
print("Found _try_include modules:", len(mods))

from importlib import import_module

for m in mods:
    print("\nModule:", m)
    try:
        import_module(m)
        print("  OK")
    except Exception:
        print("  FAIL")
        traceback.print_exc()
