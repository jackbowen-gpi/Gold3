from django.urls import re_path as url

from gchub_db.apps.news.views import search

urlpatterns = [
    url(r"^search/(?P<archive>\D+)/$", search, name="archive_search"),
]
