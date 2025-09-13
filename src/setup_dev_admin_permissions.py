#!/usr/bin/env python
"""
Script to give dev_admin user all available permissions in the system.
This should fix any permission-related errors when testing with production data.
"""

import os
import sys
import django
from django.contrib.auth.models import User, Permission, Group

# Setup Django environment
sys.path.insert(0, "/workspace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
django.setup()


def main():
    print("Setting up dev_admin with all permissions...")

    # Get or create devtest user
    try:
        admin_user = User.objects.get(username="devtest")
        print(f"Found existing user: {admin_user.username}")
    except User.DoesNotExist:
        print("devtest user not found. Creating it...")
        admin_user = User.objects.create_superuser(username="devtest", email="devtest@localhost", password="devtest")
        print("Created devtest user with password: devtest")

    # Make sure user is superuser and staff
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.is_active = True
    admin_user.save()

    # Get all permissions in the system
    all_permissions = Permission.objects.all()
    print(f"Found {all_permissions.count()} total permissions in system")

    # Add all permissions to user
    admin_user.user_permissions.set(all_permissions)

    # Also add to all groups for good measure
    all_groups = Group.objects.all()
    print(f"Found {all_groups.count()} groups in system")

    for group in all_groups:
        admin_user.groups.add(group)

    admin_user.save()

    print(f"Successfully granted all {all_permissions.count()} permissions to devtest")
    print(f"Added devtest to all {all_groups.count()} groups")
    print("\nKey permissions verified:")

    # Check key permissions
    key_perms = [
        "foodservice_access",
        "beverage_access",
        "container_access",
        "carton_access",
        "in_artist_pulldown",
        "salesperson",
        "is_fsb_csr",
    ]

    for perm_code in key_perms:
        try:
            perm = Permission.objects.get(codename=perm_code)
            has_perm = admin_user.has_perm(f"{perm.content_type.app_label}.{perm_code}")
            print(f"  ✓ {perm_code}: {has_perm}")
        except Permission.DoesNotExist:
            print(f"  ✗ {perm_code}: NOT FOUND")

    print("\ndevtest is ready to test all functionality!")


if __name__ == "__main__":
    main()
