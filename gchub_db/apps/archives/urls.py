from django.urls import re_path as url

from gchub_db.apps.archives.views import search

urlpatterns = [
    url(r"^search/(?P<archive>\D+)/$", search, name="archive_search"),
]
