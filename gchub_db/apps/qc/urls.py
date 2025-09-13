from django.urls import re_path as url

from gchub_db.apps.qc.views.job import (
    ajax_create_qc,
    ajax_create_qc2,
    qc_manager,
    select_and_create,
)
from gchub_db.apps.qc.views.qc import (
    ajax_set_response_type,
    ajax_whoops_delete,
    ajax_whoops_get_div,
    ajax_whoops_report,
    create_review_and_redirect,
    create_review_and_redirect2,
    edit_qc,
    edit_qc2,
    finish_qc,
    view_qc,
)

urlpatterns = [
    url(
        r"^doc/(?P<qcdoc_id>\d+)/create_review/$",
        create_review_and_redirect,
        name="qc_create_review_and_redirect",
    ),
    url(r"^doc/(?P<qcdoc_id>\d+)/edit/$", edit_qc, name="qc_edit_qc"),
    url(r"^doc/(?P<qcdoc_id>\d+)/view/$", view_qc, name="qc_view_qc"),
    url(r"^doc/(?P<qcdoc_id>\d+)/finish/$", finish_qc, name="qc_finish_qc"),
    url(
        r"^response/(?P<qcresponse_id>\d+)/ajax/set_response_type/$",
        ajax_set_response_type,
        name="qc_ajax_set_response_type",
    ),
    url(
        r"^response/(?P<qcresponse_id>\d+)/ajax/whoops/get_div/$",
        ajax_whoops_get_div,
        name="qc_ajax_whoops_get_div",
    ),
    url(
        r"^whoops/(?P<qcresponse_id>\d+)/ajax/whoops/report/$",
        ajax_whoops_report,
        name="qc_ajax_whoops_report",
    ),
    url(
        r"^whoops/(?P<qcwhoops_id>\d+)/ajax/delete/$",
        ajax_whoops_delete,
        name="qc_ajax_whoops_delete",
    ),
    url(
        r"^doc/(?P<qcdoc_id>\d+)/create_review2/$",
        create_review_and_redirect2,
        name="qc_create_review_and_redirect2",
    ),
    url(r"^doc/(?P<qcdoc_id>\d+)/edit2/$", edit_qc2, name="qc_edit_qc2"),
]

urlpatterns += [
    url(r"^manager/job/(?P<job_id>\d+)/$", qc_manager, name="qc_manager"),
    url(
        r"^manager/job/(?P<job_id>\d+)/select_and_create/$",
        select_and_create,
        name="qc_select_and_create",
    ),
    url(
        r"^manager/job/(?P<job_id>\d+)/ajax/create_qc/$",
        ajax_create_qc,
        name="qc_ajax_create_qc",
    ),
    url(
        r"^manager/job/(?P<job_id>\d+)/ajax/create_qc2/$",
        ajax_create_qc2,
        name="qc_ajax_create_qc2",
    ),
]
