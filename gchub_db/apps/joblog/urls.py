from django.urls import re_path as url

from gchub_db.apps.joblog.views import (
    joblog_add_note,
    joblog_delete_log,
    joblog_delete_note,
    joblog_edit_note,
    joblog_filtered,
    joblog_fullview,
    joblog_standard,
)

urlpatterns = [
    url(r"^(?P<job_id>\d+)/standard/$", joblog_standard, name="joblog_standard"),
    url(r"^(?P<job_id>\d+)/filtered/$", joblog_filtered, name="joblog_filtered_default"),
    url(
        r"^(?P<job_id>\d+)/filtered/(?P<filter_type>\D+)/$",
        joblog_filtered,
        name="joblog_filtered",
    ),
    url(r"^(?P<job_id>\d+)/fullview/$", joblog_fullview, name="joblog_fullview"),
    url(r"^(?P<job_id>\d+)/addnote/$", joblog_add_note, name="joblog_add_note"),
    url(r"^(?P<log_id>\d+)/editnote/$", joblog_edit_note, name="joblog_edit_note"),
    url(r"^(?P<log_id>\d+)/delete/$", joblog_delete_log, name="joblog_delete_log"),
    url(r"^(?P<log_id>\d+)/deletenote/$", joblog_delete_note, name="joblog_delete_note"),
]
