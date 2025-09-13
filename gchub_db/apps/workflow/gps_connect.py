"""Modules for communication with GPS Connect."""

from xml.dom import minidom

import requests

# Machine name of the server hosting GPS connect. It's been known to change.
gps_server = "gpicstfms01"


def _get_customer_data(sap_num):
    """
    Query for retrieving customer info from GPS connect. We look up the customer
    using a number that everyone calls by a different name.

    SAP: Payer Customer
    GPS Connect: Customer number / SAP payer number
    GOLD: CustomerID (job.customer_identifier)

    Returns a dictionary of customer info.
    """
    try:
        # Get the XML file from GPS connect
        gps_request_url = (
            "http://cgxml:xml05@"
            + gps_server
            + "/fmi/xml/fmresultset.xml?-db=GPSConnect&-lay=XML_Customer&Customer%20Number="
            + sap_num
            + "&-find"
        )
        gps_requests = requests.get(gps_request_url)
    except Exception:  # Coudn't connect.
        error = "bad_connect"
        return error

    # Parse the XML file.
    doc = minidom.parseString(gps_requests.content)
    # Get all the "field" elements.
    fields = doc.getElementsByTagName("field")

    # Go through each field element and add it to a dictionary. Dictionary
    # entries that can have more than one item will be stored as lists.
    customer_dict = {}
    for field in fields:
        name = field.getAttribute("name")
        data = field.getElementsByTagName("data")[0]
        if data.firstChild:
            read_data = data.firstChild.data
        else:
            read_data = None
        # Remove odd characters from keys. Lets us use them in django templates.
        fromatted_name = name.replace(" ", "_").replace("::", "_")
        # Store everything as a list at first to catch the fields with multiple objects
        customer_dict.setdefault(fromatted_name, []).append(read_data)

    return customer_dict


def _get_customer_field_names(sap_num):
    """
    Looks up a csutomer and then returns only the names of the fields. Use this
    if you suspect a field has changed or been added. You can also specify a
    different sap number if the default one doesn't work for whatever reason.
    """
    customer_data = _get_customer_data(sap_num)
    fied_list = []
    for field in customer_data.keys():
        fied_list.append(field)

    return sorted(fied_list)
