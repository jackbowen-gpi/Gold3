AI Setup Summary and Conversation Log

Summary
-------
This repository was prepared for local development with SQLite and Django 4.2. Key actions performed by the AI assistant:

- Created/updated `requirements.txt` by freezing the active virtualenv.
- Updated `local_settings.py` to use SQLite and temporarily used a `urls_dummy` during migrations. Restored `ROOT_URLCONF` after fixtures dumped.
- Applied multiple code compatibility fixes (gettext migrations, AppConfig.name adjustments, URL compatibility shims, fedex fallbacks, and a fix in `includes/model_fields.py`).
- Ran `python -m django migrate` successfully to create the local database at `db.sqlite3`.
- Created a development superuser (username: `devadmin`, password: `devadminpass`) and dumped minimal fixtures to `fixtures_dev.json`.

Files created/edited (high level)
- `requirements.txt` (frozen from virtualenv)
- `local_settings.py` (SQLite + ROOT_URLCONF changes)
- `includes/model_fields.py` (bug fix)
- `urls_dummy.py` (temporary minimal URLconf)
- `fixtures_dev.json` (contains auth.user and sites.site entries)
- `AiReadme.md` (this file)

Fixtures
--------
- `fixtures_dev.json` contains a superuser `devadmin` and a `sites.site` entry.

How to run locally
------------------
(Use PowerShell on Windows)

Set the Python path and activate venv in PowerShell:

```powershell
& C:/Dev/Gold/gchub_db/.venv/Scripts/Activate.ps1
$env:PYTHONPATH='C:/Dev/Gold'
```

Apply migrations (already applied, but safe to run):

```powershell
python -m django migrate --settings=gchub_db.settings
```

Create or reset the superuser if you want a different password:

```powershell
python manage.py createsuperuser --settings=gchub_db.settings
```

Load fixtures (if needed):

```powershell
python manage.py loaddata fixtures_dev.json --settings=gchub_db.settings
```

Start dev server:

```powershell
python manage.py runserver --settings=gchub_db.settings
```

Conversation snapshot
---------------------
The assistant iteratively upgraded and debugged the project to run locally. Key steps included:
- Migrated code from older Django idioms (ugettext -> gettext, url -> re_path) and fixed AppConfig names.
- Temporarily used a dummy URL conf to allow migrations while addressing import-time failures.
- Installed extra Python packages into a virtualenv and froze them to `requirements.txt`.
- Fixed an exception in `includes/model_fields.py` so migrations could proceed.
- Created a dev superuser and exported it to `fixtures_dev.json`.

For full detailed transcript and exact commands executed, please review your terminal history or ask the assistant to append the complete conversation log (note: for privacy/security, secrets were never captured).


End of AI summary.



