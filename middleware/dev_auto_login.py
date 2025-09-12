"""
Dev-only middleware to ensure a development admin user exists and is
automatically logged in for local development (DEBUG=True).

This middleware is intentionally defensive: it only runs when DEBUG is True
and will never raise an exception that could break app startup. It creates a
user with username 'devadmin' (if missing), marks them staff+superuser, and
logs them in via the standard Django auth backend on each incoming request
when not already authenticated.
"""

import sys
from django.conf import settings  # noqa: E402

try:
    from django.contrib.auth import get_user_model, login  # noqa: E402
    from django.contrib.auth.hashers import make_password  # noqa: E402
except Exception:  # pragma: no cover - safety if Django not configured yet
    get_user_model = None
    login = None


DEV_USERNAME = getattr(settings, "DEV_ADMIN_USERNAME", "devadmin")
DEV_PASSWORD = getattr(settings, "DEV_ADMIN_PASSWORD", "devadmin")
DEV_EMAIL = getattr(settings, "DEV_ADMIN_EMAIL", "devadmin@example.com")


class DevAutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only active in DEBUG mode to prevent accidental use in production.
        if not getattr(settings, "DEBUG", False):
            return self.get_response(request)

        # If Django isn't ready or auth imports failed, skip gracefully.
        if get_user_model is None or login is None:
            return self.get_response(request)

        try:
            # If user already authenticated, nothing to do.
            if getattr(request, "user", None) and request.user.is_authenticated:
                return self.get_response(request)

            User = get_user_model()

            # Create or get the dev admin user.
            user, created = User.objects.get_or_create(
                username=DEV_USERNAME,
                defaults={
                    "email": DEV_EMAIL,
                    "is_staff": True,
                    "is_superuser": True,
                    # store a hashed password (use set_password path for more
                    # complex workflows; keep simple here)
                    "password": make_password(DEV_PASSWORD),
                },
            )

            # If existing user wasn't superuser/staff, make it so.
            updated = False
            if not user.is_superuser:
                user.is_superuser = True
                updated = True
            if not user.is_staff:
                user.is_staff = True
                updated = True
            if updated:
                user.save()

            # Ensure the session backend is ready: set backend attribute and
            # log the user in. login() will attach the user id to the session.
            try:
                # For the common setup, use ModelBackend
                user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user)
            except Exception:
                # Best-effort: don't raise if login fails
                pass
        except Exception:
            # Ensure any unexpected failure here doesn't stop the app.
            try:
                # Write a harmless message to stderr to aid debugging.
                print("[dev_auto_login] failed to ensure dev admin", file=sys.stderr)
            except Exception:
                pass

        return self.get_response(request)


"""Middleware to auto-create and auto-login a development superuser.

This middleware only acts when `settings.DEBUG` is True. On the first
request it will ensure a superuser with username `dev_auto` exists and will
log that user into the session so you can iterate locally without manual
login. Password: `devpass` (change as desired).
"""
