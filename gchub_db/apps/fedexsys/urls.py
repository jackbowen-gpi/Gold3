from django.urls import re_path as url

from gchub_db.apps.fedexsys.views import (
    ListShipments,
    delete_ship_request,
    ship_request,
    track_shipment,
)

urlpatterns = [
    # Request a Shipment/Label
    url(
        r"^request/jobaddress/(?P<jobaddress_id>\d+)/(?P<delivery>\D+)/",
        ship_request,
        name="shipment_request_jobaddress",
    ),
    # Ship to an address, but not regarding any particular job.
    url(
        r"^request/contact/(?P<contact_id>\d+)/(?P<delivery>\D+)/",
        ship_request,
        name="shipment_request_contact",
    ),
    # Track a Shipment
    # GET Keys: tracking_num
    url(r"^track/(?P<tracking_num>\d+)/", track_shipment, name="shipment_track"),
    # Delete a Shipment
    url(r"^delete/(?P<tracking_num>\d+)/", delete_ship_request, name="shipment_delete"),
    # List current shipments
    url(r"^$", ListShipments.as_view(), name="shipment_list"),
]
