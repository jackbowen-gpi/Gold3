"""Useful general functions for the bin directory scripts."""

import os
import sys


def setup_paths():
    """Setup the Django environment."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    home_dir = os.path.dirname(root_dir)
    includes_dir = os.path.join(root_dir, "includes")
    sys.path.insert(0, home_dir)
    sys.path.insert(0, root_dir)
    sys.path.insert(0, includes_dir)
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
