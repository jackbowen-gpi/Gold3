from django.urls import re_path as url

from gchub_db.apps.catscanner.views import color_data, item_data, send_measurement

urlpatterns = [
    url(
        r"^item_data/(?P<job_id>\d+)/(?P<item_num>\d+)/$",
        item_data,
        name="catscanner-item_data",
    ),
    url(
        r"^color_data/(?P<job_id>\d+)/(?P<item_num>\d+)/(?P<color_num>\d+)/$",
        color_data,
        name="catscanner-color_data",
    ),
    url(
        r"^send_measurement/(?P<job_id>\d+)/(?P<item_num>\d+)/(?P<color_num>\d+)/$",
        send_measurement,
        name="catscanner-send_measurement",
    ),
]
