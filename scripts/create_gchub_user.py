import os

import django

# Allow env override; default to using Postgres dev DB when USE_PG_DEV is set
os.environ.setdefault("USE_PG_DEV", os.environ.get("USE_PG_DEV", "1"))
os.environ.setdefault("DEV_DB_NAME", os.environ.get("DEV_DB_NAME", "gchub_dev"))
os.environ.setdefault("DEV_DB_HOST", os.environ.get("DEV_DB_HOST", "localhost"))
os.environ.setdefault("DEV_DB_PORT", os.environ.get("DEV_DB_PORT", "5432"))
os.environ.setdefault("DEV_DB_USER", os.environ.get("DEV_DB_USER", "postgres"))
os.environ.setdefault("DEV_DB_PASSWORD", os.environ.get("DEV_DB_PASSWORD", "postgres"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction

User = get_user_model()


def main():
    # Create group 'gchub' and grant all permissions (dev convenience)
    with transaction.atomic():
        group, group_created = Group.objects.get_or_create(name="gchub")
        perms = Permission.objects.all()
        group.permissions.set(perms)
        group.save()

        user_defaults = {
            "email": "gchub@example.com",
            "is_staff": True,
            "is_superuser": True,
        }
        user, user_created = User.objects.get_or_create(
            username="gchub", defaults=user_defaults
        )
        # set password and flags for dev convenience
        user.set_password("gchub")
        user.is_staff = True
        user.is_superuser = True
        user.save()
        user.groups.add(group)
        user.save()

    print(
        f"group_created={group_created} user_created={user_created} username={user.username} email={user.email}"
    )


if __name__ == "__main__":
    main()
