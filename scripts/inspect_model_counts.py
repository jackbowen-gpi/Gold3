"""Diagnostic helper: attempts to count rows for every registered
model and prints full tracebacks for any exceptions. Run with
the dev Postgres env vars set when using Postgres.
"""

import os
import pathlib
import sys
import traceback

# Ensure settings load like manage.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

import django
from django.apps import apps

# Make sure the project root is on sys.path so 'gchub_db' can be imported
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

try:
    django.setup()
except Exception:
    print("Failed to setup Django:")
    traceback.print_exc()
    sys.exit(2)

models = list(apps.get_models())
print(f"Found {len(models)} models. Starting counts...", flush=True)

for m in models:
    name = f"{m.__module__}.{m.__name__}"
    try:
        cnt = m.objects.count()
        print(f"OK    {name}: {cnt}")
    except Exception:
        print(f"ERROR {name}:")
        traceback.print_exc()
    sys.stdout.flush()

print("Done.")
