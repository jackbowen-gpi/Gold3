import importlib.util
import os
import sys

print("CWD=", os.getcwd())
print("sys.path[0:6]=", sys.path[0:6])
print("DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))

for name in ("gchub_db", "gchub_db.conftest"):
    try:
        spec = importlib.util.find_spec(name)
        print("\nfind_spec", name, "->", spec)
    except Exception as e:
        print("\nfind_spec", name, "-> ERROR:", e)

print('\nsys.modules keys containing "conftest":')
for k in sorted(sys.modules.keys()):
    if "conftest" in k:
        print("  ", k, "->", getattr(sys.modules[k], "__file__", None))

print("\nPaths exist:")
print("repo-root conftest:", os.path.exists(os.path.join(os.getcwd(), "conftest.py")))
print(
    "package conftest:",
    os.path.exists(os.path.join(os.getcwd(), "gchub_db", "conftest.py")),
)
print(
    "inner conftest:",
    os.path.exists(os.path.join(os.getcwd(), "gchub_db", "gchub_db", "conftest.py")),
)
