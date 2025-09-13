"""
Diagnostic: attempt to import each gchub_db.apps.<app>.urls and .models
Writes results to stdout so caller can tee to a file.
"""

import os
import sys
import traceback
from importlib import import_module

# Ensure repo root and parent are on sys.path
ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PARENT = os.path.dirname(ROOT)
for p in (ROOT, PARENT):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.test_settings")

print("PYTHON:", sys.executable)
print("ROOT:", ROOT)
print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))

# Try to setup Django
try:
    import django

    print("Django version:", django.get_version())
    django.setup()
    print("django.setup() succeeded")
except Exception:
    print("django.setup() failed:")
    traceback.print_exc()

apps_dir = os.path.join(ROOT, "gchub_db", "apps")
print("\nScanning apps in", apps_dir)
if not os.path.isdir(apps_dir):
    print("No apps directory found at", apps_dir)
    sys.exit(1)

for name in sorted(os.listdir(apps_dir)):
    path = os.path.join(apps_dir, name)
    if not os.path.isdir(path):
        continue
    if not os.path.exists(os.path.join(path, "__init__.py")):
        # not a package
        continue
    print("\n---- APP:", name, "----")
    for sub in ("urls", "models"):
        modname = f"gchub_db.apps.{name}.{sub}"
        try:
            mod = import_module(modname)
            print("OK import", modname)
        except Exception:
            print("ERROR importing", modname)
            traceback.print_exc()

print("\nDiagnostic complete")
