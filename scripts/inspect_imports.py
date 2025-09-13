import importlib
import importlib.util
import sys

print("sys.path (first 10 entries):")
for i, p in enumerate(sys.path[:10]):
    print(i, p)


def show_spec(name):
    spec = importlib.util.find_spec(name)
    print("\nSPEC for", name)
    if spec is None:
        print("  None")
        return
    print("  origin:", spec.origin)
    print("  loader:", spec.loader)
    print("  submodule_search_locations:", spec.submodule_search_locations)


show_spec("gchub_db")
show_spec("gchub_db.apps")
show_spec("gchub_db.apps.workflow")
show_spec("gchub_db.apps.workflow.urls")

# Try importing the packages and show file location
print("\nAttempting imports...")
try:
    import gchub_db

    print(
        "gchub_db __file__:",
        getattr(gchub_db, "__file__", getattr(gchub_db, "__path__", None)),
    )
except Exception as e:
    print("import gchub_db failed:", e)
try:
    import gchub_db.apps.workflow as wf

    print(
        "gchub_db.apps.workflow __file__:",
        getattr(wf, "__file__", getattr(wf, "__path__", None)),
    )
except Exception as e:
    print("import gchub_db.apps.workflow failed:", e)

print("\nListing gchub_db directory:")
import os

root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
print("root:", root)
print(os.listdir(root)[:50])
