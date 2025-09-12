from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic.list import ListView

try:
    # Optional external dependency. Provide a local stub if not installed so
    # the project can start for local development without the real package.
    from fedex.base_service import FedexError
    from fedex.services import ship_service, track_service
except Exception:

    class FedexError(Exception):
        pass

    class _StubService:
        class FedexTrackRequest:
            def __init__(self, *args, **kwargs):
                self.response = type("R", (), {})()
                # Minimal shape used by code; empty lists/attrs to avoid
                # attribute errors during template rendering in dev.
                self.response.CompletedTrackDetails = []

            def send_request(self):
                return None

        class FedexDeleteShipmentRequest:
            def __init__(self, *args, **kwargs):
                self.TrackingId = type("T", (), {})()

            def send_request(self):
                return None

    track_service = _StubService
    ship_service = _StubService
from django.template import loader

from gchub_db.apps.address.models import Contact
from gchub_db.apps.fedexsys import countries
from gchub_db.apps.fedexsys.config_factory import create_fedex_config
from gchub_db.apps.fedexsys.models import Shipment
from gchub_db.apps.workflow.models import JobAddress
from gchub_db.includes import general_funcs
from gchub_db.includes.gold_json import JSMessage


class ListShipments(ListView):
    """Shows a list of the last X number of shipments."""

    queryset = Shipment.objects.all().order_by("-date_shipped")
    paginate_by = 30
    template_name = "fedexsys/shipment_list.html"


def track_shipment(request, tracking_num):
    """Gets the shipment's tracking information from Fedex and displays it."""
    tracked_shipment = get_object_or_404(Shipment, tracking_num=tracking_num)

    # Use our config_factory module to get a FedexConfig object.
    fedex_config = create_fedex_config()
    track = track_service.FedexTrackRequest(fedex_config, tracking_num)
    # Set the tracking number to query for.
    track.SelectionDetails.PackageIdentifier.Value = tracking_num

    try:
        # Send off the request.
        track.send_request()
    except FedexError:
        # The shipment data has yet to be received by FedEx. There is
        # often a delay of 10-15 minutes after submitting a shipment
        # before FedEx's API wants to acknowledge its existence.
        # Show an error page and tell them to check back soon.
        pagevars = {"tracking_num": tracking_num}

        return render(request, "fedexsys/not_tracked_yet_error.html", context=pagevars)

    # Just for convenience.
    response = track.response
    # To see the full response, un-comment this line. It is typically useful
    # to do so when trying to figure out which attributes are available
    # for display.
    # print track.response

    if response.CompletedTrackDetails[0].TrackDetails[0].Notification[0] == "ERROR":
        # We've been getting weird responses from FedEx where the
        # HighesSeverity is "SUCCESS" even though there's an error in the
        # TrackDetails. We're assuming this is a bug so in the mean time we're
        # manually double-checking the TrackDetails for errors as well.
        pagevars = {"tracking_num": tracking_num}

        return render(request, "fedexsys/not_tracked_yet_error.html", context=pagevars)
    # This will hold some context variables.
    pagevars = {}

    # Go through the Events[] array from the response, and grab some info
    # about each for display. Do some really rudimentary formatting.
    event_list = []
    for event in response.CompletedTrackDetails[0].TrackDetails[0].Events:
        # These values should be there for all events.
        event_dict = {"timestamp": event.Timestamp, "desc": event.EventDescription}

        try:
            # If this fails with an AttributeError, the event is
            # address-less. Fun stuff. Should usually just by
            # EventType == OC
            event_dict["details"] = "- %s, %s (%s)" % (
                event.Address.City,
                event.Address.StateOrProvinceCode,
                event.Address.CountryCode,
            )
            event_list.append(event_dict)
        except AttributeError:
            # Lacking an 'Address' attribute on the Event. This Event does
            # not contain any address info, just ignore this key.
            # Set an empty string to prevent template errors.
            event_dict["details"] = ""

    pagevars["event_list"] = event_list
    # Make the entirety of the TrackDetails object available to the template.
    pagevars["track_details"] = response.CompletedTrackDetails[0].TrackDetails[0]
    # Reference to the Shipment model representing.
    pagevars["shipment"] = tracked_shipment

    return render(request, "fedexsys/track_shipment.html", context=pagevars)


def clean_phone_number(phone_num):
    """Cleans a phone number of extraneous characters."""
    cleaned_phone = ""
    for char in phone_num:
        if char.isdigit():
            cleaned_phone += char
    return cleaned_phone


