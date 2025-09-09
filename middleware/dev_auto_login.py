"""Dev-only middleware to ensure a development admin user exists and is
automatically logged in for local development (DEBUG=True).

This middleware is intentionally defensive: it only runs when DEBUG is True
and will never raise an exception that could break app startup. It creates a
user with username 'devadmin' (if missing), marks them staff+superuser, and
logs them in via the standard Django auth backend on each incoming request
when not already authenticated.
"""

from django.conf import settings
import sys

try:
    from django.contrib.auth import get_user_model, login
    from django.contrib.auth.hashers import make_password
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

import os
from django.conf import settings
from django.contrib.auth import get_user_model, login


class DevAutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only enable in DEBUG mode to avoid altering prod behavior.
        if settings.DEBUG:
            try:
                # If user isn't authenticated, ensure dev user exists and log them in.
                # Only act when the request user isn't already authenticated as the canonical dev
                User = get_user_model()
                # Read canonical dev credentials from environment so the
                # middleware matches the helper script that creates the
                # dev admin. Defaults mirror dev/_ensure_admin_and_session.py
                username = os.environ.get("DEV_ADMIN_USER", "dev_admin")
                password = os.environ.get("DEV_ADMIN_PASSWORD", "devpass")
                user = User.objects.filter(username=username).first()
                if not user:
                    # create_superuser to ensure full permissions when first created
                    user = User.objects.create_superuser(
                        username=username, email="dev@example.com", password=password
                    )

                # Ensure canonical display name and admin flags are set on the dev account.
                # We update these on every request in DEBUG so local changes are resilient.
                try:
                    changed = False
                    if not user.is_superuser:
                        user.is_superuser = True
                        changed = True
                    if not user.is_staff:
                        user.is_staff = True
                        changed = True
                    if user.first_name != "dev" or user.last_name != "admin":
                        user.first_name = "dev"
                        user.last_name = "admin"
                        changed = True
                    # Ensure known development password (only on local dev)
                    user.set_password(password)
                    changed = True
                    if changed:
                        user.save()

                except Exception:
                    # If DB not ready or user model issues, continue without blocking.
                    pass

                # Log the dev user in for this request so the UI shows the expected account.
                try:
                    user.backend = "django.contrib.auth.backends.ModelBackend"
                    login(request, user)
                except Exception:
                    # If login fails (sessions not configured yet), skip silently.
                    pass
            except Exception:
                # Guard against DB/config errors during startup.
                pass

        response = self.get_response(request)
        return response
