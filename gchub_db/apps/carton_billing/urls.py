from django.urls import re_path as url

from gchub_db.apps.carton_billing.views import SapEntryQueue, complete_sap_entry

urlpatterns = [
    url(r"^sap_entry/queue/$", SapEntryQueue.as_view(), name="sap_entry_queue"),
    url(
        r"^sap_entry/complete/(?P<entry_id>\d+)/$",
        complete_sap_entry,
        name="complete_sap_entry",
    ),
]
