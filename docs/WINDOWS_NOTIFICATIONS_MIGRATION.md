# Windows Notifications Migration Guide

## Overview
This guide shows how to replace your old Growl notification system with modern Windows Toast notifications.

## Benefits of Windows Notifications
- ✅ **Native Windows integration** - No third-party Mac software required
- ✅ **Modern UI** - Clean, consistent with Windows 10/11 design
- ✅ **Action Center integration** - Notifications appear in Windows Action Center
- ✅ **Cross-platform libraries available** - Can expand to Linux/Mac later
- ✅ **No network configuration** - Direct local notifications
- ✅ **Better reliability** - No network dependencies

## Installation Steps

### 1. Install Windows notification library
Choose one option:

```powershell
# Option 1: win10toast (Recommended for simplicity)
pip install win10toast==0.9

# Option 2: plyer (Cross-platform support)
# pip install plyer==2.1.0

# Option 3: windows-toasts (Most modern features)
# pip install windows-toasts==1.0.0
```

### 2. Update requirements.txt
Add to your `requirements.txt`:
```
win10toast==0.9
```

### 3. Integration Options

#### Option A: Direct Replacement (Recommended)
Replace your existing `UserProfile.growl_at()` method:

1. **Backup your current method** (just in case):
   ```python
   def growl_at_old(self, title, description, sticky=False, pref_field=None):
       # Your existing Growl implementation
   ```

2. **Replace with Windows notifications**:
   ```python
   def growl_at(self, title, description, sticky=False, pref_field=None):
       """Send a Windows Toast notification to the user."""
       from includes.notification_manager import send_user_notification
       return send_user_notification(
           user_profile=self,
           title=title,
           description=description,
           sticky=sticky,
           pref_field=pref_field
       )
   ```

#### Option B: Gradual Migration
Add a new method alongside the existing one:

```python
def notify_windows(self, title, description, sticky=False, pref_field=None):
    """Modern Windows notification method."""
    from includes.notification_manager import send_user_notification
    return send_user_notification(
        user_profile=self,
        title=title,
        description=description,
        sticky=sticky,
        pref_field=pref_field
    )
```

### 4. Update Bulk Notification Scripts

#### For `bin/growl_code_changes.py`:
Replace the user notification loop:

```python
# OLD:
for user in users:
    user.profile.growl_at(
        "GOLD Change Announcement",
        change.change,
        pref_field="growl_hear_gold_changes",
    )

# NEW:
from includes.notification_manager import bulk_notify_users
bulk_notify_users(
    users_queryset=users,
    title="GOLD Change Announcement",
    message=change.change,
    pref_field="growl_hear_gold_changes"
)
```

#### For `bin/growl_intercom.py`:
Similar update for the bulk messaging functionality.

### 5. Optional: Add Icon Support

Add to your Django settings:
```python
# settings.py
NOTIFICATION_ICON_PATH = os.path.join(MEDIA_ROOT, 'img', 'gold2logo.ico')
```

Convert your existing PNG logo to ICO format for best Windows compatibility.

### 6. Testing

Test the notifications:
```python
# In Django shell
from django.contrib.auth.models import User
user = User.objects.first()

# Test basic notification
user.profile.growl_at("Test", "Hello from Windows!")

# Test sticky notification
user.profile.growl_at("Important", "This is important!", sticky=True)

# Test with preferences
user.profile.growl_at(
    "Job Update",
    "New job available",
    pref_field="growl_hear_new_carton_jobs"
)
```

## Migration Timeline

### Phase 1: Setup (Day 1)
- Install `win10toast` library
- Add the notification manager files
- Test basic functionality

### Phase 2: Integration (Day 2-3)
- Update UserProfile.growl_at() method
- Test existing notification workflows
- Verify user preferences still work

### Phase 3: Scripts (Day 4)
- Update bulk notification scripts
- Test automated notifications
- Verify error handling

### Phase 4: Cleanup (Day 5)
- Remove old Growl dependencies (`gntp==1.0.3`)
- Remove `includes/netgrowl.py` if no longer needed
- Update user documentation

## Rollback Plan
If issues arise, you can quickly rollback by:
1. Restoring the original `growl_at()` method
2. Re-adding `gntp==1.0.3` to requirements
3. Reverting the script changes

## User Experience Changes
- **Appearance**: Modern Windows-style notifications instead of Growl
- **Location**: Notifications appear in bottom-right corner and Windows Action Center
- **Persistence**: "Sticky" notifications use maximum 60-second duration (Windows limitation)
- **Settings**: User preferences (growl_hear_*) continue to work the same way

## Future Enhancements
Once Windows notifications are stable, consider:
- Adding notification actions (buttons for approve/reject)
- Rich content support (images, progress bars)
- Cross-platform support (Linux/Mac) using `plyer`
- Web push notifications for remote users

Would you like me to help you implement any specific part of this migration?
