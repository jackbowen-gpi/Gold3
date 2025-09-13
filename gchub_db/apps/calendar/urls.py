from django.urls import re_path as url

from gchub_db.apps.calendar.views import event_add, event_delete, event_view, month_overview

urlpatterns = [
    url(r"^$", month_overview, name="event-overview"),
    url(
        r"^month/(?P<year_num>\d+)/(?P<month_num>\d+)/$",
        month_overview,
        name="event-month_overview",
    ),
    url(
        r"^event/(?P<year_num>\d+)/(?P<month_num>\d+)/(?P<day_num>\d+)/add/$",
        event_add,
        name="event-add",
    ),
    url(r"^event/save/$", event_add, name="event-safe"),
    url(r"^event/(?P<event_id>\d+)/view/$", event_view, name="event-view"),
    url(r"^event/(?P<event_id>\d+)/delete/$", event_delete, name="event-delete"),
]
