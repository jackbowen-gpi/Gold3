"""
Workflow app package shim: re-export submodules that legacy code/tests import
directly from the package (for example: `from gchub_db.apps.workflow import views`).
"""

# Re-export the views package so legacy imports succeed without pulling
# in the entire models package (which imports many other apps).
from . import views as views  # re-export the views package

__all__ = ["views"]
