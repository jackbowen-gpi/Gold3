"""Create or ensure a PlatePackage/Platemaker exists for local development."""

import os
import sys
from pathlib import Path

# Add the repository root (parent of scripts/)
# to sys.path so the gchub_db package is importable
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django

django.setup()

from gchub_db.apps.workflow.models.general import Platemaker, PlatePackage

name = "Shelbyville"
platetype = "Corrugate"

platemaker, pm_created = Platemaker.objects.get_or_create(name=name)
if pm_created:
    print(f"Created Platemaker: {platemaker} (id={platemaker.id})")
else:
    print(f"Platemaker exists: {platemaker} (id={platemaker.id})")

pp, pp_created = PlatePackage.objects.get_or_create(
    platemaker=platemaker, platetype=platetype, defaults={"active": True}
)
if pp_created:
    print(f"Created PlatePackage: {pp} (id={pp.id})")
else:
    print(f"PlatePackage exists: {pp} (id={pp.id})")
