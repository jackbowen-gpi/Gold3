import json
import os
import sys

# Make repo importable like manage.py does
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
parent = os.path.dirname(repo_root)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if parent not in sys.path:
    sys.path.insert(1, parent)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django  # noqa: E402

django.setup()
from django.conf import settings  # noqa: E402

print(json.dumps(settings.DATABASES))
