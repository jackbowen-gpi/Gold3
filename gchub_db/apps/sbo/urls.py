from django.urls import re_path as url

from gchub_db.apps.sbo.views import SBOHome, SBOSearch, sbo_detail

urlpatterns = [
    url(r"^home/$", SBOHome.as_view(), name="sbo_home"),
    url(r"^search/$", SBOSearch.as_view(), name="sbo_search"),
    url(r"^sbo_detail/(?P<sbo_id>\d+)/$", sbo_detail, name="sbo_detail"),
    url(r"^home/(?P<year>\d+)/$", SBOHome.as_view(), name="annual_sbo_report"),
]
