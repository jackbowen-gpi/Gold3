"""Account-Related Views"""

import datetime
import json
from datetime import timedelta
from types import SimpleNamespace

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from mwclient import Site

from gchub_db.includes.notification_manager import send_user_notification
# windows_notifications import removed; use plyer or notification_daemon instead

import gchub_db.apps.workflow.app_defs as workflow_defs
from gchub_db.apps.calendar.models import Event
from gchub_db.apps.error_tracking.models import Error
from gchub_db.apps.joblog.app_defs import (
    JOBLOG_TYPE_BILLING,
    JOBLOG_TYPE_CRITICAL,
    JOBLOG_TYPE_ITEM_9DIGIT,
    JOBLOG_TYPE_ITEM_APPROVED,
    JOBLOG_TYPE_ITEM_PROOFED_OUT,
    JOBLOG_TYPE_ITEM_REVISION,
    JOBLOG_TYPE_NOTE,
)
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.news.models import CodeChange
from gchub_db.apps.workflow.models import ItemReview, Job
from gchub_db.includes import general_funcs


def preferences_contact_info(request):
    """Simple placeholder for contact info preferences."""
    pagevars = {"page_title": "Preferences - Contact Info"}
    return render(request, "preferences/contact_info.html", context=pagevars)


def preferences_growl_preferences(request):
    """Simple placeholder for growl/notification preferences."""
    pagevars = {"page_title": "Preferences - Growl"}
    return render(request, "preferences/growl_preferences.html", context=pagevars)


@login_required
def preferences_settings(request):
    """Handle user settings including legacy search preference and search criteria."""
    if request.method == "POST":
        # Get the checkbox values
        use_legacy_search = request.POST.get("use_legacy_search") == "1"
        notifications_enabled = request.POST.get("notifications_enabled") == "1"

        # Job search criteria
        job_search_brand = request.POST.get("job_search_brand") == "1"
        job_search_customer = request.POST.get("job_search_customer") == "1"
        job_search_po_number = request.POST.get("job_search_po_number") == "1"
        job_search_comments = request.POST.get("job_search_comments") == "1"
        job_search_instructions = request.POST.get("job_search_instructions") == "1"
        job_search_salesperson = request.POST.get("job_search_salesperson") == "1"
        job_search_artist = request.POST.get("job_search_artist") == "1"

        # Item search criteria
        item_search_description = request.POST.get("item_search_description") == "1"
        item_search_upc = request.POST.get("item_search_upc") == "1"
        item_search_brand = request.POST.get("item_search_brand") == "1"
        item_search_customer = request.POST.get("item_search_customer") == "1"
        item_search_comments = request.POST.get("item_search_comments") == "1"
        item_search_specifications = (
            request.POST.get("item_search_specifications") == "1"
        )

        # Update user profile notifications setting
        if hasattr(request.user, "profile"):
            request.user.profile.notifications_enabled = notifications_enabled
            request.user.profile.save()

        # Store in session for now (until DB migration can be applied)
        request.session["use_legacy_search"] = use_legacy_search

        # Store job search criteria
        request.session["job_search_brand"] = job_search_brand
        request.session["job_search_customer"] = job_search_customer
        request.session["job_search_po_number"] = job_search_po_number
        request.session["job_search_comments"] = job_search_comments
        request.session["job_search_instructions"] = job_search_instructions
        request.session["job_search_salesperson"] = job_search_salesperson
        request.session["job_search_artist"] = job_search_artist

        # Store item search criteria
        request.session["item_search_description"] = item_search_description
        request.session["item_search_upc"] = item_search_upc
        request.session["item_search_brand"] = item_search_brand
        request.session["item_search_customer"] = item_search_customer
        request.session["item_search_comments"] = item_search_comments
        request.session["item_search_specifications"] = item_search_specifications

        request.session.modified = True  # Ensure session is saved

        # Add success message
        messages.success(request, "Search preferences saved successfully!")

        return HttpResponseRedirect(request.path)

    # Get current values (from session or defaults)
    pagevars = {
        "page_title": "Preferences - Settings",
        "use_legacy_search": request.session.get("use_legacy_search", True),
        "notifications_enabled": getattr(
            request.user.profile, "notifications_enabled", True
        )
        if hasattr(request.user, "profile")
        else True,
        # Job search criteria
        "job_search_brand": request.session.get("job_search_brand", True),
        "job_search_customer": request.session.get("job_search_customer", True),
        "job_search_po_number": request.session.get("job_search_po_number", True),
        "job_search_comments": request.session.get("job_search_comments", True),
        "job_search_instructions": request.session.get("job_search_instructions", True),
        "job_search_salesperson": request.session.get("job_search_salesperson", True),
        "job_search_artist": request.session.get("job_search_artist", True),
        # Item search criteria
        "item_search_description": request.session.get("item_search_description", True),
        "item_search_upc": request.session.get("item_search_upc", True),
        "item_search_brand": request.session.get("item_search_brand", True),
        "item_search_customer": request.session.get("item_search_customer", True),
        "item_search_comments": request.session.get("item_search_comments", True),
        "item_search_specifications": request.session.get(
            "item_search_specifications", True
        ),
    }
    return render(request, "preferences/settings.html", context=pagevars)


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Your password was successfully updated!")
            return HttpResponseRedirect("/")
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "preferences/change_password.html", {"form": form})


