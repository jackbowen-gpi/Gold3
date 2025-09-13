"""
The urls.py file handles URL dispatching for the workflow module. Requests
that begin with /workflow are sent here. The major models get their own
URL matching sections below, which are combined into urlpatterns at the end
of the file for matching.
"""

from django.urls import re_path as url
from django.views.generic import TemplateView

from gchub_db.apps.workflow.views.itemcatalog_views import (
    BrowseItemCatalog,
    BrowseItemSpecs,
)
from gchub_db.apps.workflow.views.job_views import JobFindPrintgroup, JobFindRelated
from gchub_db.apps.workflow.views.platemaking_views import (
    Platemaking,
    PlatemakingCompleted,
    PlateReorderList,
)
from gchub_db.apps.workflow.views.search_views import (
    FedexShipments,
    GetReport,
    InkCovReport,
    ItemFindSame,
    JobSearchResultsView,
    job_todo_list,
    MktReviewReport,
)

"""
color-warning views
"""
from gchub_db.apps.workflow.views.color_warning_views import (
    add_warning,
    color_warning,
    edit_warning,
    view_warning,
)

urlpatterns = [
    url(
        r"^$",
        TemplateView.as_view(template_name="workflow/index.html"),
        name="workflow_index",
    ),
    url(r"^color_warning/add_warning/$", add_warning, name="add_warning"),
    url(
        r"^color_warning/edit_warning/(?P<warning_id>\d+)$",
        edit_warning,
        name="edit_warning",
    ),
    url(
        r"^color_warning/view_warning/(?P<warning_id>\d+)$",
        view_warning,
        name="view_warning",
    ),
    url(r"^color_warning/color_warning/$", color_warning, name="color_warning"),
]

"""
Job-related views
"""
from gchub_db.apps.workflow.views.job_views import (
    add_item,
    add_job_address,
    ajax_job_save,
    attach_address_to_job,
    bev_item_nomenclature,
    carton_invoice,
    cartonprofile_lookup,
    change_job_csr,
    change_job_name,
    change_platepackage,
    change_printlocation,
    copy_jobaddress_to_contacts,
    create_job_creative_shortcut,
    cycle_job_todo_list_mode,
    db_doc_upload,
    delete_job_address,
    duplicate_job,
    edit_all_billing,
    edit_all_timeline,
    edit_all_timeline_pageload,
    edit_job_address,
    etools_show_request,
    extended_job_edit,
    get_database_document,
    get_zipfile_proof,
    gps_connect_cust_info,
    gps_connect_cust_info_json,
    item_duplicate_list,
    item_summary,
    item_tracker_art,
    item_tracker_mkt,
    item_tracker_promo,
    job_detail,
    job_detail_main,
    job_item_json,
    job_specsheet_data,
    misc_info,
    new_beverage_item,
    new_beverage_job,
    new_carton_item,
    new_carton_job,
    new_container_item,
    new_container_job,
    remove_from_archive,
    reset_permissions,
    shipping_manager,
    sync_folders,
    timesheets,
)

