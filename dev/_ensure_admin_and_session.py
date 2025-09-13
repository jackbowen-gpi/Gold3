import os
import sys

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore

# Ensure imports behave like manage.py so running this script directly works.
# Insert the repository root and its parent on sys.path (same approach as manage.py).
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent = os.path.dirname(repo_root)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if parent not in sys.path:
    sys.path.insert(1, parent)

# Create a superuser if missing and create a session for them.
# Writes dev/admin_session_cookie.txt containing 'sessionid=...'

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

try:
    import django

    django.setup()
except Exception as e:
    print("Django setup failed:", e)
    raise

User = get_user_model()

username = os.environ.get("DEV_ADMIN_USER", "dev_admin")
password = os.environ.get("DEV_ADMIN_PASSWORD", "devpass")
email = os.environ.get("DEV_ADMIN_EMAIL", "dev_admin@example.com")

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        "email": email,
        "is_staff": True,
        "is_superuser": True,
    },
)

if created:
    user.set_password(password)
    user.save()
    print(f"Created admin user: {username}")
else:
    changed = False
    if not user.is_staff:
        user.is_staff = True
        changed = True
    if not user.is_superuser:
        user.is_superuser = True
        changed = True
    if changed:
        user.save()
        print(f"Updated admin flags for user: {username}")
    else:
        print(f"Admin user exists: {username}")

# Create a session that logs in this user
s = SessionStore()
s["_auth_user_id"] = str(user.pk)
s["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
# _auth_user_hash is optional but good to set
try:
    s["_auth_user_hash"] = user.get_session_auth_hash()
except Exception:
    pass
s.save()

cookie_value = f"sessionid={s.session_key}"
out_path = os.path.join(os.path.dirname(__file__), "admin_session_cookie.txt")
with open(out_path, "w") as f:
    f.write(cookie_value + "\n")

print("Wrote admin session cookie to:", out_path)
print(cookie_value)