def _seperate_events_by_day(events, date_attrib_name):
    """This is a generic function to separate events into a list representing
    days of the month that contain events occuring on that day.
    """
    # Stores the integer day of the month of the last event.
    last_day = None
    # Stores the events occurring on the current day.
    current_day_events = []
    # This is the final list of events, grouped in lists by day.
    daily_events = []

    for event in events:
        day_of_month = getattr(event, date_attrib_name).day
        # The day changed, move on to a new day list.
        if last_day != day_of_month:
            # This prevents adding empty lists on the first item in the loop.
            if current_day_events:
                daily_events.append(current_day_events)
            last_day = day_of_month
            current_day_events = []
        current_day_events.append(event)

    # This will pick up the last day and add it to the list too.
    if current_day_events:
        daily_events.append(current_day_events)

    return daily_events


def add_wiki_quote(request):
    quote = ""
    title = ""
    site = Site(
        ("http", "wiki.na.graphicpkg.pri"),
        path="/",
    )
    site.login("quotemaker", "pass123word")

    # print request
    if request.GET:
        quote = request.GET.get("quote")
        title = request.GET.get("title")
    person = request.GET.get("person")

    page = site.pages[title]
    text = page.text()
    # Ensure values are str() on Python 3 and handle None values safely
    quote_text = "" if quote is None else str(quote)
    person_text = "" if person is None else str(person)
    page.save(
        text + str("\n----\n") + str('"' + quote_text + '" -- ' + person_text),
        "added quote",
    )

    return HttpResponseRedirect("/")


def _get_events_by_day():
    """Retrieve a list of events, grouped by day (sub-lists)."""
    # use timezone-aware now and dates
    today = timezone.now().date()
    end_event_range = today + timedelta(days=7)
    events = Event.objects.filter(event_date__range=(today, end_event_range)).order_by(
        "event_date"
    )
    return _seperate_events_by_day(events, "event_date")


def _get_changes_by_day():
    """Retrieve a list of GOLD changes, grouped by day (sub-lists)."""
    changes = CodeChange.objects.all().order_by("-creation_date")[:5]
    return _seperate_events_by_day(changes, "creation_date")


