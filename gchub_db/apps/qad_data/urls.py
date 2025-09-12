from django.urls import re_path as url

from gchub_db.apps.qad_data.views import *

urlpatterns = [
    url(r"^$", search_printgroup, name="qad_data-search_printgroup"),
]
