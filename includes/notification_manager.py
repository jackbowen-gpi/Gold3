#!/usr/bin/env python
"""
Django integration for Windows notifications to replace Growl.
Drop-in replacement for the existing growl_at() method.
"""

import logging
from typing import Optional
import os
import requests


NOTIFICATION_DAEMON_URL = os.environ.get("NOTIFICATION_DAEMON_URL", "http://127.0.0.1:5341/notify")


def send_user_notification(
    user_profile,
    title: str,
    description: str,
    sticky: bool = False,
    pref_field: Optional[str] = None,
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
    # Check user preferences if specified (same logic as original Growl)
    if pref_field:
        from gchub_db.apps.accounts.models import (
            GROWL_STATUS_DISABLED,
            GROWL_STATUS_STICKY,
        )

        growl_pref = getattr(user_profile, pref_field, GROWL_STATUS_DISABLED)

        if growl_pref == GROWL_STATUS_DISABLED:
            # User doesn't want these notifications
            return False

        if growl_pref == GROWL_STATUS_STICKY:
            sticky = True

    # Send notification to the notification daemon via HTTP POST
    payload = {
        "title": title,
        "message": description,
        "duration": 60 if sticky else 10,
    }
    try:
        resp = requests.post(NOTIFICATION_DAEMON_URL, json=payload, timeout=1.0)
        if resp.status_code == 200:
            return True
        else:
            logging.warning(f"Notification daemon returned status {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        logging.warning(f"Could not send notification to daemon: {e}")
        print(f"NOTIFICATION for {user_profile.user.username}: {title} - {description}")
        return False


def bulk_notify_users(
    users_queryset,
    title: str,
    message: str,
    sticky: bool = False,
    pref_field: Optional[str] = None,
):
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
            if hasattr(user, "profile"):
                success = send_user_notification(
                    user.profile,
                    title=title,
                    description=message,
                    sticky=sticky,
                    pref_field=pref_field,
                )
                if success:
                    success_count += 1
        except Exception as e:
            logging.error(f"Failed to notify user {user.username}: {e}")
            continue

    logging.info(f"Windows notifications sent to {success_count}/{users_queryset.count()} users")
    return success_count