def _get_user_hold_job_list(request):
    """Gets the user_hold_list and user_job_list for display on the index page."""
    # use timezone-aware date arithmetic
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    ninety_days_ago = tomorrow + timedelta(days=-90)
    thirty_days_ago = tomorrow + timedelta(days=-30)
    fortyfive_days_ago = tomorrow + timedelta(days=-45)
    this_user = request.user
    view_workflows = general_funcs.get_user_workflow_access(request)

    user_hold_list = []
    user_job_list = []
    if this_user.has_perm("accounts.in_artist_pulldown"):
        job_activity = (
            JobLog.objects.filter(
                type__in=[
                    JOBLOG_TYPE_ITEM_APPROVED,
                    JOBLOG_TYPE_CRITICAL,
                    JOBLOG_TYPE_ITEM_REVISION,
                    JOBLOG_TYPE_ITEM_PROOFED_OUT,
                    JOBLOG_TYPE_BILLING,
                    JOBLOG_TYPE_ITEM_9DIGIT,
                    JOBLOG_TYPE_NOTE,
                ],
                event_time__range=(ninety_days_ago, tomorrow),
            )
            .values("job")
            .query
        )
        try:
            user_job_list = (
                Job.objects.filter(
                    workflow__name__in=view_workflows,
                    id__in=job_activity,
                    artist=this_user,
                    status="Active",
                )
                .exclude(todo_list_mode=workflow_defs.TODO_LIST_MODE_HIDDEN)
                .order_by("-due_date")
            )
        except Exception:
            user_job_list = []

        try:
            user_hold_list = (
                Job.objects.filter(
                    workflow__name__in=view_workflows,
                    id__in=job_activity,
                    artist=this_user,
                    status="Hold",
                )
                .exclude(todo_list_mode=workflow_defs.TODO_LIST_MODE_HIDDEN)
                .order_by("-due_date")[:8]
            )
        except Exception:
            user_hold_list = []

    elif this_user.has_perm("accounts.salesperson"):
        job_activity = (
            JobLog.objects.filter(
                type__in=[
                    JOBLOG_TYPE_ITEM_APPROVED,
                    JOBLOG_TYPE_CRITICAL,
                    JOBLOG_TYPE_ITEM_REVISION,
                    JOBLOG_TYPE_ITEM_PROOFED_OUT,
                    JOBLOG_TYPE_BILLING,
                    JOBLOG_TYPE_NOTE,
                ],
                event_time__range=(fortyfive_days_ago, tomorrow),
            )
            .values("job")
            .query
        )
        try:
            user_job_list = Job.objects.filter(
                Q(archive_disc__isnull=True) | Q(archive_disc__exact=""),
                workflow__name__in=view_workflows,
                id__in=job_activity,
                salesperson=this_user,
                status="Active",
            ).order_by("-due_date")
        except Exception:
            user_job_list = []
        user_hold_list = []

    elif this_user.has_perm("accounts.is_fsb_csr"):
        job_activity = (
            JobLog.objects.filter(
                type__in=[
                    JOBLOG_TYPE_ITEM_APPROVED,
                    JOBLOG_TYPE_ITEM_PROOFED_OUT,
                    JOBLOG_TYPE_ITEM_9DIGIT,
                    JOBLOG_TYPE_NOTE,
                ],
                event_time__range=(thirty_days_ago, tomorrow),
            )
            .values("job")
            .query
        )
        try:
            user_job_list = Job.objects.filter(
                Q(archive_disc__isnull=True) | Q(archive_disc__exact=""),
                workflow__name__in=view_workflows,
                id__in=job_activity,
                csr=this_user,
            ).order_by("-due_date")
        except Exception:
            user_job_list = []
        user_hold_list = []

    # List of items approved but no nine digit number for sales.
    # Purpose of making sure POs get going on approved items. Increase completions.
    user_approve_list = []
    job_activity = (
        JobLog.objects.filter(
            type=JOBLOG_TYPE_ITEM_APPROVED,
            event_time__range=(ninety_days_ago, tomorrow),
            item__fsb_nine_digit__in=("",),
        )
        .values("job")
        .query
    )
    if job_activity:
        user_approve_list = Job.objects.filter(
            workflow__name="Foodservice", id__in=job_activity, salesperson=this_user
        ).order_by("-due_date")

    print(user_approve_list)

    return user_hold_list, user_job_list, user_approve_list


