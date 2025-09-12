"""
Create or update a development superuser for local development.

This script is intended to be run from the repository root inside the
project virtualenv. It creates or updates a `dev` user with administrative
privileges.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add repository root (one level up) so top-level packages referenced by
# settings (for example `api`) can be imported.
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

import django

django.setup()

from django.contrib.auth import get_user_model


def main():
    """
    Create or update the local development superuser `dev`.

    Idempotent: if the user exists, update password and privileges.
    """
    user_model = get_user_model()
    username = "dev"
    password = "pass123"
    email = "dev@example.local"

    try:
        user = user_model.objects.filter(username=username).first()
        if user:
            user.is_staff = True
            user.is_superuser = True
            user.email = email
            user.set_password(password)
            user.first_name = "dev"
            user.last_name = "admin"
            user.save()
            print(f"Updated existing user '{username}' and set admin privileges.")
        else:
            user = user_model.objects.create_superuser(username=username, email=email, password=password)
            user.first_name = "dev"
            user.last_name = "admin"
            user.save()
            print(f"Created superuser '{username}' with name 'Jack Bowen'.")
    except Exception as exc:
        print("Failed to create/update dev user:", exc)


if __name__ == "__main__":
    main()
