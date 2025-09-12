#!/usr/bin/env python
"""Scan for CodeChange objects without a growl_date and notify affected workflows."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
from django.contrib.auth.models import Permission, User

# Back to the ordinary imports
from django.utils import timezone

from gchub_db.apps.news.models import CodeChange

# When this is True, print some useful debugging output.
DEBUG = False


def growl_code_change(change):
    """Notify everyone when a new CodeChange is posted."""
    if DEBUG:
        print("* Sending '%s' to %s" % (change.change, change.workflows_affected.all()))

    # This will hold the merged QuerySet of groups to look for.
    users = User.objects.none()

    for workflow in change.workflows_affected.all():
        try:
            # Find the permission that coincides with this workflow.
            permission = Permission.objects.get(codename="%s_access" % workflow.name.lower())
            # Combine querysets to build the list of groups to look for.
            groups = permission.group_set.all()
            users = users | User.objects.filter(groups__in=groups)
        except Permission.DoesNotExist:
            # Abandon ship, matey!
            continue

    # We only want to growl at clemson employees.
    clemson_perm = Permission.objects.get(codename="clemson_employee")
    clemson_groups = clemson_perm.group_set.all()

    # Find users in the groups that have workflow permissions AND are
    # Clemson employees.
    users = users.filter(groups__in=clemson_groups, is_active=True).distinct()

    if DEBUG:
        print("* Recipients:")
    for user in users:
        if DEBUG:
            print(user, user.groups.all().order_by("id"))
        user.profile.growl_at(
            "GOLD Change Announcement",
            change.change,
            pref_field="growl_hear_gold_changes",
        )
    if DEBUG:
        print("* Total:", users.count())

    # This prevents a CodeChange from being Growled more than once.
    change.growl_date = timezone.now()
    change.save()


def main():
    """Announce CodeChange objects without a growl_date to recipients."""
    new_changes = CodeChange.objects.filter(growl_date=None)
    for change in new_changes:
        growl_code_change(change)


if __name__ == "__main__":
    main()
