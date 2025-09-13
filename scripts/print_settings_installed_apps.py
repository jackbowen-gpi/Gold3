"""Print INSTALLED_APPS from the project's settings for debugging."""

import importlib
import os
import sys

repo_root = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), "manage.py")))
parent = os.path.dirname(repo_root)
sys.path.insert(0, repo_root)
sys.path.insert(1, parent)
settings = importlib.import_module("gchub_db.settings")
print("\n".join(settings.INSTALLED_APPS))
