"""General includes that are useful throughout the entire application."""

import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission, User
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone


def paginate_get_request(request):
    """Accepts a request object, grabs the GET keys and returns the proper
    GET querystring to retain persistence across different pages.
    """
    extra_link = []
    for key in request.GET:
        # Don't include the 'page' key, as these would pile up. We can't
        # just delete the key from request.GET, it's immutable. Can't convert
        # to dict and encode, unicode problem.
        if key != "page":
            valuelist = request.GET.getlist(key)
            extra_link.extend(["%s=%s" % (key, val) for val in valuelist])
    # If there's something to return join the list together as a string with
    # ampersands and then prefix it with an ampersand to pad between existing
    # arguments.
    if len(extra_link) > 0:
        extra_link = "&".join(extra_link)
        extra_link = "&" + extra_link
        return extra_link
    else:
        return ""


def rgb_to_hex(rgb_tuple):
    """Convert an (R, G, B) tuple to #RRGGBB"""
    hexcolor = "#%02x%02x%02x" % rgb_tuple
    # that's it! '%02x' means zero-padded, 2-digit hex values
    return hexcolor


def send_err_message(request, msg_text):
    """Sends an error message."""
    messages.add_message(request, messages.INFO, msg_text)


def send_succ_message(request, msg_text):
    """Sends a success message."""
    messages.add_message(request, messages.INFO, msg_text)


def get_user_workflow_access(request):
    """Return a tuple of workflows that the user has accesss to."""
    view_workflows = []
    if request.user.has_perm("accounts.foodservice_access"):
        view_workflows.append("Foodservice")
    if request.user.has_perm("accounts.beverage_access"):
        view_workflows.append("Beverage")
    if request.user.has_perm("accounts.container_access"):
        view_workflows.append("Container")
    if request.user.has_perm("accounts.carton_access"):
        view_workflows.append("Carton")
    return view_workflows


def filter_query_same_perms(request, qset):
    """Takes a request object and a queryset, returns a queryset of users with same permissions as
    the requesting user.
    """
    qset_1 = User.objects.none()
    qset_2 = User.objects.none()
    qset_3 = User.objects.none()
    qset_4 = User.objects.none()
    if request.user.has_perm("accounts.beverage_access"):
        workflow_permission = Permission.objects.get(codename="beverage_access")
        qset_1 = (
            qset.filter(Q(groups__in=workflow_permission.group_set.all()))
            .values("id")
            .query
        )
    if request.user.has_perm("accounts.foodservice_access"):
        workflow_permission = Permission.objects.get(codename="foodservice_access")
        qset_2 = (
            qset.filter(Q(groups__in=workflow_permission.group_set.all()))
            .values("id")
            .query
        )
    if request.user.has_perm("accounts.container_access"):
        workflow_permission = Permission.objects.get(codename="container_access")
        qset_3 = (
            qset.filter(Q(groups__in=workflow_permission.group_set.all()))
            .values("id")
            .query
        )
    if request.user.has_perm("accounts.carton_access"):
        workflow_permission = Permission.objects.get(codename="carton_access")
        qset_4 = (
            qset.filter(Q(groups__in=workflow_permission.group_set.all()))
            .values("id")
            .query
        )
    # Return a query of users that appear in any of the 3 sub-qsets.
    return User.objects.filter(
        Q(id__in=qset_1) | Q(id__in=qset_2) | Q(id__in=qset_3) | Q(id__in=qset_4)
    ).order_by("username")


def set_cookie(response, key, value, expire=None):
    """Simplifies cookie expiration time setting.

    response: (HttpResponse)
    key: (string)
    value: (string)
    expire: (int) Number of seconds the cookie will last.
    """
    if expire is None:
        # If no expiration
        max_age = 365 * 24 * 60 * 60
    else:
        max_age = expire
    # Use an aware UTC datetime for cookie expiration to avoid naive/aware warnings
    expires_dt = timezone.now().astimezone(datetime.timezone.utc) + datetime.timedelta(
        seconds=max_age
    )
    expires = expires_dt.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires)


def _utcnow_naive():
    """Return a naive UTC datetime in a conservative way.

    Prefer Django's timezone.now() when available (aware), convert to UTC and
    drop tzinfo to preserve legacy naive-UTC semantics. Fall back to
    datetime.datetime.utcnow() if timezone.now() is unavailable.
    """
    try:
        now = timezone.now()
        # Ensure it's in UTC and naive
        return now.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    except Exception:
        return datetime.datetime.utcnow()


def send_info_mail(subject, body, recipients, fail_silently=True):
    """This is a very light wrapper for send_mail which can be used to quickly
    enable fail_silently and a few other things for all emails.

    This function is more aimed at general, informative messages rather than
    critical stuff.

    recipients: (list of str) Emails to send to.
    """
    send_mail(
        subject,
        body,
        settings.EMAIL_FROM_ADDRESS,
        recipients,
        fail_silently=fail_silently,
    )
