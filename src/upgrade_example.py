"""
Example: update your UserProfile.growl_at() method to use Windows notifications.
You can either replace the existing method or add this as a new method.
"""

# Add this import at the top of gchub_db/apps/accounts/models.py
from includes.notification_manager import send_user_notification

# Then in your UserProfile class, you can either:


# Option 1: Replace the existing growl_at method
def growl_at(self, title, description, sticky=False, pref_field=None):
    """
    Send a notification to the user via Windows Toast notifications.

    This replaces the old Growl functionality with modern Windows notifications.
    Falls back to console output if Windows notifications are unavailable.

    Args:
        title: (str) Title of the notification
        description: (str) The message to be displayed below the title.
        sticky: (bool) When True, notification uses maximum duration.
        pref_field: (str) The name of one of the growl_ fields on the
                          UserProfile model. If it evaluates to True, send
                          the notification.
    """
    return send_user_notification(
        user_profile=self,
        title=title,
        description=description,
        sticky=sticky,
        pref_field=pref_field,
    )


# Option 2: Add a new method and keep the old one for transition
def notify_windows(self, title, description, sticky=False, pref_field=None):
    """
    Send a Windows notification to the user.
    Modern replacement for growl_at() method.
    """
    return send_user_notification(
        user_profile=self,
        title=title,
        description=description,
        sticky=sticky,
        pref_field=pref_field,
    )


# For the bulk notification scripts like growl_code_changes.py and growl_intercom.py,
# you can update them to use:
# from includes.notification_manager import bulk_notify_users

# Replace the loop that calls user.profile.growl_at() with:
# bulk_notify_users(
#     users_queryset=users,
#     title="GOLD Change Announcement",
#     message=change.change,
#     pref_field="growl_hear_gold_changes",
# )