urlpatterns += [
    url(r"^job/(?P<job_id>\d+)/$", job_detail, name="job_detail"),
    url(
        r"^job/cycle_job_todo_list_mode/(?P<job_id>\d+)/$",
        cycle_job_todo_list_mode,
        name="job_cycle_job_todo_list_mode",
    ),
    url(r"^job/(?P<job_id>\d+)/main/$", job_detail_main),
    url(r"^job/new/beverage/$", new_beverage_job, name="new_beverage_job"),
    url(
        r"^job/new/beverage/(?P<job_id>\d+)/item/(?P<type>\D+)/$",
        new_beverage_item,
        name="new_beverage_item",
    ),
    url(
        r"^job/new/beverage/(?P<job_id>\d+)/item/(?P<type>\D+)/(?P<item_id>\d+)/$",
        new_beverage_item,
        name="dupe_beverage_item",
    ),
    url(r"^job/new/carton/$", new_carton_job, name="new_carton_job"),
    url(
        r"^job/new/carton/(?P<job_id>\d+)/item/(?P<type>\D+)/$",
        new_carton_item,
        name="new_carton_item",
    ),
    url(r"^job/new/container/$", new_container_job, name="new_container_job"),
    url(
        r"^job/new/container/(?P<job_id>\d+)/item/$",
        new_container_item,
        name="new_container_item",
    ),
    url(r"^job/(?P<job_id>\d+)/misc_info/$", misc_info, name="misc_info"),
    url(
        r"^job/(?P<job_id>\d+)/creative_shortcut/$",
        create_job_creative_shortcut,
        name="create_job_creative_shortcut",
    ),
    url(r"^job/(?P<job_id>\d+)/sync_folders/$", sync_folders, name="sync_folders"),
    url(
        r"^job/(?P<job_id>\d+)/extended_job_edit/$",
        extended_job_edit,
        name="extended_job_edit",
    ),
    url(r"^job/(?P<job_id>\d+)/carton_invoice/$", carton_invoice, name="carton_invoice"),
    url(
        r"^job/(?P<job_id>\d+)/find_related/$",
        JobFindRelated.as_view(),
        name="job_find_related",
    ),
    url(
        r"^job/(?P<job_id>\d+)/find_printgroup/$",
        JobFindPrintgroup.as_view(),
        name="job_find_printgroup",
    ),
    url(r"^job/(?P<job_id>\d+)/(?P<view>\D+)/summary/$", item_summary),
    url(r"^job/(?P<job_id>\d+)/job_item_json/(?P<null_char>\D+)$", job_item_json),
    url(
        r"^job/(?P<job_id>\d+)/shipping_manager/$",
        shipping_manager,
        name="shipping_manager",
    ),
    url(r"^job/(?P<job_id>\d+)/db_doc_upload/$", db_doc_upload, name="job_db_doc_upload"),
    url(
        r"^db_doc_upload_complete/$",
        TemplateView.as_view(template_name="workflow/job/job_detail/popups/db_doc_upload_complete.html"),
        name="jb_db_doc_upload_complete",
    ),
    url(
        r"^job/(?P<job_num>\d+)/get_db_doc/(?P<filepath>.+)/$",
        get_database_document,
        name="job_get_db_doc",
    ),
    url(r"^job/(?P<job_id>\d+)/save/$", ajax_job_save),
    url(
        r"^job/(?P<job_id>\d+)/bev_item_nomenclature/$",
        bev_item_nomenclature,
        name="bev_item_nomenclature",
    ),
    url(r"^job/(?P<job_id>\d+)/add_item/$", add_item),
    url(r"^job/(?P<job_id>\d+)/add_jobaddress/$", add_job_address),
    url(r"^job/jobaddress/(?P<address_id>\d+)/edit/$", edit_job_address),
    url(r"^job/jobaddress/(?P<address_id>\d+)/copy/$", copy_jobaddress_to_contacts),
    url(r"^job/jobaddress/(?P<address_id>\d+)/delete/$", delete_job_address),
    url(r"^job/jobaddress/attach/$", attach_address_to_job),
    url(r"^job/(?P<job_id>\d+)/change_name/$", change_job_name),
    url(r"^job/(?P<job_id>\d+)/change_csr/$", change_job_csr),
    url(r"^job/(?P<job_id>\d+)/duplicate_job/(?P<dupe_type>\D+)/$", duplicate_job),
    url(r"^job/(?P<job_id>\d+)/edit_all_timeline/$", edit_all_timeline),
    url(r"^job/(?P<job_id>\d+)/edit_all_timeline/(?P<event>\D+)/$", edit_all_timeline),
    url(
        r"^job/(?P<job_id>\d+)/edit_all_timeline_pageload/(?P<event>\D+)/(?P<action>\D+)/$",
        edit_all_timeline_pageload,
    ),
    url(
        r"^job/(?P<job_id>\d+)/edit_all_billing/$",
        edit_all_billing,
        name="edit_all_billing",
    ),
    url(r"^job/(?P<job_id>\d+)/item_tracker_mkt/$", item_tracker_mkt),
    url(r"^job/(?P<job_id>\d+)/item_tracker_promo/$", item_tracker_promo),
    url(r"^job/(?P<job_id>\d+)/item_tracker_art/$", item_tracker_art),
    url(r"^job/(?P<job_id>\d+)/timesheets/$", timesheets, name="timesheets"),
    url(r"^job/(?P<job_id>\d+)/item_duplicate_list/$", item_duplicate_list),
    url(
        r"^job/(?P<job_id>\d+)/etools/show_request/$",
        etools_show_request,
        name="etools_show_request",
    ),
    url(
        r"^job/(?P<job_id>\d+)/gps_connect/customer_info/$",
        gps_connect_cust_info,
        name="gps_connect_cust_info",
    ),
    url(
        r"^job/gps_connect/customer_info_json/(?P<cust_id>\d+)/$",
        gps_connect_cust_info_json,
        name="gps_connect_cust_info_json",
    ),
    url(
        r"^job/(?P<job_id>\d+)/change_printlocation/$",
        change_printlocation,
        name="change_printlocation",
    ),
    url(
        r"^job/(?P<job_id>\d+)/change_platepackage/$",
        change_platepackage,
        name="change_platepackage",
    ),
    url(
        r"^job/(?P<job_id>\d+)/remove_from_archive/$",
        remove_from_archive,
        name="remove_from_archive",
    ),
    url(
        r"^job/(?P<job_id>\d+)/job_specsheet_data/$",
        job_specsheet_data,
        name="job_specsheet_data",
    ),
    url(
        r"^job/(?P<job_id>\d+)/get_zipfile_proof/$",
        get_zipfile_proof,
        name="get_zipfile_proof",
    ),
    url(r"^job/(?P<job_id>\d+)/reset_permissions/$", reset_permissions),
    url(
        r"^job/cartonprofile/(?P<cartonworkflow_id>\d+)/(?P<linescreen_id>\d+)/(?P<inkset_id>\d+)/(?P<substrate_id>\d+)/(?P<printlocation_id>\d+)/(?P<printcondition_id>\d+)/$",
        cartonprofile_lookup,
    ),
]

