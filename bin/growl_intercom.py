#!/usr/bin/env python
"""Send arbitrary Growl messages to selected recipient groups."""

import sys

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from django.contrib.auth.models import Permission, User

# When this is True, print some useful debugging output.
DEBUG = False


def growl_message(message):
    """Notify everyone when a new CodeChange is posted."""
    if DEBUG:
        print("* Sending: '%s'" % message)

    # We only want to growl at clemson employees.
    clemson_perm = Permission.objects.get(codename="clemson_employee")
    clemson_groups = clemson_perm.group_set.all()

    # Find users in the groups that have workflow permissions AND are
    # Clemson employees.
    users = User.objects.filter(groups__in=clemson_groups, is_active=True)

    if DEBUG:
        print("* Recipients:")
    for user in users:
        if DEBUG:
            print(user, user.groups.all().order_by("id"))
        user.profile.growl_at("ANNOUNCEMENT", message, sticky=True)
    if DEBUG:
        print("* Total:", users.count())


def main():
    """Announce a provided message via Growl to the configured recipient groups."""
    # Grab a list of arguments. Arg 0 is the command name, don't want that.
    arg_list = sys.argv[1:]

    # You must provide some kind of message. Fail if no arguments given.
    if len(arg_list) < 1:
        print("Provide the message as the argument to the command.")
        sys.exit(1)

    # Bombs away!
    growl_message(" ".join(arg_list))


if __name__ == "__main__":
    main()