@login_required
def index(request):
    """Default Database Index page."""
    #    Old pre-itemreview-model methode
    #    demand_rejections = Item.objects.filter(demand_plan_date__isnull=False,
    #                                            demand_plan_ok=False,
    #                                            job__workflow__name="Foodservice").exclude(demand_plan_comments__in=("Resubmitted",
    #                                                                                                                 "Accepted",)).count()
    #
    #    plant_rejections = Item.objects.filter(preflight_date__isnull=False,
    #                                           preflight_ok=False).exclude(plant_comments__in=("Resubmitted",
    #                                                                                                "Accepted",)).count()
    #
    #    mkt_rejections = Item.objects.filter(mkt_review_date__isnull=False,
    #                                         mkt_review_ok=False,
    #                                         mkt_review_needed=True).exclude(mkt_review_comments__in=("Resubmitted",
    #                                                                                                 "Accepted,")).count()
    #
    #    rejected_items = demand_rejections + plant_rejections + mkt_rejections

    """
    Provides the number of rejected items in the new Item Review model.
    """

    rejections_demand = (
        ItemReview.objects.filter(
            review_catagory="demand",
            review_date__isnull=False,
            review_ok=False,
        )
        .exclude(resubmitted=True)
        .exclude(comments="Resubmitted")
        .count()
    )

    rejections_mkt = (
        ItemReview.objects.filter(
            review_date__isnull=False,
            review_catagory="market",
            review_ok=False,
        )
        .exclude(resubmitted=True)
        .exclude(comments="Resubmitted")
        .count()
    )

    rejections_plant = (
        ItemReview.objects.filter(
            review_catagory="plant", review_date__isnull=False, review_ok=False
        )
        .exclude(resubmitted=True)
        .exclude(comments="Resubmitted")
        .count()
    )

    items_rejected = rejections_demand + rejections_plant + rejections_mkt

    user_hold_list, user_job_list, user_approve_list = _get_user_hold_job_list(request)
    stickied_jobs = Job.objects.filter(
        artist=request.user, todo_list_mode=workflow_defs.TODO_LIST_MODE_STICKIED
    )

    # Calculate the time since the last error was recorded.
    # Use .first() to avoid IndexError if no Error records exist.
    last_error_obj = Error.objects.all().order_by("-id").first()
    if last_error_obj:
        try:
            now = timezone.now()
            last_reported = last_error_obj.reported_date
            # If the stored value is naive, assume UTC (legacy) and make it aware.
            if timezone.is_naive(last_reported):
                last_reported = last_reported.replace(tzinfo=datetime.timezone.utc)
            # normalize both to UTC for safe subtraction
            now_utc = now.astimezone(datetime.timezone.utc)
            last_reported_utc = last_reported.astimezone(datetime.timezone.utc)
            time_diff = now_utc - last_reported_utc
            last_error = time_diff.days
        except Exception:
            last_error = None
    else:
        # No errors recorded yet
        last_error = None

    # Set color to green by default. Only adjust color when we have a value.
    last_error_color = "#00CC00"
    if last_error is not None:
        if last_error < 30:
            # Red
            last_error_color = "#FF0033"
        elif last_error < 60:
            # Orange
            last_error_color = "#FF9900"

    pagevars = {
        "page_title": "Home",
        "user_job_list": user_job_list,
        "user_hold_list": user_hold_list,
        "user_approve_list": user_approve_list,
        "user_stickied_jobs": stickied_jobs,
        "items_rejected": items_rejected,
        "last_error": last_error,
        "last_error_color": last_error_color,
    }

    # Only do these if we're dealing with a Clemson employee. Otherwise,
    # save a lot of query time and don't mess with the events since we won't
    # be displaying them.
    if request.user.has_perm("accounts.clemson_employee"):
        # Retrieve a list of events, grouped by day (sub-lists).
        pagevars["daily_events"] = _get_events_by_day()
        pagevars["gold_changes"] = _get_changes_by_day()

        # Calculate what changes happened today using UTC-naive now.
        today = general_funcs._utcnow_naive().date()
        start_date = today - timedelta(days=3)
        changes_today = CodeChange.objects.filter(
            creation_date__range=(start_date, today)
        ).count()
        pagevars["gold_changes_today"] = changes_today

    return render(request, "accounts/index.html", context=pagevars)


def home(request):
    """Public homepage: show the authenticated index to logged-in users,
    otherwise render a simple public landing page.
    """
    if request.user.is_authenticated:
        return index(request)

    pagevars = {"page_title": "Welcome to GOLD"}
    return render(request, "home.html", context=pagevars)


def logout_get(request):
    """Allow logout via GET for compatibility with older templates/links.

    This performs the same action as the Django `LogoutView` but accepts GET
    so legacy anchors that point to the logout URL don't get 405.
    """
    # Perform logout and redirect to configured LOGOUT_REDIRECT_URL
    auth_logout(request)
    redirect_to = getattr(settings, "LOGOUT_REDIRECT_URL", "/")
    return HttpResponseRedirect(redirect_to)


def office_contacts(request):
    """Contacts for the Clemson Office. We'll totally link this to the User
    system later, huh? HELL YES WE WILL. Go Thundercuddles!
    """
    pagevars = {
        "page_title": "Clemson Hub Contacts",
    }

    return render(request, "accounts/office_contacts.html", context=pagevars)


class LoginForm(forms.Form):
    """Used to render the user login form."""

    # Username field
    username = forms.ChoiceField(
        choices=[], widget=forms.Select(attrs={"style": "width:174px"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"style": "width:170px"})
    )

    def __init__(self, request, *args, **kwargs):
        """Generate the drop-down of active users so they don't have to type their
        username in.
        """
        super(LoginForm, self).__init__(*args, **kwargs)

        # Store the list of formatted usernames.
        user_list = []
        # Go through the filtered users and format the name for the drop-down.
        for user in User.objects.filter(is_active=True).order_by("last_name"):
            name = "%s, %s" % (user.last_name, user.first_name)
            user_list.append((user.id, name))

        # Default the selection to the user ID in the last_login_id cookie.
        self.fields["username"].choices = user_list
        self.fields["username"].initial = request.COOKIES.get("last_login_id", None)


