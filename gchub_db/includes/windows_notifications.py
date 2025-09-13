#!/usr/bin/env python
"""
Modern Windows notification system to replace Growl.
Uses Windows 10/11 native toast notifications.
"""

# Remove win10toast dependency: always use fallback (console output only)
NOTIFICATIONS_AVAILABLE = False


# Stub WindowsNotificationManager: always prints to console
class WindowsNotificationManager:
    """
    Stub notification manager: always prints to console (no-op for Windows toasts)
    """

    def send_notification(self, title, message, duration=10, icon_path=None, threaded=False):
        print(f"NOTIFICATION: {title} - {message}")
        return False

    def send_sticky_notification(self, title, message, icon_path=None):
        print(f"STICKY NOTIFICATION: {title} - {message}")
        return False


# Global instance for easy importing
windows_notifier = WindowsNotificationManager()
