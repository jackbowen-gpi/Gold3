from django.urls import re_path as url

from gchub_db.apps.art_req.views import (
    address_autocomplete,
    art_req_add,
    art_req_delete,
    art_req_home,
    art_req_process,
    art_req_review,
    casepack_lookup,
    mktseg_lookup,
)

urlpatterns = [
    url(r"^delete/(?P<temp_id>\d+)/$", art_req_delete, name="art_req_delete"),
    url(r"^home/$", art_req_home, name="art_req_home"),
    url(r"^add/$", art_req_add, name="art_req_add"),
    # includes success message at the top.
    url(r"^add/(?P<new_artreq_id>\d+)/$", art_req_add, name="art_req_add"),
    url(r"^edit/(?P<artreq_id>\d+)/$", art_req_add, name="art_req_edit"),
    # Hides submit button
    url(r"^review/(?P<artreq_id>\d+)/$", art_req_review, name="art_req_review"),
    # Includes submit button
    url(
        r"^review/(?P<artreq_id>\d+)/(?P<temp_id>\w+)/(?P<submit>\D+)/$",
        art_req_review,
        name="art_req_review",
    ),
    url(
        r"^process/(?P<artreq_id>\d+)/(?P<temp_id>\w+)/$",
        art_req_process,
        name="art_req_process",
    ),
    # Process a market segment lookup.
    url(r"^add/mktseg/(?P<seg_id>\d+)/$", mktseg_lookup, name="mktseg_lookup"),
    # Process a casepack lookup
    url(r"^add/casepack/(?P<size_id>\d+)/$", casepack_lookup, name="casepack_lookup"),
    # Process an address auto-complete lookup
    url(r"^add/autocomplete/$", address_autocomplete, name="address_autocomplete"),
]
