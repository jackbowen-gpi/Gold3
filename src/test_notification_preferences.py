#!/usr/bin/env python
"""
Test script to verify the new notification preferences work correctly.
"""

import os
import sys
import django
from django.contrib.auth.models import User

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()


def test_notification_preferences():
    """Test the new notification preferences functionality."""

    print("🔔 Testing Notification Preferences")
    print("=" * 50)

    # Get or create a test user
    user, created = User.objects.get_or_create(
        username="test_notifications",
        defaults={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    if created:
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"📋 Using existing test user: {user.username}")

    # Test the master notification toggle
    profile = user.profile

    print("\n📊 Current notification settings:")
    print(f"   Master toggle (notifications_enabled): {profile.notifications_enabled}")
    print(f"   Item approvals: {profile.growl_hear_approvals}")
    print(f"   New carton jobs: {profile.growl_hear_new_carton_jobs}")

    # Test notification with master toggle enabled
    print("\n🧪 Testing notifications with master toggle ON...")
    profile.notifications_enabled = True
    profile.save()

    result1 = profile.growl_at(
        "Test Notification",
        "This should work - master toggle is ON",
        pref_field="growl_hear_approvals",
    )
    print(f"   Result: {'✅ Success' if result1 else '❌ Failed'}")

    # Test notification with master toggle disabled
    print("\n🧪 Testing notifications with master toggle OFF...")
    profile.notifications_enabled = False
    profile.save()

    result2 = profile.growl_at(
        "Test Notification",
        "This should be blocked - master toggle is OFF",
        pref_field="growl_hear_approvals",
    )
    if not result2:
        print("   Result: ❌ Correctly blocked")
    else:
        print("   Result: ⚠️ Unexpected - should have been blocked")

    # Restore default state
    profile.notifications_enabled = True
    profile.save()
    print("\n✅ Restored master toggle to ON")

    print("\n🎉 Notification preferences test completed!")
    print("📍 You can now visit: http://127.0.0.1:8000/accounts/preferences/growl/")


if __name__ == "__main__":
    test_notification_preferences()