(.venv) PS C:\Dev\Gold\gchub_db> python manage.py test gchub_db.apps.workflow.tests.test_job_model_comprehensive gchub_db.apps.workflow.tests.test_job_model_integration -v 2
Found 52 test(s).
Creating test database for alias 'default' ('test_gchub_dev')...
Operations to perform:
  Synchronize unmigrated apps: admindocs, django_extensions, formtools, humanize, legacy_support, maintenance_mode, messages, staticfiles
  Apply all migrations: accounts, address, admin, admin_log, archives, art_req, auth, auto_corrugated, auto_ftp, bev_billing, budget, calendar, carton_billing, color_mgt, contenttypes, draw_down, error_tracking, fedexsys, item_catalog, joblog, news, qad_data, qc, queues, sbo, sessions, sites, software, timesheet, workflow
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying accounts.0001_initial... OK
  Applying accounts.0002_userprofile_total_sick... OK
  Applying accounts.0003_userprofile_machine_name... OK
  Applying accounts.0004_auto_20190118_1333... OK
  Applying accounts.0005_auto_20190425_1344... OK
  Applying accounts.0006_auto_20190923_1111... OK
  Applying accounts.0007_auto_20200217_1052... OK
  Applying accounts.0008_userprofile_growl_hear_new_carton_jobs... OK
  Applying accounts.0009_auto_20200921_1359... OK
  Applying accounts.0010_auto_20201015_1352... OK
  Applying accounts.0011_auto_20201023_0815... OK
  Applying accounts.0012_auto_20210121_0915... OK
  Applying accounts.0013_alter_userprofile_id... OK
  Applying accounts.0014_userprofile_use_legacy_search... OK
  Applying accounts.0015_userprofile_item_search_brand_and_more... OK
  Applying address.0001_initial... OK
  Applying address.0002_auto_20190923_1111... OK
  Applying address.0003_alter_contact_id... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying admin_log.0001_initial... OK
  Applying admin_log.0002_auto_20190923_1111... OK
  Applying admin_log.0003_alter_adminlog_id... OK
  Applying archives.0001_initial... OK
  Applying archives.0002_auto_20190923_1111... OK
  Applying archives.0003_alter_kentonarchive_id_alter_renmarkarchive_id... OK
  Applying sites.0001_initial... OK
  Applying sites.0002_alter_domain_unique... OK
  Applying qad_data.0001_initial... OK
  Applying item_catalog.0001_initial... OK
  Applying color_mgt.0001_initial... OK
  Applying bev_billing.0001_initial... OK
  Applying workflow.0001_initial... OK
  Applying art_req.0001_initial... OK
  Applying art_req.0002_product_case_pack... OK
  Applying art_req.0003_auto_20180302_1702... OK
  Applying art_req.0004_auto_20190522_1053... OK
  Applying art_req.0005_partialartreq_is_completed... OK
  Applying art_req.0005_auto_20190923_1111... OK
  Applying art_req.0006_merge_20191002_1022... OK
  Applying art_req.0007_product_render... OK
  Applying art_req.0008_alter_additionalinfo_id_alter_artreq_id_and_more... OK
  Applying art_req.0009_alter_product_ship_to_state... OK
  Applying art_req.0010_alter_product_ship_to_state... OK
  Applying art_req.0011_alter_product_ship_to_state... OK
  Applying art_req.0012_alter_product_ship_to_state... OK
  Applying art_req.0013_alter_product_ship_to_state... OK
  Applying art_req.0014_alter_product_ship_to_state... OK
  Applying art_req.0015_alter_product_ship_to_state... OK
  Applying art_req.0016_alter_product_ship_to_state... OK
  Applying art_req.0017_alter_product_ship_to_state... OK
  Applying art_req.0018_alter_product_ship_to_state... OK
  Applying art_req.0019_alter_product_ship_to_state... OK
  Applying art_req.0020_alter_product_ship_to_state... OK
  Applying art_req.0021_alter_product_ship_to_state... OK
  Applying art_req.0022_alter_product_ship_to_state... OK
  Applying art_req.0023_alter_product_ship_to_state... OK
  Applying art_req.0024_alter_product_ship_to_state... OK
  Applying art_req.0025_alter_product_ship_to_state... OK
  Applying art_req.0026_alter_product_ship_to_state... OK
  Applying art_req.0027_alter_product_ship_to_state... OK
  Applying art_req.0028_alter_product_ship_to_state... OK
  Applying art_req.0029_alter_product_ship_to_state... OK
  Applying art_req.0030_alter_product_ship_to_state... OK
  Applying art_req.0031_auto_fix_art_req... OK
  Applying art_req.0032_alter_product_ship_to_state... OK
  Applying art_req.0033_alter_product_ship_to_state... OK
  Applying art_req.0034_alter_product_ship_to_state... OK
  Applying art_req.0035_alter_product_ship_to_state... OK
  Applying art_req.0036_stabilize_ship_to_state... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying auto_corrugated.0001_initial... OK
  Applying auto_corrugated.0002_auto_20180302_1702... OK
  Applying auto_corrugated.0003_generatedbox_plate_number... OK
  Applying auto_corrugated.0004_auto_20190923_1111... OK
  Applying auto_corrugated.0005_alter_boxitem_id_alter_boxitemspec_id_and_more... OK
  Applying auto_ftp.0001_initial... OK
  Applying auto_ftp.0002_auto_20180302_1702... OK
  Applying auto_ftp.0003_auto_20191121_0934... OK
  Applying auto_ftp.0004_auto_20200208_1021... OK
  Applying auto_ftp.0005_alter_autoftptiff_id... OK
  Applying bev_billing.0002_auto_20180302_1702... OK
  Applying bev_billing.0003_auto_20190923_1111... OK
  Applying bev_billing.0004_alter_bevinvoice_id... OK
  Applying budget.0001_initial... OK
  Applying budget.0002_alter_budget_id_alter_invoiceamt_id... OK
  Applying calendar.0001_initial... OK
  Applying calendar.0002_auto_20190923_1111... OK
  Applying calendar.0003_alter_event_id... OK
  Applying workflow.0002_auto_20180525_1135... OK
  Applying workflow.0003_auto_20180601_1533... OK
  Applying workflow.0004_itemcatalog_product_board... OK
  Applying workflow.0005_auto_20181024_1548... OK
  Applying workflow.0006_auto_20190104_1658... OK
  Applying workflow.0007_auto_20190208_1410... OK
  Applying workflow.0008_itemcatalog_comments... OK
  Applying workflow.0009_job_type... OK
  Applying workflow.0010_jobcomplexity... OK
  Applying workflow.0011_auto_20190625_1125... OK
  Applying workflow.0012_auto_20191107_1639... OK
  Applying workflow.0013_auto_20200208_1021... OK
  Applying workflow.0014_prooftracker... OK
  Applying workflow.0015_prooftracker_xml_filename... OK
  Applying workflow.0016_prooftracker_proofer... OK
  Applying workflow.0017_auto_20200528_1726... OK
  Applying workflow.0018_auto_20200618_1408... OK
  Applying workflow.0019_auto_20200629_1026... OK
  Applying workflow.0020_auto_20200818_1326... OK
  Applying workflow.0021_auto_20200825_1008... OK
  Applying workflow.0022_auto_20201021_1348... OK
  Applying workflow.0023_job_graphic_specialist... OK
  Applying workflow.0024_auto_20210121_0915... OK
  Applying workflow.0025_auto_20210126_1331... OK
  Applying workflow.0026_item_kd_press... OK
  Applying workflow.0027_colorwarning_notes... OK
  Applying carton_billing.0001_initial... OK
  Applying carton_billing.0002_alter_cartonsapentry_id... OK
  Applying color_mgt.0002_auto_20190923_1111... OK
  Applying color_mgt.0003_colordefinition_pantone_plus... OK
  Applying color_mgt.0004_alter_colordefinition_id... OK
  Applying draw_down.0001_initial... OK
  Applying draw_down.0002_auto_20180302_1702... OK
  Applying draw_down.0003_auto_20180905_1430... OK
  Applying draw_down.0004_auto_20180907_1601... OK
  Applying draw_down.0005_auto_20190923_1111... OK
  Applying draw_down.0006_alter_drawdown_id_alter_drawdownitem_id_and_more... OK
  Applying error_tracking.0001_initial... OK
  Applying error_tracking.0002_auto_20180302_1702... OK
  Applying error_tracking.0003_auto_20190923_1111... OK
  Applying error_tracking.0004_alter_error_id... OK
  Applying fedexsys.0001_initial... OK
  Applying fedexsys.0002_shipment_job... OK
  Applying fedexsys.0003_auto_20190923_1111... OK
  Applying fedexsys.0004_alter_shipment_id... OK
  Applying item_catalog.0002_auto_20190923_1111... OK
  Applying item_catalog.0003_alter_productsubcategory_id... OK
  Applying joblog.0001_initial... OK
  Applying joblog.0002_auto_20180302_1702... OK
  Applying joblog.0003_auto_20190923_1111... OK
  Applying joblog.0004_auto_20220518_0917... OK
  Applying joblog.0005_auto_20220531_1104... OK
  Applying joblog.0006_alter_joblog_id... OK
  Applying news.0001_initial... OK
  Applying news.0002_auto_20190923_1111... OK
  Applying news.0003_alter_codechange_id... OK
  Applying news.0004_alter_codechange_creation_date... OK
  Applying qad_data.0002_qad_casepacks_size... OK
  Applying qad_data.0003_qad_casepacks_active... OK
  Applying qad_data.0004_alter_qad_casepacks_id_alter_qad_printgroups_id... OK
  Applying qc.0001_initial... OK
  Applying qc.0002_auto_20180302_1702... OK
  Applying qc.0003_auto_20190923_1111... OK
  Applying qc.0004_alter_qccategory_id_alter_qcquestiondefinition_id_and_more... OK
  Applying queues.0001_initial... OK
  Applying queues.0002_auto_20180302_1702... OK
  Applying queues.0003_auto_20190923_1111... OK
  Applying queues.0004_alter_colorkeyqueue_id_alter_tifftopdf_id... OK
  Applying sbo.0001_initial... OK
  Applying sbo.0002_auto_20190923_1111... OK
  Applying sbo.0003_alter_sbo_id... OK
  Applying sessions.0001_initial... OK
  Applying software.0001_initial... OK
  Applying software.0002_alter_software_id... OK
  Applying timesheet.0001_initial... OK
  Applying timesheet.0002_alter_timesheet_id_alter_timesheetcategory_id... OK
  Applying workflow.0028_job_carton_type... OK
  Applying workflow.0029_auto_20220119_1012... OK
  Applying workflow.0030_auto_20220119_1342... OK
  Applying workflow.0031_substrate... OK
  Applying workflow.0032_item_substrate... OK
  Applying workflow.0033_item_gcr... OK
  Applying workflow.0034_auto_20220215_0905... OK
  Applying workflow.0035_auto_20220215_1042... OK
  Applying workflow.0036_auto_20220217_1042... OK
  Applying workflow.0037_auto_20220329_0929... OK
  Applying workflow.0038_auto_20220524_1050... OK
  Applying workflow.0039_item_proof_type_notes... OK
  Applying workflow.0040_auto_20220714_1112... OK
  Applying workflow.0041_auto_20220803_1325... OK
  Applying workflow.0042_item_ecg... OK
  Applying workflow.0043_job_duplication_type... OK
  Applying workflow.0044_item_render... OK
  Applying workflow.0045_auto_20250223_2048... OK
  Applying workflow.0046_merge_0045_auto_20240611_1949_0045_auto_20250223_2048... OK
  Applying workflow.0047_alter_beveragebrandcode_id_and_more... OK
