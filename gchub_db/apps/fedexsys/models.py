import binascii

from django.conf import settings
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone

try:
    from fedex.services.address_validation_service import FedexAddressValidationRequest
    from fedex.services.ship_service import FedexProcessShipmentRequest
except Exception:
    # Provide lightweight fallbacks for local development when fedex package
    # isn't installed. These dummies will raise if used at runtime.
    class _FedexDummy:
        def __init__(self, *args, **kwargs):
            raise ImportError("fedex package not installed")

    FedexProcessShipmentRequest = _FedexDummy
    FedexAddressValidationRequest = _FedexDummy
from gchub_db.apps.fedexsys import countries
from gchub_db.apps.fedexsys.defines import (
    CARRIER_CODES,
    PACKAGING_CODES,
    SHIPPING_SERVICES,
)

from .config_factory import create_fedex_config


class Shipment(models.Model):
    """Represents a Fedex Shipment. These may be directed to individual people,
    or sent automatically when a job is proofed out.
    """

    # When associating to a JobAddress, store the Job here for easier retrieval.
    job = models.ForeignKey(
        "workflow.Job", on_delete=models.CASCADE, blank=True, null=True
    )
    """
    The next three fields form a generic relation to JobAddress and Contact
    models. The two models must preserve cross-compatibility in methods and
    attributes to allow them both to be referred to the same.
    """
    address_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    address_id = models.PositiveIntegerField()
    address = fields.GenericForeignKey("address_content_type", "address_id")

    # Populated by Fedex after sending a request.
    tracking_num = models.CharField(blank=True, max_length=15)
    date_shipped = models.DateTimeField(auto_now_add=True)
    # When this is None, the label printing queue checker will print the label.
    date_label_printed = models.DateTimeField(blank=True, null=True)
    # This will pretty much always be Fedex Express (FDXE).
    ship_carrier_code = models.CharField(
        max_length=15, choices=CARRIER_CODES, default="FDXE"
    )
    ship_packaging = models.CharField(
        max_length=50, choices=PACKAGING_CODES, default="FEDEX_PAK"
    )
    # Our packages are almost always very light.
    ship_weight = models.FloatField(default=1.0)
    ship_service = models.CharField(
        max_length=75, choices=SHIPPING_SERVICES, default="PRIORITY_OVERNIGHT"
    )
    label_data = models.TextField(blank=True, null=True)
    # Net (total) cost of shipping.
    net_shipping_cost = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.get_ref_string()

    def get_ref_string(self):
        """Returns the shipment's reference string. For example:
        50883 SMRE_12 SD
        """
        if self.job:
            return "%s %s" % (self.job.id, self.job.name)
        else:
            return "%s" % (self.get_recipient())

    def get_recipient(self):
        """Returns the recipient. First check for Person, then go to company."""
        if self.address.name:
            return self.address.name
        else:
            return self.address.company

    def is_international(self):
        """Returns True if this shipment is an international shipment."""
        return countries.full_to_abbrev(self.address.country) != "US"

    def print_label(self, debug=False):
        """Grabs the textual representation of the label from the XML response,
        converts it to base64, and pipes it directly into the label printer
        via a device node in /dev/
        """
        if debug:
            print(("Label output type: " + settings.FEDEX_LABEL_IMG_TYPE))

        # Convert the ASCII label representation in the XML response to base64
        label_binary = binascii.a2b_base64(self.label_data)

        # Pipe the binary directly to the label printer. Works under Linux
        # without requiring PySerial.
        label_file = open("/dev/usb/lp0", "wb+")
        label_file.write(label_binary)
        label_file.close()

        # The following is printing with the PySerial module. We shouldn't ever
        # really need it, but it would work under Windows.
        """
        import serial
        ser = serial.Serial(0)
        print("SELECTED PORT: "+ ser.portstr)
        ser.write(label_binary)
        ser.close()
        """
        self.date_label_printed = timezone.now()
        self.save()

    def get_shipment_request(self):
        """Populates and returns a FedexProcessShipmentRequest object that
        is pretty much ready for sending. Final adjustments may be applied
        in the view.
        """
        config_obj = create_fedex_config()
        shipment = FedexProcessShipmentRequest(config_obj)
        shipment.RequestedShipment.DropoffType = "REGULAR_PICKUP"
        shipment.RequestedShipment.ServiceType = self.ship_service
        shipment.RequestedShipment.PackagingType = self.ship_packaging

        # Shipper contact info.
        shipment.RequestedShipment.Shipper.Contact.CompanyName = settings.GCHUB_COMPANY
        shipment.RequestedShipment.Shipper.Contact.PhoneNumber = settings.GCHUB_PHONE

        # Shipper address.
        shipment.RequestedShipment.Shipper.Address.StreetLines = [
            settings.GCHUB_ADDRESS1,
            settings.GCHUB_ADDRESS2,
        ]
        shipment.RequestedShipment.Shipper.Address.City = settings.GCHUB_CITY
        shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = (
            settings.GCHUB_STATE
        )
        shipment.RequestedShipment.Shipper.Address.PostalCode = settings.GCHUB_ZIP
        shipment.RequestedShipment.Shipper.Address.CountryCode = (
            settings.GCHUB_COUNTRY_CODE
        )
        shipment.RequestedShipment.Shipper.Address.Residential = False

        # Recipient contact info.
        if self.address.name:
            shipment.RequestedShipment.Recipient.Contact.PersonName = self.address.name
        if self.address.company:
            shipment.RequestedShipment.Recipient.Contact.CompanyName = (
                self.address.company
            )
        shipment.RequestedShipment.Recipient.Contact.PhoneNumber = self.address.phone

        # Recipient address
        address_lines = [self.address.address1]
        if self.address.address2:
            address_lines.append(self.address.address2)

        shipment.RequestedShipment.Recipient.Address.StreetLines = address_lines
        shipment.RequestedShipment.Recipient.Address.City = self.address.city
        shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = (
            self.address.state
        )
        shipment.RequestedShipment.Recipient.Address.PostalCode = self.address.zip
        country_code = countries.full_to_abbrev(self.address.country)
        shipment.RequestedShipment.Recipient.Address.CountryCode = country_code

        shipment.RequestedShipment.ShippingChargesPayment.Payor.ResponsibleParty.AccountNumber = (
            config_obj.account_number
        )
        shipment.RequestedShipment.ShippingChargesPayment.PaymentType = "SENDER"
        shipment.RequestedShipment.LabelSpecification.LabelFormatType = "COMMON2D"
        shipment.RequestedShipment.LabelSpecification.ImageType = "EPL2"
        shipment.RequestedShipment.LabelSpecification.LabelStockType = (
            "STOCK_4X6.75_LEADING_DOC_TAB"
        )
        #         shipment.RequestedShipment.LabelSpecification.LabelStockType = 'STOCK_4X6'
        shipment.RequestedShipment.LabelSpecification.LabelPrintingOrientation = (
            "BOTTOM_EDGE_OF_TEXT_FIRST"
        )

        package1_weight = shipment.create_wsdl_object_of_type("Weight")
        # Weight, in pounds.
        package1_weight.Value = 1.0
        package1_weight.Units = "LB"

        package1 = shipment.create_wsdl_object_of_type("RequestedPackageLineItem")
        package1.Weight = package1_weight

        if self.is_international():
            shipment.RequestedShipment.CustomsClearanceDetail.DocumentContent = (
                "DOCUMENTS_ONLY"
            )
            shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency = (
                "USD"
            )
            shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount = (
                "1.00"
            )

            commod = shipment.create_wsdl_object_of_type("Commodity")
            commod.NumberOfPieces = "1"
            commod.Description = "Printed Proofs"
            commod.CountryOfManufacture = "US"
            commod.Weight.Units = "LB"
            commod.Weight.Value = "1.0"
            commod.Quantity = "1"
            commod.QuantityUnits = "EA"
            commod.UnitPrice.Currency = "USD"
            commod.UnitPrice.Amount = "1.00"
            shipment.RequestedShipment.CustomsClearanceDetail.Commodities.append(commod)

            shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.PaymentType = (
                "SENDER"
            )
            shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor.ResponsibleParty.AccountNumber = (
                config_obj.account_number
            )
            shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor.ResponsibleParty.Address.CountryCode = (
                "US"
            )

        # Un-comment this to see the other variables you may set on a package.
        # print package1

        # This adds the RequestedPackageLineItem WSDL object to the shipment. It
        # increments the package count and total weight of the shipment for you.
        shipment.add_package(package1)

        return shipment

    def get_absolute_url(self):
        return reverse("shipment_track", args=[self.tracking_num])


class AddressValidationModel(models.Model):
    """This abstract model enables any sub-classes to validate their addresses.
    Note that the fields must match up with the apps.address.models.Contact
    for this to work.
    """

    class Meta:
        abstract = True

    def validate_address(self):
        """Sends a FedEx validation request. Returns the response directly. Check
        the score or overall status attributes for the result.
        """
        config_obj = create_fedex_config()
        address = FedexAddressValidationRequest(config_obj)
        address1 = address.create_wsdl_object_of_type("AddressToValidate")
        if self.company:
            address1.CompanyName = self.company
        address1.Address.StreetLines = [self.address1]
        if self.address2:
            address1.Address.StreetLines.append(self.address2)
        address1.Address.City = self.city
        address1.Address.StateOrProvinceCode = self.state
        address1.Address.PostalCode = self.zip_code
        country_code = countries.full_to_abbrev(self.country)
        address1.Address.CountryCode = country_code

        address.add_address(address1)
        address.send_request()

        # Un-comment this to see the full response.
        # print address.response
