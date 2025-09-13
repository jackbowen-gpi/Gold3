from django.urls import re_path as url

from gchub_db.apps.timesheet.views import add, delete, home

urlpatterns = [
    url(r"^$", home, name="timesheet_home"),
    url(r"^(?P<user_id>\d+)/$", home, name="timesheet_home"),
    url(r"^add/$", add, name="timesheet_add"),
    url(r"^edit/(?P<timesheet_id>\d+)/$", add, name="timesheet_edit"),
    url(r"^delete/(?P<timesheet_id>\d+)/$", delete, name="timesheet_delete"),
]
