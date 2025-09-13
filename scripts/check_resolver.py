import sys

sys.path.insert(0, r"c:\Dev\Gold3")
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()
from django.urls import get_resolver

resolver = get_resolver(None)
names = [k for k in resolver.reverse_dict.keys() if isinstance(k, str)]
print("todo_list" in names)
print("sample registered names count", len(names))
print("some names:", list(names)[:30])
