from django.urls import re_path as url

from gchub_db.apps.video_player.views import *

urlpatterns = [
    url(r"^$", home, name="video_player_home"),
]
