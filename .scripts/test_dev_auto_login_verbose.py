import os
import sys
import traceback
from datetime import datetime

log = []


def l(msg):
    ts = datetime.utcnow().isoformat()
    log.append(f"[{ts}] {msg}")


try:
    sys.path.insert(0, os.getcwd())
    l("cwd added to sys.path")
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
        l("set DJANGO_SETTINGS_MODULE=gchub_db.settings")

    import django

    l("imported django")
    try:
        django.setup()
        l("django.setup() ok")
    except Exception as e:
        l("django.setup() failed: " + repr(e))
        raise

    from django.test.client import RequestFactory
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.auth.middleware import AuthenticationMiddleware
    from django.conf import settings

    l(f"DEBUG={settings.DEBUG}")

    from gchub_db.middleware.dev_auto_login import DevAutoLoginMiddleware

    l("imported DevAutoLoginMiddleware")

    rf = RequestFactory()
    req = rf.get("/")
    l("created RequestFactory request")

    # Attach middlewares
    SessionMiddleware(lambda r: None).process_request(req)
    l("session middleware attached")
    AuthenticationMiddleware(lambda r: None).process_request(req)
    l("auth middleware attached")

    mw = DevAutoLoginMiddleware(lambda r: r)
    l("middleware instance created")
    try:
        res = mw(req)
        l("middleware __call__ returned")
    except Exception:
        l("middleware raised exception:")
        l(traceback.format_exc())

    user = getattr(req, "user", None)
    if user and getattr(user, "is_authenticated", False):
        l(
            f"DEV ADMIN logged in: username={getattr(user,'username',None)} is_superuser={getattr(user,'is_superuser',None)}"
        )
    else:
        l("DEV ADMIN NOT logged in; user repr: " + repr(user))

except Exception:
    l("top-level exception:")
    l(traceback.format_exc())

finally:
    out = "\n".join(log)
    dest = os.path.join(".scripts", "dev_auto_login_result.txt")
    try:
        with open(dest, "w", encoding="utf-8") as f:
            f.write(out)
    except Exception as e:
        print("failed to write log:", e)
    print(out)
