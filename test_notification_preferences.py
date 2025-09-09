#!/usr/bin/env python
"""
Test script to verify the new notification preferences work correctly.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gchub_db.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from gchub_db.apps.accounts.models import UserProfile

def test_notification_preferences():
    """Test the new notification preferences functionality."""
    
    print("🔔 Testing Notification Preferences")
    print("=" * 50)
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_notifications',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"📋 Using existing test user: {user.username}")
    
    # Test the master notification toggle
    profile = user.profile
    
    print(f"\n📊 Current notification settings:")
    print(f"   Master toggle (notifications_enabled): {profile.notifications_enabled}")
    print(f"   Item approvals: {profile.growl_hear_approvals}")
    print(f"   New carton jobs: {profile.growl_hear_new_carton_jobs}")
    
    # Test notification with master toggle enabled
    print(f"\n🧪 Testing notifications with master toggle ON...")
    profile.notifications_enabled = True
    profile.save()
    
    result1 = profile.growl_at(
        "Test Notification", 
        "This should work - master toggle is ON", 
        pref_field="growl_hear_approvals"
    )
    print(f"   Result: {'✅ Success' if result1 else '❌ Failed'}")
    
    # Test notification with master toggle disabled
    print(f"\n🧪 Testing notifications with master toggle OFF...")
    profile.notifications_enabled = False
    profile.save()
    
    result2 = profile.growl_at(
        "Test Notification", 
        "This should be blocked - master toggle is OFF", 
        pref_field="growl_hear_approvals"
    )
    print(f"   Result: {'❌ Correctly blocked' if not result2 else '⚠️ Unexpected - should have been blocked'}")
    
    # Restore default state
    profile.notifications_enabled = True
    profile.save()
    print(f"\n✅ Restored master toggle to ON")
    
    print(f"\n🎉 Notification preferences test completed!")
    print(f"📍 You can now visit: http://127.0.0.1:8000/accounts/preferences/growl/")

if __name__ == '__main__':
    test_notification_preferences()
