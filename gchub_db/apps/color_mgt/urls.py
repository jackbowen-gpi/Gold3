from django.urls import re_path as url

from gchub_db.apps.color_mgt.views import color_home, color_stats, color_stats_sorted

urlpatterns = [
    # Example for displaying a job.
    url(r"^home/$", color_home, name="color_home"),
    url(r"^stats/$", color_stats, name="color_stats"),
    url(r"^sorted/$", color_stats_sorted, name="color_stats_sorted"),
]
