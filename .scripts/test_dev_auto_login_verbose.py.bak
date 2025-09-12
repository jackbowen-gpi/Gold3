import os
import sys
import traceback
from datetime import datetime

log = []


def log_message(msg):
    ts = datetime.utcnow().isoformat()
    log.append(f"[{ts}] {msg}")


try:
    sys.path.insert(0, os.getcwd())
    log_message("cwd added to sys.path")
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
        log_message("set DJANGO_SETTINGS_MODULE=gchub_db.settings")

    import django

    log_message("imported django")
    try:
        django.setup()
        log_message("django.setup() ok")
    except Exception as e:
        log_message("django.setup() failed: " + repr(e))
        raise

    from django.test.client import RequestFactory
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.auth.middleware import AuthenticationMiddleware
    from django.conf import settings

    log_message(f"DEBUG={settings.DEBUG}")

    from gchub_db.middleware.dev_auto_login import DevAutoLoginMiddleware

    log_message("imported DevAutoLoginMiddleware")

    rf = RequestFactory()
    req = rf.get("/")
    log_message("created RequestFactory request")

    # Attach middlewares
    SessionMiddleware(lambda r: None).process_request(req)
    log_message("session middleware attached")
    AuthenticationMiddleware(lambda r: None).process_request(req)
    log_message("auth middleware attached")

    mw = DevAutoLoginMiddleware(lambda r: r)
    log_message("middleware instance created")
    try:
        res = mw(req)
        log_message("middleware __call__ returned")
    except Exception:
        log_message("middleware raised exception:")
        log_message(traceback.format_exc())

    user = getattr(req, "user", None)
    if user and getattr(user, "is_authenticated", False):
        log_message(
            f"DEV ADMIN logged in: username={getattr(user,'username',None)} "
            f"is_superuser={getattr(user,'is_superuser',None)}"
        )
    else:
        log_message("DEV ADMIN NOT logged in; user repr: " + repr(user))

except Exception:
    log_message("top-level exception:")
    log_message(traceback.format_exc())

finally:
    out = "\n".join(log)
    dest = os.path.join(".scripts", "dev_auto_login_result.txt")
    try:
        with open(dest, "w", encoding="utf-8") as f:
            f.write(out)
    except Exception as e:
        print("failed to write log:", e)
    print(out)
