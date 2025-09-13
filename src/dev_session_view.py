r"""
Module src\dev_session_view.py
"""

import os

from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseServerError
from django.middleware.csrf import get_token
from django.shortcuts import redirect


def set_dev_session(request):
    """
    Read the dev/admin_session_cookie.txt file and set sessionid cookie
    then redirect to '/'.

    Only enabled when settings.DEBUG is True.
    """
    if not getattr(settings, "DEBUG", False):
        return HttpResponseNotFound("Dev session endpoint not available")

    cookie_path = os.path.join(
        getattr(settings, "PROJECT_ROOT", os.path.dirname(os.path.dirname(__file__))),
        "dev",
        "admin_session_cookie.txt",
    )
    if not os.path.exists(cookie_path):
        return HttpResponseNotFound(f"No admin session cookie file at: {cookie_path}")

    try:
        with open(cookie_path, "r", encoding="utf-8") as f:
            data = f.read().strip()
        # Expect 'sessionid=VALUE' or just VALUE
        if "=" in data:
            _, val = data.split("=", 1)
        else:
            val = data
        response = redirect("/")
        # Set host-only cookie (no domain) so it applies to 127.0.0.1 or localhost.
        # Session cookie must be HttpOnly for security; CSRF cookie must be
        # readable by JS/templates.
        response.set_cookie("sessionid", val, path="/", httponly=True)

        # Generate or fetch a CSRF token for this request and set the CSRF cookie
        try:
            token = get_token(request)
            csfname = getattr(settings, "CSRF_COOKIE_NAME", "csrftoken")
            # set cookie as non-httpOnly so template JS can read if necessary
            response.set_cookie(csfname, token, path="/", httponly=False)
        except Exception:
            # best-effort: if CSRF machinery isn't available, skip setting token
            pass

        return response
    except Exception as e:
        return HttpResponseServerError(str(e))
