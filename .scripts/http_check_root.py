r"""
Module .scripts\http_check_root.py
"""

import requests

resp = requests.get("http://127.0.0.1:8000/")
print("status:", resp.status_code)
print("headers:")
for k, v in resp.headers.items():
    if k.lower().startswith("set-cookie") or k.lower().startswith("cookie"):
        print(k + ":", v)
print(
    "\nHas session cookie:",
    any("sessionid" in h.lower() for h in resp.headers.get("set-cookie", "").split(",")),
)
# Print a small snippet of the body to look for the username
text = resp.text
print("\nbody snippet:\n", text[:800])