"""
Item-related views
"""
from gchub_db.apps.workflow.views.item_views import (
    add_item_charge,
    add_itemcolor,
    ajax_item_save,
    bev_nomenclature_lookup,
    change_itemcolor,
    charge_lookup,
    delete_billing,
    delete_item,
    delete_item_tracker,
    delete_itemcolor,
    delete_revision,
    do_colorkey_queue,
    do_copy_fsb_production_template,
    do_copy_master_template,
    do_copy_misregistration_pdf,
    do_copy_nx_plates,
    do_copy_qad_data,
    do_item_import_qad,
    do_item_make_bev_die,
    do_item_tiff_to_pdf,
    do_make_fsb_art_rectangle,
    edit_bev_brand_code,
    edit_billing,
    enter_revision,
    get_item_approval_scan,
    get_item_finalfile,
    get_item_preview_art,
    get_item_print_seps,
    get_item_proof,
    get_single_tiff,
    get_stepped_item_proof,
    get_zipfile_tiff,
    item_billing_detail,
    item_ink_data,
    item_internal_detail,
    item_jdf_detail,
    item_production_detail,
    item_sap_detail,
    item_thumbnail,
    item_tiff_download_list,
    item_timeline_detail,
    json_get_item_specs,
    tiff_rip,
    transfer_files_to_concord,
    view_bev_brand_code,
)