def ship_request(request, jobaddress_id=None, contact_id=None, delivery=None):
    """
    Send out a Fedex shipping request.

    jobaddress_id: (str) ID number of a JobAddress object to ship. This is
                         specific to jobs, and is used for automatically
                         printed proofs.
    contact_id: (str) The ID number of a Contact object. This means that we
                      are shipping to someone manually, not tied to a job.
    delivery: (str) Delivery method. See the 'if' statement in the body
                    of the function for details. Currently: PRON or TWOD
    """
    if jobaddress_id:
        # check to make sure that there is a phone number on the address object before we try and make a shipment.
        if get_object_or_404(JobAddress, pk=jobaddress_id).phone is None:
            return HttpResponse(
                JSMessage(
                    "New Shipments require a phone number on the address.",
                    is_error=True,
                )
            )
    else:
        # check to make sure that there is a phone number on the address object before we try and make a shipment.
        if get_object_or_404(Contact, id=contact_id).phone is None:
            return HttpResponse(
                JSMessage(
                    "New Shipments require a phone number on the address.",
                    is_error=True,
                )
            )

    # Create a new Shipment and associate it to either a JobAddress or a
    # Contact (which is not associated with a job).
    new_ship = Shipment()
    if jobaddress_id:
        new_ship.address = get_object_or_404(JobAddress, pk=jobaddress_id)
        new_ship.job = new_ship.address.job
    else:
        new_ship.address = get_object_or_404(Contact, id=contact_id)

    # This is handled in the address and jobaddress entry
    new_ship.address.phone = clean_phone_number(new_ship.address.phone)
    new_ship.address.country = countries.full_to_abbrev(new_ship.address.country)
    new_ship.address.state = countries.country_state_to_abbrev(new_ship.address.country, new_ship.address.state)

    # Depending on the shipment service value from the URL string, set the
    # shipment request object up accordingly.
    if delivery == "PRON":
        # Priority Overnight
        if not new_ship.is_international():
            new_ship.ship_service = "PRIORITY_OVERNIGHT"
        else:
            new_ship.ship_service = "INTERNATIONAL_PRIORITY"
    elif delivery == "TWOD":
        # 2-Day
        if not new_ship.is_international():
            new_ship.ship_service = "FEDEX_2_DAY"
        else:
            new_ship.ship_service = "INTERNATIONAL_ECONOMY"
    else:
        # Ship Standard.
        if not new_ship.is_international():
            new_ship.ship_service = "STANDARD_OVERNIGHT"
        else:
            new_ship.ship_service = "INTERNATIONAL_ECONOMY"

    ship_req = new_ship.get_shipment_request()

    # print ship_req.RequestedShipment
    try:
        # Send the XML request and retrieve the response
        print("going --> ship_req.send_request()")
        ship_req.send_request()
        print("returning --> ship_req.send_request()")
    except FedexError as err:
        return HttpResponse(JSMessage(err.__str__(), is_error=True))

    # print ship_req.response

    # Get the tracking number back from FedEx
    new_ship.tracking_num = str(ship_req.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber)
    # Store ASCII representation of the label for re-print
    ascii_label_data = ship_req.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
    # Convert the ASCII data to binary. The FedEx label printing machine
    # will read this, convert it to base64, and pipe that to the label printer.
    new_ship.label_data = str(ascii_label_data)
    # Determine the total cost of shipping the proof.
    new_ship.net_shipping_cost = ship_req.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount
    new_ship.save()

    if jobaddress_id and new_ship.job.customer_email:
        # If the job has a customer's email associated with it then we email the customer the FedEx tracking number.

        email_list = []
        email_list.append(new_ship.job.customer_email)

        mail_subject = "Artwork Tracking # for %s" % new_ship.job
        mail_body = loader.get_template("emails/fedex_tracking.txt")
        mail_context = {"job": new_ship.job, "track_number": new_ship.tracking_num}
        general_funcs.send_info_mail(mail_subject, mail_body.render(mail_context), email_list)

    return HttpResponse(JSMessage("Shipment completed."))


def delete_ship_request(request, tracking_num):
    """Deletes/Cancels a shipment."""
    tracked_shipment = get_object_or_404(Shipment, tracking_num=tracking_num)

    fedex_config = create_fedex_config()
    del_request = ship_service.FedexDeleteShipmentRequest(fedex_config)
    del_request.DeletionControlType = "DELETE_ALL_PACKAGES"
    del_request.TrackingId.TrackingNumber = tracking_num
    # All of our automated shipments are done via FedEx Express.
    del_request.TrackingId.TrackingIdType = "EXPRESS"
    try:
        del_request.send_request()
    except FedexError as err:
        error = str(err)
    else:
        error = None

    # Variables for inclusion via markup in the HTML template.
    pagevars = {
        "error": error,
        "TrackingNumber": tracking_num,
        "Reference": tracked_shipment.get_ref_string(),
    }

    tracked_shipment.delete()

    return render(request, "fedexsys/delete_shipment.html", context=pagevars)
