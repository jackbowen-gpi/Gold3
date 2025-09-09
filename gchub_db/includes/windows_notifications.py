#!/usr/bin/env python
"""
Modern Windows notification system to replace Growl.
Uses Windows 10/11 native toast notifications.
"""

import logging
import threading
import warnings
from typing import Optional
import subprocess
import sys
import json
import urllib.request
import urllib.error

# Import win10toast while suppressing noisy deprecation/warning chatter that
# can come from pkg_resources (this keeps dev server output cleaner).
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from win10toast import ToastNotifier

    NOTIFICATIONS_AVAILABLE = True
except Exception:
    NOTIFICATIONS_AVAILABLE = False
    logging.warning("win10toast not available. Install with: pip install win10toast")

class WindowsNotificationManager:
    """
    Windows notification manager to replace Growl functionality.
    Provides cross-platform notification support with fallback options.
    """
    
    def __init__(self):
        # Do not create a long-lived ToastNotifier instance; create per-call to avoid
        # issues with internal state across threads on some environments.
        self.toaster = None
        
    def send_notification(
        self,
        title: str,
        message: str,
        duration: int = 10,
        icon_path: Optional[str] = None,
    threaded: bool = False
    ) -> bool:
        """
        Send a Windows toast notification.
        
        Args:
            title: Notification title
            message: Notification message body
            duration: How long to show (seconds) - max 60 for Windows
            icon_path: Path to icon file (.ico format preferred)
            threaded: Whether to run in background thread
            
        Returns:
            bool: True if notification was sent successfully
        """
        if not NOTIFICATIONS_AVAILABLE:
            # Fallback to console output
            print(f"NOTIFICATION: {title} - {message}")
            return False

        # Windows has a 60-second max duration limit
        duration = min(duration, 60)

        def _send_sync_local_process():
            """Run win10toast in a fresh Python process (main thread) to avoid
            issues when the current thread is not the main thread. This is the
            most reliable option for the devserver where request handlers run
            on worker threads.
            """
            try:
                # Build a small python snippet that calls win10toast from argv.
                code = (
                    "import sys;"
                    "from win10toast import ToastNotifier;"
                    "toaster=ToastNotifier();"
                    "title=sys.argv[1];msg=sys.argv[2];"
                    "duration=int(sys.argv[3]);"
                    "icon=sys.argv[4] if len(sys.argv)>4 and sys.argv[4] != '' else None;"
                    "toaster.show_toast(title, msg, duration=duration, icon_path=icon, threaded=False)"
                )

                args = [sys.executable, "-c", code, title, message, str(duration), icon_path or ""]
                # Start detached process so we don't block the request thread.
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                logging.exception("Failed to send Windows notification via subprocess")
                return False

        def _send_sync_inproc():
            """Call win10toast synchronously in-process on the current thread.
            This should only be used when running on the main thread.
            """
            try:
                toaster = ToastNotifier()
                toaster.show_toast(
                    title=title,
                    msg=message,
                    duration=duration,
                    icon_path=icon_path,
                    threaded=False,
                )
                return True
            except Exception:
                logging.exception("Synchronous in-process Windows notification failed")
                return False

        # If we're on the main thread, prefer an in-process synchronous call.
        if threading.current_thread() is threading.main_thread():
            return _send_sync_inproc()

        # Try daemon POST first — this will show the toast from a separate
        # process that owns a GUI/main thread. If daemon isn't reachable,
        # fall back to subprocess or in-process methods.
        try:
            payload = json.dumps({'title': title, 'message': message, 'duration': duration, 'icon': icon_path}).encode('utf-8')
            req = urllib.request.Request('http://127.0.0.1:5341/notify', data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                # we don't care about the response body; success means queued
                return True
        except (urllib.error.URLError, Exception):
            # daemon not running or request failed; continue to fallback
            pass

        # Not on the main thread: prefer launching a small subprocess that will
        # perform the toast on its own main thread. This avoids win10toast's
        # main-thread restriction and prevents C-level callback errors.
        try:
            return _send_sync_local_process()
        except Exception:
            logging.exception("Subprocess toast failed; attempting in-process fallback")
            # Last resort: try in-process (may fail with Not on MainThread warning)
            return _send_sync_inproc()
    
    def send_sticky_notification(
        self,
        title: str,
        message: str,
        icon_path: Optional[str] = None
    ) -> bool:
        """
        Send a persistent notification (Windows equivalent of sticky Growl).
        Windows doesn't have true "sticky" notifications, so we use max duration.
        """
        return self.send_notification(
            title=title,
            message=message,
            duration=60,  # Maximum allowed duration
            icon_path=icon_path,
            threaded=False  # Don't thread for sticky notifications
        )

# Global instance for easy importing
windows_notifier = WindowsNotificationManager()
