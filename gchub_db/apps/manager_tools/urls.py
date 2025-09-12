from django.urls import re_path as url

from gchub_db.apps.manager_tools.views import *

urlpatterns = [
    url(r"^$", home, name="manager_tools-home"),
    url(r"^overview/$", overview, name="manager_tools-overview"),
    url(r"^timesheets/$", timesheets, name="manager_tools-timesheets"),
    url(r"^materials/$", materials, name="manager_tools-materials"),
    url(r"^metrics/$", metrics_form, name="manager_tools-metrics_form"),
    url(
        r"^metrics/excel/(?P<year_from>\d+)/(?P<month_from>\d+)/(?P<day_from>\d+)/to/(?P<year_to>\d+)/(?P<month_to>\d+)/(?P<day_to>\d+)/$",
        metrics_excel,
        name="manager_tools-metrics_excel",
    ),
    url(
        r"^metrics/pdf/(?P<year_from>\d+)/(?P<month_from>\d+)/(?P<day_from>\d+)/to/(?P<year_to>\d+)/(?P<month_to>\d+)/(?P<day_to>\d+)/$",
        metrics_pdf,
        name="manager_tools-metrics_pdf",
    ),
    url(r"^qc/$", qc, name="manager_tools-qc"),
    url(r"^turntime/$", turntime, name="manager_tools-turntime"),
    url(
        r"^turntime/artists/(?P<month>\D+)/(?P<year>\d+)/(?P<workflow>\D+)/$",
        turntimes_by_artist,
        name="manager_tools-turntimes_by_artist",
    ),
    url(
        r"^turntime/items/(?P<month>\d+)/(?P<year>\d+)/(?P<workflow>\D+)/(?P<artist_id>\d+)/$",
        turntimes_by_item,
        name="manager_tools-turntimes_by_item",
    ),
    url(r"^jobcategory_all/$", jobcategory_all, name="manager_tools-jobcategory_all"),
    url(
        r"^jobcategory_artists/(?P<supplied_category>\D+)/(?P<supplied_type>\D+)/$",
        jobcategory_artists,
        name="manager_tools-jobcategory_artists",
    ),
    url(r"^stalecharges/$", stalecharges, name="manager_tools-stalecharges"),
    url(
        r"^stalecharges/excel/(?P<year_from>\d+)/(?P<month_from>\d+)/(?P<day_from>\d+)/to/(?P<year_to>\d+)/(?P<month_to>\d+)/(?P<day_to>\d+)/$",
        stalecharges_excel,
        name="manager_tools-stalecharges_excel",
    ),
    url(r"^monthly_billing/$", monthly_billing, name="manager_tools-monthly_billing"),
    url(r"^costavoidance/$", costavoidance, name="manager_tools-costavoidance"),
    url(r"^vacation/$", vacation, name="manager_tools-vacation"),
    url(r"^sick/$", sick, name="manager_tools-sick"),
    url(r"^artworktracking/$", artworktracking, name="manager_tools-artworktracking"),
    url(
        r"^artworktracking/excel/(?P<month>\d+)/(?P<year>\d+)/(?P<spreadsheetType>\D+)/$",
        artwork_excel,
        name="manager_tools-artwork_excel",
    ),
    url(r"^hoursbyplant/$", hoursbyplant, name="manager_tools-hoursbyplant"),
    url(r"^loading/$", artist_loading, name="manager_tools-artist_loading"),
]