System check identified no issues (0 silenced).
test_all_items_complete_false (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_all_items_complete_false)
Test all_items_complete when some items don't have final files. ... ok
test_all_items_complete_no_items (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_all_items_complete_no_items)
Test all_items_complete when there are no items. ... ok
test_all_items_complete_true (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_all_items_complete_true)
Test all_items_complete when all items have final files. ... ok
test_created_timestamp (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_created_timestamp)
Test that created timestamp is set properly. ... ok
test_date_properties (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_date_properties)
Test date-related properties. ... ok
test_due_date_calculation_food_site (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_due_date_calculation_food_site)
Test due date calculation for food sites (moves Friday to previous day). ... ok
test_due_date_calculation_regular_site (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_due_date_calculation_regular_site)
Test due date calculation for non-food sites. ... ok
test_icon_url_beverage (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_icon_url_beverage)
Test icon URL for beverage jobs. ... ok
test_icon_url_carton (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_icon_url_carton)
Test icon URL for carton jobs. ... ok
test_icon_url_default (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_icon_url_default)
Test default icon URL for other job types. ... ok
test_job_creation_basic (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_creation_basic)
Test basic job creation and string representation. ... ok
test_job_creation_with_joblog (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_creation_with_joblog)
Test that creating a job creates a corresponding job log entry. ... ok
test_job_deletion_soft_delete (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_deletion_soft_delete)
Test that job deletion is soft delete (marks is_deleted=True). ... ok
test_job_fields_validation (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_fields_validation)
Test field validation and constraints. ... ok
test_job_manager_methods (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_manager_methods)
Test custom manager methods if they exist. ... ok
test_job_ordering (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_ordering)
Test default ordering of jobs. ... ok
test_job_repr_and_str (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_repr_and_str)
Test string representations of job objects. ... ok
test_job_search_functionality (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_search_functionality)
Test job search and filtering capabilities. ... ok
test_job_unique_constraints (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_job_unique_constraints)
Test any unique constraints on the job model. ... ok
test_keyword_generation (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_keyword_generation)
Test automatic keyword generation on save. ... ok
test_last_modified_tracking (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_last_modified_tracking)
Test that last_modified_by is set when job is updated. ... ok
test_status_update_no_change (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_status_update_no_change)
Test status update when items are not complete. ... ok
test_status_update_to_complete (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_status_update_to_complete)
Test automatic status update when all items are complete. ... ok
test_todo_list_html_generation (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_todo_list_html_generation)
Test todo list HTML generation. ... ok
test_workflow_site_relationship (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelComprehensiveTests.test_workflow_site_relationship)
Test the relationship between job and workflow site. ... ok
test_job_with_empty_name (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelEdgeCaseTests.test_job_with_empty_name)
Test job creation with empty or None name. ... ok
test_job_with_invalid_dates (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelEdgeCaseTests.test_job_with_invalid_dates)
Test job with invalid date values. ... ok
test_job_with_various_field_values (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelEdgeCaseTests.test_job_with_various_field_values)
Test job with various field combinations. ... ok
test_job_with_very_long_name (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelEdgeCaseTests.test_job_with_very_long_name)
Test job creation with very long name. ... ok
test_job_without_workflow (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelEdgeCaseTests.test_job_without_workflow)
Test job creation without workflow (should fail). ... ok
test_bulk_job_creation (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelPerformanceTests.test_bulk_job_creation)
Test creating multiple jobs efficiently. ... ok
test_job_filtering_performance (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelPerformanceTests.test_job_filtering_performance)
Test performance of common job filtering operations. ... ok
test_job_queryset_efficiency (gchub_db.apps.workflow.tests.test_job_model_comprehensive.JobModelPerformanceTests.test_job_queryset_efficiency)
Test that job queries are efficient. ... ok
test_concurrent_job_updates (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelConcurrencyTests.test_concurrent_job_updates)
Test handling of concurrent job updates. ... ok
test_job_creation_uniqueness (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelConcurrencyTests.test_job_creation_uniqueness)
Test job creation uniqueness handling. ... ok
test_job_deletion_concurrent_access (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelConcurrencyTests.test_job_deletion_concurrent_access)
Test concurrent access during job deletion. ... ! Error removing symlink.
! Error removing symlink.
ERROR
test_job_bulk_operations_integrity (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_bulk_operations_integrity)
Test that bulk operations maintain data integrity. ... ok
test_job_completion_status_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_completion_status_integration)
Test job completion status with mock items. ... FAIL
test_job_creation_date_ordering_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_creation_date_ordering_integration)
Test job ordering by creation date. ... ok
test_job_creation_with_joblog_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_creation_with_joblog_integration)
Test that job creation properly integrates with job logging. ... ok
test_job_date_calculations_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_date_calculations_integration)
Test date calculations in different site contexts. ... FAIL
test_job_deletion_cascade_behavior (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_deletion_cascade_behavior)
Test job deletion and its effects on related objects. ... FAIL
test_job_icon_url_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_icon_url_integration)
Test icon URL generation for different site types. ... FAIL
test_job_keyword_generation_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_keyword_generation_integration)
Test keyword generation with realistic job data. ... FAIL
test_job_search_and_filtering_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_search_and_filtering_integration)
Test job search functionality with realistic data. ... ok
test_job_status_calculations_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_status_calculations_integration)
Test status-related calculations and validations. ... ok
test_job_status_workflow_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_status_workflow_integration)
Test job status changes and their effects on workflow. ... ok
test_job_user_relationship_tracking (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_user_relationship_tracking)
Test job relationships with users (created_by, modified_by). ... ok
test_job_workflow_site_relationship_integrity (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_workflow_site_relationship_integrity)
Test the integrity of job-site relationships. ... ok
test_job_bulk_operation_transaction (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelTransactionTests.test_job_bulk_operation_transaction)
Test bulk operations within transactions. ... ok
test_job_creation_rollback_scenario (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelTransactionTests.test_job_creation_rollback_scenario)
Test job creation rollback behavior. ... ok
test_job_creation_transaction_integrity (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelTransactionTests.test_job_creation_transaction_integrity)
Test job creation in transaction scenarios. ... ok

