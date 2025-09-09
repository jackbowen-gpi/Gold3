"""Video Player Views"""

from django.shortcuts import render

from gchub_db.apps.joblog.app_defs import *


def home(request):
    """This is an experimental view to host videos"""
    pagevars = {
        "page_title": "Art Request Introduction",
    }

    return render(request, "video_player/home.html", context=pagevars)
