#!/usr/bin/env python
"""
Django integration for Windows notifications to replace Growl.
Drop-in replacement for the existing growl_at() method.
"""

from django.conf import settings
import logging
from typing import Optional

# Import our Windows notification manager from the packaged implementation
try:
    from gchub_db.includes.windows_notifications import windows_notifier, NOTIFICATIONS_AVAILABLE as _NOTIF
    WINDOWS_NOTIFICATIONS_AVAILABLE = bool(_NOTIF)
except Exception:
    WINDOWS_NOTIFICATIONS_AVAILABLE = False
    logging.warning("Windows notifications not available")

def send_user_notification(
    user_profile,
    title: str,
    description: str,
    sticky: bool = False,
    pref_field: Optional[str] = None
) -> bool:
    """
    Send a Windows notification to a user - replacement for UserProfile.growl_at()
    
    Args:
        user_profile: UserProfile instance
        title: Notification title
        description: Notification message
        sticky: Whether notification should be persistent (maps to max duration)
        pref_field: User preference field to check (same as Growl system)
        
    Returns:
        bool: True if notification sent successfully
    """
    
    # Check master notification toggle first
    try:
        if not getattr(user_profile, 'notifications_enabled', True):
            # User has disabled all notifications
            return False
    except Exception:
        # If we can't read the preference (maybe during migration), allow notifications
        pass
    
    # Check user preferences if specified (same logic as original Growl)
    if pref_field:
        # Import constants locally to avoid import-time DB access
        try:
            from gchub_db.apps.accounts.models import GROWL_STATUS_DISABLED, GROWL_STATUS_STICKY
        except Exception:
            # If import fails for any reason, default to safe behaviour
            GROWL_STATUS_DISABLED = 0
            GROWL_STATUS_STICKY = 2

        # Guard preference lookup against missing DB columns or DB errors (e.g., migrations not applied)
        try:
            growl_pref = getattr(user_profile, pref_field, GROWL_STATUS_DISABLED)
        except Exception as e:
            # If reading the preference triggers a DB error (column missing) or similar,
            # log and fall back to default (treat as disabled to avoid unexpected notifications).
            logging.warning(
                "Could not read user preference '%s' for user %s: %s - falling back to disabled",
                pref_field,
                getattr(getattr(user_profile, 'user', None), 'username', repr(user_profile)),
                e,
            )
            growl_pref = GROWL_STATUS_DISABLED

        if growl_pref == GROWL_STATUS_DISABLED:
            # User doesn't want these notifications
            return False

        if growl_pref == GROWL_STATUS_STICKY:
            sticky = True
    
    # For debugging/development - log to console if Windows notifications not available
    if not WINDOWS_NOTIFICATIONS_AVAILABLE:
        print(f"NOTIFICATION for {user_profile.user.username}: {title} - {description}")
        return False
    
    try:
        # Get icon path from Django settings or use default
        icon_path = getattr(settings, 'NOTIFICATION_ICON_PATH', None)
        
        if sticky:
            success = windows_notifier.send_sticky_notification(
                title=title,
                message=description,
                icon_path=icon_path
            )
        else:
            success = windows_notifier.send_notification(
                title=title,
                message=description,
                duration=10,  # 10 seconds for normal notifications
                icon_path=icon_path
            )
            
        return success
        
    except Exception as e:
        logging.error(f"Windows notification error for user {user_profile.user.username}: {e}")
        # Fallback to console output
        print(f"NOTIFICATION for {user_profile.user.username}: {title} - {description}")
        return False


def bulk_notify_users(users_queryset, title: str, message: str, sticky: bool = False, pref_field: Optional[str] = None):
    """
    Send notifications to multiple users - replacement for bulk Growl operations.
    
    Args:
        users_queryset: QuerySet of User objects
        title: Notification title
        message: Notification message
        sticky: Whether notifications should be persistent
        pref_field: User preference field to check
    """
    success_count = 0
    
    for user in users_queryset:
        try:
            if hasattr(user, 'profile'):
                success = send_user_notification(
                    user.profile,
                    title=title,
                    description=message,
                    sticky=sticky,
                    pref_field=pref_field
                )
                if success:
                    success_count += 1
        except Exception as e:
            logging.error(f"Failed to notify user {user.username}: {e}")
            continue
    
    logging.info(f"Windows notifications sent to {success_count}/{users_queryset.count()} users")
    return success_count
