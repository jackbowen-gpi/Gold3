"""
Module .scripts\fetch_root.py
"""

import requests

r = requests.get("http://127.0.0.1:8000/", allow_redirects=True)
print("status", r.status_code)
print(r.text[:800])