======================================================================
ERROR: test_job_deletion_concurrent_access (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelConcurrencyTests.test_job_deletion_concurrent_access)
Test concurrent access during job deletion.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\Gold\gchub_db\gchub_db\apps\workflow\tests\test_job_model_integration.py", line 433, in test_job_deletion_concurrent_access
    final_job = Job.objects.get(id=job_id)
  File "C:\Dev\Gold\gchub_db\.venv\Lib\site-packages\django\db\models\manager.py", line 87, in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "C:\Dev\Gold\gchub_db\.venv\Lib\site-packages\django\db\models\query.py", line 633, in get
    raise self.model.DoesNotExist(
        "%s matching query does not exist." % self.model._meta.object_name
    )
gchub_db.apps.workflow.models.job.Job.DoesNotExist: Job matching query does not exist.

======================================================================
FAIL: test_job_completion_status_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_completion_status_integration)
Test job completion status with mock items.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\Gold\gchub_db\gchub_db\apps\workflow\tests\test_job_model_integration.py", line 299, in test_job_completion_status_integration
    self.assertFalse(job.all_items_complete())
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: True is not false

======================================================================
FAIL: test_job_date_calculations_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_date_calculations_integration)
Test date calculations in different site contexts.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\Gold\gchub_db\gchub_db\apps\workflow\tests\test_job_model_integration.py", line 204, in test_job_date_calculations_integration
    self.assertEqual(food_job.real_due_date, expected_date)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: datetime.date(2025, 8, 29) != datetime.date(2025, 8, 28)

