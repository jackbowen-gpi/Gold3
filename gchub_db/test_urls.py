from django.http import HttpResponse
from django.urls import path

# Lightweight test URLConf for pytest / manage.py test runs.
# Keep this file dependency-free (no include()) to avoid import-time side-effects.


def _simple_ok(request):
    return HttpResponse("ok")


# Provide a set of named URLs commonly used by tests and templates.
urlpatterns = [
    path("", _simple_ok, name="root"),
    path("logout/", _simple_ok, name="logout"),
    path("job/search/", _simple_ok, name="job_search"),
    path("joblog_filtered_default/", _simple_ok, name="joblog_filtered_default"),
    path("joblog_add_note/", _simple_ok, name="joblog_add_note"),
    path("joblog_fullview/", _simple_ok, name="joblog_fullview"),
    path("workflow/reports/list/", _simple_ok, name="list_reports"),
]
