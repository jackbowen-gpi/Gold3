import importlib.util
import os
import sys

print("CWD=", os.getcwd())
print("ENV DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))
print("sys.path[0:6]=", sys.path[0:6])
for name in ("gchub_db", "gchub_db.gchub_db"):
    try:
        spec = importlib.util.find_spec(name)
    except Exception as e:
        spec = f"ERROR: {e}"
    print("\nfind_spec", name, "->", spec)

p = os.path.abspath(os.path.join(os.getcwd(), "gchub_db", "gchub_db", "__init__.py"))
print("\ninner __init__ path exists:", os.path.exists(p), p)
p2 = os.path.abspath(os.path.join(os.getcwd(), "gchub_db", "__init__.py"))
print("repo-root __init__ exists:", os.path.exists(p2), p2)