urlpatterns += [
    url(r"^item/(?P<item_id>\d+)/colorkey/$", do_colorkey_queue),
    url(r"^item/(?P<item_id>\d+)/(?P<save_type>\D+)/save/$", ajax_item_save),
    url(
        r"^item/(?P<item_id>\d+)/edit_bev_brand_code/$",
        edit_bev_brand_code,
        name="edit_bev_brand_code",
    ),
    url(
        r"^item/(?P<item_id>\d+)/(?P<bev_brand_code>\d+)/view/$",
        view_bev_brand_code,
        name="view_bev_brand_code",
    ),
    url(r"^item/(?P<item_id>\d+)/production_detail/$", item_production_detail),
    url(r"^item/(?P<item_id>\d+)/billing_detail/$", item_billing_detail),
    url(r"^item/(?P<item_id>\d+)/internal_detail/$", item_internal_detail),
    url(r"^item/(?P<item_id>\d+)/tiff_rip/$", tiff_rip),
    url(r"^item/(?P<item_id>\d+)/ink_data/$", item_ink_data),
    url(r"^item/(?P<item_id>\d+)/sap_detail/$", item_sap_detail),
    url(r"^item/(?P<item_id>\d+)/add_billing/$", add_item_charge),
    url(r"^item/(?P<item_id>\d+)/delete_item/$", delete_item),
    url(
        r"^item/(?P<item_id>\d+)/item_tracker/delete/(?P<item_tracker_id>\d+)/(?P<comment>\D+)/$",
        delete_item_tracker,
    ),
    url(
        r"^item/(?P<item_id>\d+)/item_tracker/delete/(?P<item_tracker_id>\d+)//$",
        delete_item_tracker,
    ),
    url(r"^json/get_item_specs/", json_get_item_specs, name="item_json_get_item_specs"),
    url(r"^item/(?P<item_id>\d+)/timeline_detail/$", item_timeline_detail),
    url(r"^item/(?P<item_id>\d+)/thumbnail/$", item_thumbnail, name="item_thumbnail"),
    url(
        r"^item/(?P<item_id>\d+)/thumbnail/(?P<width>\d+)/$",
        item_thumbnail,
        name="item_thumbnail_sized",
    ),
    url(
        r"^job/new/beverage/bev_nomenclature_lookup/(?P<size>\d+)/item/(?P<printlocation>\d+)/(?P<platepackage>\d+)/(?P<bev_alt_code>\d+)/(?P<bev_center_code>\d+)/(?P<bev_liquid_code>\d+)/$",
        bev_nomenclature_lookup,
        name="bev_nomenclature_lookup",
    ),
    url(
        r"^item/(?P<item_id>\d+)/enter_revision/$",
        enter_revision,
        name="enter_revision",
    ),
    url(
        r"^item/(?P<item_id>\d+)/edit_revision/(?P<rev_id>\d+)/$",
        enter_revision,
        name="edit_revision",
    ),
    url(
        r"^item/(?P<rev_id>\d+)/delete_revision/$",
        delete_revision,
        name="delete_revision",
    ),
    url(r"^item/(?P<item_id>\d+)/jdf_detail/$", item_jdf_detail),
    #    url(r'^item/(?P<job_num>\d+)/(?P<item_num>\d+)/do_item_make_bev_die_old/$', 'do_item_make_bev_die_old',
    #        name='do_item_make_bev_die_old'),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/do_item_make_bev_die/$",
        do_item_make_bev_die,
        name="do_item_make_bev_die",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/do_item_tiff_to_pdf/$",
        do_item_tiff_to_pdf,
        name="do_item_tiff_to_pdf",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/do_item_make_bev_die/(?P<old_marks>\D+)/$",
        do_item_make_bev_die,
        name="do_item_make_bev_die_old_marks",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/do_item_make_bev_die/(?P<old_marks>\D+)/(?P<force_crosshairs>\d+)/$",
        do_item_make_bev_die,
        name="do_item_make_bev_die_old_marks_force_crosshairs",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_id>\d+)/do_item_import_qad/$",
        do_item_import_qad,
        name="do_item_import_qad",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_id>\d+)/do_copy_qad_data/$",
        do_copy_qad_data,
        name="do_copy_qad_data",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_id>\d+)/do_copy_fsb_production_template/$",
        do_copy_fsb_production_template,
        name="do_copy_fsb_production_template",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_id>\d+)/do_copy_misregistration_pdf/$",
        do_copy_misregistration_pdf,
        name="do_copy_misregistration_pdf",
    ),
    url(
        r"^item/(?P<item_id>\d+)/do_copy_nx_plates/$",
        do_copy_nx_plates,
        name="do_copy_nx_plates",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_id>\d+)/do_copy_master_template/$",
        do_copy_master_template,
        name="do_copy_master_template",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_id>\d+)/do_make_fsb_art_rectangle/$",
        do_make_fsb_art_rectangle,
        name="do_make_fsb_art_rectangle",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/proof/$",
        get_item_proof,
        name="get_item_proof",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/stepped_proof/$",
        get_stepped_item_proof,
        name="get_stepped_item_proof",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/past_proof/(?P<log_id>\d+)/$",
        get_item_proof,
        name="get_item_past_proof",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/finalfile/$",
        get_item_finalfile,
        name="get_item_finalfile",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/preview/$",
        get_item_preview_art,
        name="get_item_preview_art",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/separations/$",
        get_item_print_seps,
        name="get_item_print_seps",
    ),
    url(
        r"^item/(?P<job_num>\d+)/(?P<item_num>\d+)/approval/$",
        get_item_approval_scan,
        name="get_item_approval_scan",
    ),
    url(
        r"^item/(?P<item_id>\d+)/tiff_download/$",
        item_tiff_download_list,
        name="item_tiff_download",
    ),
    url(
        r"^item/(?P<item_id>\d+)/(?P<filename>.+)/get_single_tiff/$",
        get_single_tiff,
        name="get_single_tiff",
    ),
    url(
        r"^item/(?P<item_id>\d+)/get_zipfile_tiff/$",
        get_zipfile_tiff,
        name="get_zipfile_tiff",
    ),
    url(r"^charge/(?P<item_id>\d+)/save/$", add_item_charge),
    url(
        r"^item/change_itemcolor/(?P<color_id>\d+)/$",
        change_itemcolor,
        name="change_itemcolor",
    ),
    url(r"^item/add_itemcolor/(?P<item_id>\d+)/$", add_itemcolor, name="add_itemcolor"),
    url(
        r"^item/delete_itemcolor/(?P<color_id>\d+)/$",
        delete_itemcolor,
        name="delete_itemcolor",
    ),
    url(r"^charge/(?P<charge_id>\d+)/edit/$", edit_billing),
    url(r"^charge/(?P<charge_id>\d+)/delete/$", delete_billing),
    url(
        r"^charge/charge_lookup/(?P<charge_description>\d+)/(?P<item_id>\d+)/(?P<rush_days>\d+)/$",
        charge_lookup,
    ),
    url(r"^item/(?P<item_id>\d+)/transfer_files_to_concord/$", transfer_files_to_concord),
]

