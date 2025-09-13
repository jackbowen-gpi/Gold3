"""Custom admin views for administrative tools."""

from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
import json

from gchub_db.includes.windows_notifications import (
    WindowsNotificationManager,
    NOTIFICATIONS_AVAILABLE,
)


class SendAlertForm(forms.Form):
    """Form for sending alert notifications to user groups."""

    TEMPLATE_CHOICES = [
        ("", "-- Select a template or write custom message --"),
        ("server_maintenance", "🔧 Server Maintenance"),
        ("urgent_update", "⚡ Urgent System Update"),
        ("production_alert", "🚨 Production Alert"),
        ("deadline_reminder", "📅 Deadline Reminder"),
        ("system_slowdown", "🐌 System Performance Notice"),
        ("new_feature", "✨ New Feature Announcement"),
        ("training_session", "🎓 Training Session"),
        ("holiday_schedule", "🎄 Holiday Schedule Notice"),
        ("backup_reminder", "💾 Backup Reminder"),
        ("security_alert", "🔒 Security Alert"),
    ]

    template = forms.ChoiceField(
        choices=TEMPLATE_CHOICES,
        required=False,
        help_text="Select a pre-written template or leave blank for custom message",
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "onchange": "updateMessageFromTemplate(this.value)",
            }
        ),
    )

    title = forms.CharField(
        max_length=100,
        help_text="Short, clear title for the notification",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g., System Maintenance Alert",
            }
        ),
    )

    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "form-control",
                "placeholder": "Enter your alert message here...",
            }
        ),
        help_text="The main message content that users will see",
    )

    target_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select which user groups should receive this alert",
        required=False,
    )

    target_all_users = forms.BooleanField(
        required=False,
        help_text="Send to all active users (overrides group selection)",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    duration = forms.IntegerField(
        initial=10,
        min_value=3,
        max_value=30,
        help_text="How long the notification should stay visible (seconds)",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "3", "max": "30"}),
    )

    test_mode = forms.BooleanField(
        required=False,
        help_text="Send only to yourself for testing",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


def is_admin_or_above(user):
    """Check if user is admin or superuser."""
    return user.is_staff or user.is_superuser


@user_passes_test(is_admin_or_above)
def send_alert_view(request):
    """Admin view for sending alert notifications."""
    if not NOTIFICATIONS_AVAILABLE:
        messages.error(request, "Notification system is not available.")
        return redirect("/admin/")

    template_messages = {
        "server_maintenance": ("Server Maintenance: The system will be down for maintenance from X to Y. Please save your work."),
        "urgent_update": ("Urgent System Update: Please save your work and refresh your browser within the next 10 minutes."),
        "production_alert": ("Production Alert: High priority jobs need immediate attention. Please check your queue."),
        "deadline_reminder": ("Deadline Reminder: Multiple jobs are due today. Please check your queue and prioritize accordingly."),
        "system_slowdown": ("System Performance: The system may be running slower than usual. We are investigating the issue."),
        "new_feature": ("New Feature: A new feature has been added to the system. Check the workflow section for updates!"),
        "training_session": ("Training Session: Join us for training on new system features. Details in your email."),
        "holiday_schedule": ("Holiday Schedule: Please note changed hours for the upcoming holiday. Check the calendar for details."),
        "backup_reminder": ("Backup Reminder: Please ensure all important work is saved. System backup starting soon."),
        "security_alert": ("Security Alert: Please verify your account security settings and update your password if needed."),
    }

    if request.method == "POST":
        form = SendAlertForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            message = form.cleaned_data["message"]
            target_groups = form.cleaned_data["target_groups"]
            target_all_users = form.cleaned_data["target_all_users"]
            duration = form.cleaned_data["duration"]
            test_mode = form.cleaned_data["test_mode"]

            # Get target users
            if test_mode:
                target_users = [request.user]
                mode_text = "test mode"
            elif target_all_users:
                target_users = User.objects.filter(is_active=True)
                mode_text = "all active users"
            elif target_groups.exists():
                target_users = User.objects.filter(groups__in=target_groups, is_active=True).distinct()
                group_names = ", ".join([g.name for g in target_groups])
                mode_text = f"groups: {group_names}"
            else:
                messages.error(
                    request,
                    "Please select target groups or choose to send to all users.",
                )
                return render(
                    request,
                    "admin/send_alert.html",
                    {
                        "form": form,
                        "template_messages": json.dumps(template_messages),
                        "title": "Send Alert Notification",
                    },
                )

            # Send notifications
            notification_manager = WindowsNotificationManager()
            success_count = 0
            error_count = 0

            for user in target_users:
                try:
                    # For now, we'll send to all users on the same machine.
                    # In a real deployment, you'd need to track which machine
                    # each user is on.
                    sender_name = request.user.get_full_name() or request.user.username
                    result = notification_manager.send_notification(
                        title=f"[ADMIN ALERT] {title}",
                        message=f"{message}\n\n— {sender_name}",
                        duration=duration,
                    )
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception:
                    error_count += 1

            # Show success message
            if success_count > 0:
                success_msg = f"Alert sent successfully to {success_count} user(s) in {mode_text}."
                messages.success(request, success_msg)
            if error_count > 0:
                error_msg = f"Failed to send to {error_count} user(s). They may not be on this machine."
                messages.warning(request, error_msg)

            return redirect(request.path)

    else:
        form = SendAlertForm()

    return render(
        request,
        "admin/send_alert.html",
        {
            "form": form,
            "template_messages": json.dumps(template_messages),
            "title": "Send Alert Notification",
            "groups": Group.objects.all(),
            "total_users": User.objects.filter(is_active=True).count(),
        },
    )


# Register this as a custom admin view
def register_admin_views():
    """Register custom admin views."""
    # This will be called from the admin's get_urls method
    pass
