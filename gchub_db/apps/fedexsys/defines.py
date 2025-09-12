"""
This file is for common global defines that generally shouldn't change.
Anything that is subject to change is likely to be in the application's
settings.py file.
"""

APIURL = "http://www.fedex.com/fsmapi"
XSIURL = "http://www.w3.org/2001/XMLSchema-instance"
SUBSCRIBE_NNSLOC = "FDXSubscriptionRequest.xsd"  # NNSLOC is "xsi:noNamespaceSchemaLocation"
URL_RATE_CHECK = "/GatewayDC"

# Used in the ship_carrier_code field
CARRIER_CODES = (
    ("FDXE", "FedEx Express"),
    ("FDXG", "FedEx Ground"),
    ("FDXC", "FedEx Cargo"),
    ("FXCC", "FedEx Custom Critical"),
    ("FXFR", "FedEx Freight"),
)

# Used in the ship_packaging field
PACKAGING_CODES = (
    ("FEDEX_ENVELOPE", "FedEx Envelope"),
    ("FEDEX_PAK", "FedEx Pak"),
    ("FEDEX_BOX", "FedEx Box"),
    ("FEDEX_TUBE", "FedEx Tube"),
    ("FEDEX_10KG_BOX", "FedEx 10 kg Box"),
    ("FEDEX_25KG_BOX", "FedEx 25 kg Box"),
    ("YOUR_PACKAGING", "Packaging Supplied"),
)

# Used in the ship_service field
SHIPPING_SERVICES = (
    ("PRIORITY_OVERNIGHT", "Priority Overnight"),
    ("STANDARD_OVERNIGHT", "Standard Overnight"),
    ("FIRST_OVERNIGHT", "First Overnight"),
    ("FEDEX_2_DAY", "FedEx Two Day"),
    ("FEDEX_EXPRESS_SAVER", "FedEx Express Saver"),
    ("INTERNATIONAL_PRIORITY", "International - Priority"),
    ("INTERNATIONAL_ECONOMY", "International - Economy"),
    ("INTERNATIONAL_FIRST", "International - First Class"),
    ("FEDEX_GROUND", "FedEx Ground"),
    ("GROUND_HOME_DELIVERY", "Ground Home Delivery"),
    ("EUROPE_FIRST_INTERNATIONAL_PRIORITY", "Europe - First International Priority"),
)
