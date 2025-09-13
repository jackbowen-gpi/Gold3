import os
import sys
import pprint

# Ensure repo root is on sys.path (same behavior as manage.py)
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Use top-level settings module (manage.py sets DJANGO_SETTINGS_MODULE to 'settings')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django

django.setup()

from django.template import engines, TemplateDoesNotExist

e = engines["django"]
print("ENGINE DIRS:", e.dirs)
try:
    t = e.get_template("standard.html")
    print("FOUND template:", t)
except TemplateDoesNotExist as ex:
    print("NOTFOUND:", ex)
    tried = getattr(ex, "tried", None)
    print("TRIED:")
    pprint.pprint(tried)
