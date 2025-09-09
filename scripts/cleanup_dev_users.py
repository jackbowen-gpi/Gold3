r"""Cleanup legacy development user accounts and ensure a single canonical dev user.

Usage: run from repo root with the project's venv python:

    .\.venv\Scripts\python.exe scripts\cleanup_dev_users.py

Behavior:
- Looks for users with usernames in LEGACY_USERNAMES.
- Keeps a canonical username (CANONICAL_USERNAME) and will create it if missing.
- Transfers superuser/staff flags to canonical user if any legacy user had them.
- Deletes other legacy usernames after consolidating.
- Prints actions performed.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

import django

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

LEGACY_USERNAMES = ["dev", "dev_auto", "devadmin", "dev_admin", "devuser"]
CANONICAL_USERNAME = "dev"
CANONICAL_EMAIL = "dev@example.local"
CANONICAL_PASSWORD = "pass123"

print("Searching for legacy dev users...")
found = list(User.objects.filter(username__in=LEGACY_USERNAMES))
print("Found users:", [u.username for u in found])

# Ensure canonical exists
canonical = User.objects.filter(username=CANONICAL_USERNAME).first()
if not canonical:
    canonical = User.objects.create_superuser(
        CANONICAL_USERNAME, CANONICAL_EMAIL, CANONICAL_PASSWORD
    )
    canonical.first_name = "dev"
    canonical.last_name = "admin"
    canonical.save()
    print(f"Created canonical user '{CANONICAL_USERNAME}'.")

# Consolidate flags and then delete others
for u in found:
    if u.username == CANONICAL_USERNAME:
        continue
    changed = False
    if u.is_superuser and not canonical.is_superuser:
        canonical.is_superuser = True
        changed = True
    if u.is_staff and not canonical.is_staff:
        canonical.is_staff = True
        changed = True
    if changed:
        canonical.save()
        print(f"Transferred flags from {u.username} to {CANONICAL_USERNAME}.")
    if u.username != CANONICAL_USERNAME:
        try:
            u.delete()
            print(f"Deleted legacy user {u.username}.")
        except Exception as e:
            print(f"Failed to delete {u.username}: {e}")

print("Cleanup complete. Current dev users:")
print(
    list(
        User.objects.filter(username__in=[CANONICAL_USERNAME]).values_list(
            "username", "first_name", "last_name", "is_superuser", "is_staff"
        )
    )
)