======================================================================
FAIL: test_job_deletion_cascade_behavior (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_deletion_cascade_behavior)
Test job deletion and its effects on related objects.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\Gold\gchub_db\gchub_db\apps\workflow\tests\test_job_model_integration.py", line 151, in test_job_deletion_cascade_behavior
    self.assertTrue(Job.objects.filter(id=job_id).exists())
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true

======================================================================
FAIL: test_job_icon_url_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_icon_url_integration)
Test icon URL generation for different site types.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\Gold\gchub_db\gchub_db\apps\workflow\tests\test_job_model_integration.py", line 289, in test_job_icon_url_integration
    self.assertIn(expected_icon, icon_url)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'bullet_green.png' not found in '/media/img/icons/page_black.png'

======================================================================
FAIL: test_job_keyword_generation_integration (gchub_db.apps.workflow.tests.test_job_model_integration.JobModelIntegrationTests.test_job_keyword_generation_integration)
Test keyword generation with realistic job data.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\Gold\gchub_db\gchub_db\apps\workflow\tests\test_job_model_integration.py", line 273, in test_job_keyword_generation_integration
    self.assertIn(term, keywords_lower)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'techcorp' not found in 'website redesign project 83'

----------------------------------------------------------------------
Ran 52 tests in 22.791s

FAILED (failures=5, errors=1)
Destroying test database for alias 'default' ('test_gchub_dev')...
