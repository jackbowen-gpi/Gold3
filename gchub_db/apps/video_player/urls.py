from django.urls import re_path as url

from gchub_db.apps.video_player.views import home

urlpatterns = [
    url(r"^$", home, name="video_player_home"),
]
