"""
Shim module: re-export `gchub_db.includes.windows_notifications` implementation.

Some older imports use `includes.windows_notifications` (top-level). The
real implementation lives in `gchub_db.includes.windows_notifications`.
This shim keeps both import paths working and ensures the patched code is
used at runtime.
"""

try:
    # Load the inner packaged implementation by file path to avoid
    # recursive package import issues. The inner implementation lives at
    # <repo-root>/gchub_db/includes/windows_notifications.py.
    import os
    import importlib.util

    repo_root = os.path.dirname(os.path.dirname(__file__))
    inner_path = os.path.join(repo_root, "gchub_db", "includes", "windows_notifications.py")

    if os.path.exists(inner_path):
        spec = importlib.util.spec_from_file_location("gchub_db.inner_windows_notifications", inner_path)
        _mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mod)  # type: ignore

        WindowsNotificationManager = getattr(_mod, "WindowsNotificationManager")
        windows_notifier = getattr(_mod, "windows_notifier")
        NOTIFICATIONS_AVAILABLE = bool(getattr(_mod, "NOTIFICATIONS_AVAILABLE", False))
    else:
        raise ImportError("Inner windows_notifications implementation not found")
except Exception:
    # If that fails (rare), provide a minimal fallback so imports don't fail
    NOTIFICATIONS_AVAILABLE = False
    import logging

    logging.warning("Windows notifications implementation not available; using console fallback")

    class WindowsNotificationManager:
        """Minimal fallback notification manager that prints to console."""

        def send_notification(self, title, message, duration=10, icon_path=None, threaded=False):
            print(f"NOTIFICATION (fallback): {title} - {message}")
            return False

        def send_sticky_notification(self, title, message, icon_path=None):
            print(f"STICKY NOTIFICATION (fallback): {title} - {message}")
            return False

    # single global instance for compatibility with existing callers
    windows_notifier = WindowsNotificationManager()

__all__ = ["WindowsNotificationManager", "windows_notifier", "NOTIFICATIONS_AVAILABLE"]