"""
Search-related views
"""
from gchub_db.apps.workflow.views.search_views import (
    FSB_InkCovReport,
    ReviewSearchResults,
    bioengineered_excel,
    fsb_inkcov_excel,
    get_fedex_shipment_pdf,
    inkcov_excel,
    item_search,
    items_rejected,
    job_search,
    list_reports,
    makeship_excel,
    mkt_review,
    mkt_review_excel,
    otifne_report,
    pending_jobs,
    process_review,
    review,
)
from gchub_db.apps.workflow.views.autocomplete_views import (
    job_autocomplete,
    item_autocomplete,
)

urlpatterns += [
    url(r"^items_rejected/$", items_rejected, name="items_rejected"),
    url(r"^review/(?P<category>\D+)/$", review, name="review"),
    url(
        r"^review/search_results/$",
        ReviewSearchResults.as_view(),
        name="review_search_results",
    ),
    url(r"^mkt_review/$", mkt_review, name="mkt_review"),
    url(
        r"^mkt_review/(?P<type>\D+)/(?P<tracked_art_type>\d+)/$",
        MktReviewReport.as_view(),
        name="mkt_review_report",
    ),
    url(
        r"^mkt_review_excel/(?P<tracked_art_type>\d+)/$",
        mkt_review_excel,
        name="mkt_review_excel",
    ),
    url(r"^item/search/$", item_search, name="item_search"),
    url(
        r"^item/(?P<item_id>\d+)/review/(?P<category>\D+)/(?P<update_type>\D+)/$",
        process_review,
        name="process_review",
    ),
    url(r"^job/search/$", job_search, name="job_search"),
    url(
        r"^job/search_results/$",
        JobSearchResultsView.as_view(),
        name="job_search_results",
    ),
    # Autocomplete endpoints for enhanced search UI
    url(r"^api/job_autocomplete/$", job_autocomplete, name="job_autocomplete"),
    url(r"^api/item_autocomplete/$", item_autocomplete, name="item_autocomplete"),
    url(r"^todo_list/$", job_todo_list, name="todo_list"),
    url(
        r"^todo_list/manager_tools/$",
        job_todo_list,
        {"manager_tools": True},
        name="todo_list_manager_tools",
    ),
    url(r"^job/pending_jobs/$", pending_jobs, name="pending_jobs"),
    url(r"^reports/list/$", list_reports, name="list_reports"),
    url(r"^reports/get/(?P<report_name>\D+)/$", GetReport.as_view(), name="get_report"),
    url(
        r"^job/(?P<item_id>\d+)/item_find_same/$",
        ItemFindSame.as_view(),
        name="item_find_same",
    ),
    url(r"^reports/otifne/(?P<year>\d+)/$", otifne_report, name="otifne_report"),
    url(
        r"^reports/inkcov/(?P<plant>\D+)/$",
        InkCovReport.as_view(),
        name="inkcov_report",
    ),
    url(r"^reports/fsb_inkcov/$", FSB_InkCovReport.as_view(), name="fsb_inkcov_report"),
    url(r"^reports/fedex_shipments/$", FedexShipments.as_view(), name="fedex_shipments"),
    url(
        r"^reports/fedex_shipments/download/(?P<start_date>[\d\-]+)/(?P<end_date>[\d\-]+)/$",
        get_fedex_shipment_pdf,
        name="get_fedex_shipment_pdf",
    ),
    url(r"^inkcov_excel/(?P<plant>\D+)/$", inkcov_excel, name="inkcov_excel"),
    url(
        r"^fsb_inkcov_excel/(?P<start_date>[\d\-]+)/(?P<end_date>[\d\-]+)/(?P<plant>\D+)/$",
        fsb_inkcov_excel,
        name="fsb_inkcov_excel",
    ),
    url(r"^makeship_excel/$", makeship_excel, name="makeship_excel"),
    url(r"^bioengineered_excel/$", bioengineered_excel, name="bioengineered_excel"),
]

