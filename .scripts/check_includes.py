r"""
Module .scripts\check_includes.py
"""

import os
import sys
import re
import traceback

sys.path.insert(0, os.getcwd())
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

print("PYTHONPATH[0]", sys.path[0])

import django

try:
    django.setup()
    print("django.setup done")
except Exception:
    print("django.setup failed")
    traceback.print_exc()

# Read top-level urls.py
p = os.path.join(os.getcwd(), "urls.py")
text = open(p, "r", encoding="utf-8").read()

# Find include("module.path") occurrences
# This regex captures the first quoted argument to include(...)
includes = re.findall(r"include\(\s*['\"]([^'\"]+)['\"]\s*\)", text)

print("Found includes:", len(includes))

from importlib import import_module

results = []
for mod in includes:
    try:
        print("\nTrying import", mod)
        import_module(mod)
        print("OK", mod)
        results.append((mod, True, None))
    except Exception:
        print("FAIL", mod)
        tb = traceback.format_exc()
        print(tb)
        results.append((mod, False, tb))

# Summarize failures
fails = [r for r in results if not r[1]]
print("\nSummary: {} includes failed, {} succeeded".format(len(fails), len(results) - len(fails)))
for mod, ok, tb in fails:
    print("\nFAILED MODULE:", mod)
    print(tb)
