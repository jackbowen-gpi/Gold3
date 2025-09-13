r"""
Module dev\create_dev_admin.py
"""

import os
import sys

# Ensure the repository root (and its parent) are on sys.path so
# imports like `import gchub_db` resolve when running this script
# directly (for example: `python dev/create_dev_admin.py`). This
# mirrors the behavior in `manage.py`.
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent = os.path.dirname(repo_root)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if parent not in sys.path:
    sys.path.insert(1, parent)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

try:
    import django

    django.setup()
except Exception:
    # Provide a clear, immediate error message to help diagnose
    # import/path/settings issues when this script is executed.
    import traceback

    traceback.print_exc()
    print("\n--- sys.path (top 8 entries) ---")
    for p in sys.path[:8]:
        print(p)
    raise
from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.models import Permission  # noqa: E402

User = get_user_model()
u, created = User.objects.get_or_create(username="dev_admin", defaults={"email": "dev_admin@example.com"})
u.is_staff = True
u.is_superuser = True
u.set_password("pass123")
u.save()
# Assign all permissions (useful for non-superuser consumers, harmless for superuser)
perms = list(Permission.objects.all())
if perms:
    u.user_permissions.set(perms)
    u.save()
print("dev_admin created" if created else "dev_admin updated")