"""
Item catalog related views.
"""
from gchub_db.apps.workflow.views.itemcatalog_views import (
    catalog_search,
    edit_itemcatalog,
    edit_itemspecs,
    edit_stepspecs,
    itemcatalog_home,
    new_itemcatalog,
    new_itemspecs,
    new_itemspecs_dupe,
    new_stepspecs,
    new_stepspecs_dupe,
    spec_search,
    step_search,
)

urlpatterns += [
    url(r"^itemcatalog/$", itemcatalog_home, name="itemcatalog_home"),
    url(r"^itemcatalog/new/$", new_itemcatalog, name="new_itemcatalog"),
    url(r"^itemcatalog/browse/$", BrowseItemCatalog.as_view(), name="browse_itemcatalog"),
    url(r"^itemcatalog/search/$", catalog_search, name="catalog_search"),
    url(r"^itemcatalog/specs/search/$", spec_search, name="spec_search"),
    url(r"^itemcatalog/stepspecs/search/$", step_search, name="step_search"),
    url(
        r"^itemcatalog/edit/(?P<item_id>\d+)/$",
        edit_itemcatalog,
        name="itemcatalog_edit",
    ),
    url(
        r"^itemcatalog/edit/(?P<item_id>\d+)/save/$",
        edit_itemcatalog,
        name="edit_itemcatalog",
    ),
    url(r"^itemcatalog/specs/new/$", new_itemspecs, name="new_itemspecs_basic"),
    url(r"^itemcatalog/stepspecs/new/$", new_stepspecs, name="new_stepspecs_basic"),
    url(
        r"^itemcatalog/specs/dupe/(?P<spec_id>\d+)/$",
        new_itemspecs_dupe,
        name="new_itemspecs_dupe",
    ),
    url(
        r"^itemcatalog/stepspecs/dupe/(?P<stepspec_id>\d+)/$",
        new_stepspecs_dupe,
        name="new_stepspecs_dupe",
    ),
    url(
        r"^itemcatalog/specs/new/(?P<set_size>\d+)/$",
        new_itemspecs,
        name="new_itemspecs_size",
    ),
    url(
        r"^itemcatalog/specs/new/(?P<set_size>\d+)/(?P<set_printlocation>\d+)/$",
        new_itemspecs,
        name="new_itemspecs_full",
    ),
    url(
        r"^itemcatalog/specs/browse/$",
        BrowseItemSpecs.as_view(),
        name="browse_itemspecs",
    ),
    url(
        r"^itemcatalog/specs/edit/(?P<spec_id>\d+)/$",
        edit_itemspecs,
        name="edit_itemspecs",
    ),
    url(
        r"^itemcatalog/stepspecs/edit/(?P<stepspec_id>\d+)/$",
        edit_stepspecs,
        name="edit_stepspecs",
    ),
]

