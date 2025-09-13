r"""
Module .scripts\post_login_dev.py
"""

import requests
import os

url = "http://127.0.0.1:8000/accounts/login/"
username = os.environ.get("DEV_ADMIN_USER", "dev_admin")
password = os.environ.get("DEV_ADMIN_PASSWORD", "devpass")
with requests.Session() as s:
    r = s.get(url)
    # find csrf token cookie or hidden input
    csrf = s.cookies.get("csrftoken") or None
    data = {"username": username, "password": password}
    if csrf:
        data["csrfmiddlewaretoken"] = csrf
    r2 = s.post(url, data=data, allow_redirects=False)
    print("post status", r2.status_code)
    print("set-cookie after post:", r2.headers.get("set-cookie"))
    print("sessionid in cookies after post:", s.cookies.get("sessionid"))
