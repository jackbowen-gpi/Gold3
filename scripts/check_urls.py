import os
import sys

# Ensure repo root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.test_settings")

import django
from django.urls import get_resolver, reverse

django.setup()
resolver = get_resolver(None)
print("reverse_dict_keys_sample:", list(resolver.reverse_dict.keys())[:50])
print("has_job_search_in_reverse_dict:", "job_search" in resolver.reverse_dict)
try:
    print("reverse job_search ->", reverse("job_search"))
except Exception as e:
    print("reverse error:", type(e), e)

# List top-level url pattern names
print("url pattern names:")
for p in resolver.url_patterns:
    try:
        print("  pattern:", getattr(p, "name", None), "->", getattr(p, "pattern", None))
    except Exception:
        print("  pattern repr:", repr(p))
