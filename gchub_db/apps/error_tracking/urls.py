from django.urls import re_path as url

from gchub_db.apps.error_tracking.views import (
    error_tracking_home,
    error_tracking_add,
    error_tracking_delete,
)

urlpatterns = [
    url(r"^$", error_tracking_home, name="error_tracking_home"),
    url(r"^report/(?P<item_id>\d+)/$", error_tracking_add, name="error_tracking_add"),
    url(r"^year/(?P<year>\d+)/$", error_tracking_home, name="annual_error_report"),
    url(
        r"^delete/(?P<error_id>\d+)/$",
        error_tracking_delete,
        name="error_tracking_delete",
    ),
]