"""
Platemaking views
"""
from gchub_db.apps.workflow.views.platemaking_views import (
    mark_plateorder_invoiced,
    plate_reorder_form,
    plate_reorder_search,
    plate_reorder_submit,
    platemaking_canceled,
    platemaking_handle,
)

urlpatterns += [
    url(
        r"^platemaking/pending/(?P<platemaker>\D+)/$",
        Platemaking.as_view(),
        name="platemaking",
    ),
    url(
        r"^platemaking/completed/(?P<platemaker>\D+)/$",
        PlatemakingCompleted.as_view(),
        name="platemaking_completed",
    ),
    url(
        r"^platemaking/canceled/(?P<order_id>\d+)/$",
        platemaking_canceled,
        name="platemaking_canceled",
    ),
    url(
        r"^platemaking/handle/(?P<order_id>\d+)/(?P<step>\d+)/$",
        platemaking_handle,
        name="platemaking_handle",
    ),
    url(
        r"^platemaking/reorder/search/$",
        plate_reorder_search,
        name="plate_reorder_search",
    ),
    url(
        r"^platemaking/reorder/list/$",
        PlateReorderList.as_view(),
        name="plate_reorder_list",
    ),
    url(
        r"^platemaking/reorder/form/(?P<order_id>\d+)/$",
        plate_reorder_form,
        name="plate_reorder_form",
    ),
    url(
        r"^platemaking/reorder/submit/(?P<item_id>\d+)/$",
        plate_reorder_submit,
        name="plate_reorder_submit",
    ),
    url(
        r"^platemaking/reorder/mark_invoiced/(?P<order_id>\d+)/$",
        mark_plateorder_invoiced,
        name="mark_plateorder_invoiced",
    ),
]


"""
Misc. views
"""
from gchub_db.apps.workflow.views.misc_views import (
    add_centercode,
    add_endcode,
    code_manager,
    code_manager_edit,
    data_trends_cuptype,
    data_trends_main,
    data_trends_quality,
    data_trends_volume,
    gen_doc_upload,
)

urlpatterns += [
    url(
        r"^beverage/centercode/add/(?P<code>\D+)/$",
        add_centercode,
        name="add_centercode",
    ),
    url(r"^beverage/centercode/add/$", add_centercode, name="add_centercode"),
    url(
        r"^beverage/centercode/add/complete/$",
        add_centercode,
        name="add_generic_code_complete",
    ),
    url(
        r"^add_code_complete/$",
        TemplateView.as_view(template_name="workflow/misc/beverage/add_code_complete.html"),
        name="add_code_complete",
    ),
    url(r"^beverage/endcode/add/$", add_endcode, name="add_endcode"),
    url(r"^beverage/code_manager/$", code_manager, name="code_manager"),
    url(
        r"^beverage/code_manager/edit/(?P<code_id>\d+)/$",
        code_manager_edit,
        name="code_manager_edit",
    ),
    url(r"^trends/$", data_trends_main, name="data_trends_main"),
    url(r"^trends/volume/$", data_trends_volume, name="data_trends_volume"),
    url(r"^trends/cuptype/$", data_trends_cuptype, name="data_trends_cuptype"),
    url(r"^trends/quality/$", data_trends_quality, name="data_trends_quality"),
    url(r"^file/gen_doc_upload/$", gen_doc_upload, name="misc_gen_doc_upload"),
    url(
        r"^gen_doc_upload_complete/$",
        TemplateView.as_view(template_name="workflow/misc/popups/gen_doc_upload_complete.html"),
        name="misc_gen_doc_upload_complete",
    ),
]
