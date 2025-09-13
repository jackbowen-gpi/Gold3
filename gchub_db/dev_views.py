import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse


def set_dev_session(request):
    # Only available in DEBUG mode
    if not getattr(settings, "DEBUG", False):
        return HttpResponse("Not available", status=404)

    cookie_file = os.path.join(
        settings.BASE_DIR if hasattr(settings, "BASE_DIR") else os.getcwd(),
        "dev",
        "admin_session_cookie.txt",
    )
    if not os.path.exists(cookie_file):
        return HttpResponse("No dev session cookie found", status=404)

    raw = open(cookie_file, "r", encoding="utf-8").read().strip()
    # expects sessionid=... format
    if raw.startswith("sessionid="):
        val = raw.split("=", 1)[1]
    else:
        val = raw

    resp = HttpResponse('<html><body>Setting dev session and redirecting...<script>window.location="/"</script></body></html>')
    # set cookie for the current host
    resp.set_cookie("sessionid", val, path="/", httponly=False)
    return resp


def dev_whoami(request):
    """
    Dev-only endpoint: return a small JSON summary of request.user.

    Useful to verify that the session cookie produced by the helper is
    actually authenticating requests.
    """
    if not getattr(settings, "DEBUG", False):
        return HttpResponse("Not available", status=404)

    user = getattr(request, "user", None)
    if user is None:
        return JsonResponse({"authenticated": False, "user": None})

    return JsonResponse(
        {
            "authenticated": bool(getattr(user, "is_authenticated", False)),
            "username": getattr(user, "username", None),
            "is_staff": bool(getattr(user, "is_staff", False)),
            "is_superuser": bool(getattr(user, "is_superuser", False)),
            # Minimal repr for debugging
            "repr": str(user),
        }
    )