def login_form(request):
    """User login prompt."""
    pagevars = {
        "page_title": "Login",
        "form": LoginForm(request),
    }
    if request.user.is_authenticated:
        return HttpResponseRedirect("/")

    if request.POST:
        raw_username = request.POST.get("username")
        password = request.POST.get("password")

        # Accept either a numeric user id (legacy dropdown) or a literal username.
        username = None
        if raw_username is not None:
            try:
                # Try interpreting as an integer id first (legacy behavior)
                uid = int(raw_username)
                username = User.objects.get(id=uid).username
            except (ValueError, TypeError, User.DoesNotExist):
                # Fallback: treat the POST value as a username string
                try:
                    username = User.objects.get(username=raw_username).username
                except User.DoesNotExist:
                    username = None

        user = authenticate(username=username, password=password) if username else None
        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect to a success page.
                httpresp = HttpResponseRedirect("/")
                # Set this cookie so the next time the browser is pointed at the
                # login page, it will select the last user that logged in.
                general_funcs.set_cookie(httpresp, "last_login_id", user.id)
                return httpresp
            else:
                # Return a 'disabled account' error message
                pagevars["errors"] = "Your account has been disabled."
        else:
            pagevars["errors"] = "Unable to login with specified username/password."

    # context_instance = RequestContext(request)
    return render(request, "accounts/login.html", context=pagevars)


# ===== NOTIFICATION TEST VIEWS =====


@login_required
def notification_test_page(request):
    """Display the notification test page."""
    return render(request, "accounts/notification_test.html")


@login_required
@csrf_exempt
@require_POST
def test_notification(request):
    """Handle AJAX requests to test notifications."""
    try:
        data = json.loads(request.body)
        notification_type = data.get("type", "basic")

        if notification_type == "direct":
            # Test direct Windows notification manager
            # WindowsNotificationManager removed; use plyer or notification_daemon instead
            print(
                "NOTIFICATION: Direct Notification Test - This is a direct test of the Windows notification manager."
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Direct notification sent (console stub)",
                    "type": "direct",
                }
            )

        elif notification_type == "user_profile":
            # Avoid touching request.user.profile (may trigger DB column access if migrations
            # haven't been applied). Use a lightweight stub that provides the .user attr.
            stub_profile = SimpleNamespace(user=request.user)
            send_user_notification(
                user_profile=stub_profile,
                title="User Profile Test",
                description="This notification was sent via user.profile.growl_at() method.",
                sticky=False,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "UserProfile.growl_at() (stub) sent",
                    "type": "user_profile",
                }
            )

        elif notification_type == "user_profile_sticky":
            stub_profile = SimpleNamespace(user=request.user)
            send_user_notification(
                user_profile=stub_profile,
                title="Sticky Notification Test",
                description="This is a persistent notification that requires user action to dismiss.",
                sticky=True,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Sticky notification (stub) sent",
                    "type": "user_profile_sticky",
                }
            )

        elif notification_type == "notification_manager":
            # Avoid accessing request.user.profile directly; use stub
            stub_profile = SimpleNamespace(user=request.user)
            result = send_user_notification(
                user_profile=stub_profile,
                title="Notification Manager Test",
                description="This notification was sent via the send_user_notification function.",
                sticky=False,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Notification manager sent successfully: {result}",
                    "type": "notification_manager",
                }
            )

        elif notification_type == "code_change_simulation":
            # Simulate what bin/growl_code_changes.py does
            # Avoid touching request.user.profile to prevent DB column errors during tests
            stub_profile = SimpleNamespace(user=request.user)
            send_user_notification(
                user_profile=stub_profile,
                title="GOLD Change Announcement",
                description="Simulated code change notification: Fixed CSRF tokens in workflow JavaScript files.",
                pref_field=None,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Code change simulation sent successfully",
                    "type": "code_change_simulation",
                }
            )

        elif notification_type == "intercom_simulation":
            # Simulate what bin/growl_intercom.py does
            stub_profile = SimpleNamespace(user=request.user)
            send_user_notification(
                user_profile=stub_profile,
                title="ANNOUNCEMENT",
                description="Simulated intercom message: System maintenance scheduled for tonight at 11 PM.",
                sticky=True,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Intercom simulation sent successfully",
                    "type": "intercom_simulation",
                }
            )

        else:
            # Basic test
            # WindowsNotificationManager removed; use plyer or notification_daemon instead
            print("NOTIFICATION: Basic Test - This is a basic notification test.")
            return JsonResponse(
                {
                    "success": True,
                    "message": "Basic notification sent (console stub)",
                    "type": "basic",
                }
            )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Error sending notification: {str(e)}",
                "error": str(e),
            }
        )
