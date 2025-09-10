#!/usr/bin/python
"""JMF Gateway module"""

import http.client
import os
import sys
from xml.dom import minidom

# Setup the Django environment
sys.path.append("../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
from django.conf import settings

# Back to the ordinary imports
from django.urls import reverse


class JMFMessage(object):
    """Standard JMF class with common stuff on it."""

    # Holds the minidom Document
    doc = None
    # Reference to the root containing JDF node
    doc_root = None
    debug = False
    message_name = "JMFMessage"

    def get_xml_doc_string(self):
        """Returns a string representation of the document via prettyprint."""
        return self.doc.toxml()

    def __init__(self, debug=False):
        """Document initialization."""
        self.debug = debug
        self.doc = minidom.Document()

        self.doc_root = self.doc.createElement("JMF")
        self.doc_root.setAttribute("SenderID", "QMon")
        self.doc_root.setAttribute("Version", "1.2")
        self.doc_root.setAttribute(
            "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance"
        )

    def execute(self):
        """Processes the request by sending it to the FedEx server. Stores
        a minidom.Document object containing the result of the query in
        the object's responsexml property.
        """
        req_xml = "%s" % self.doc.toxml()

        print("EXECUTING")

        hcon = http.client.HTTPConnection(settings.JMF_GATEWAY)
        hcon.putrequest("POST", settings.JMF_GATEWAY_PATH)
        hcon.putheader("Content-Length", len(req_xml))
        hcon.putheader("Content-Type", "application/vnd.cip4-jmf+xml")
        hcon.endheaders()
        hcon.send(req_xml)
        hres = hcon.getresponse()

        print("GOT RESPONSE")

        self.response = hres.read()
        self.responsexml = minidom.parseString(self.response)

        if self.debug:
            print("-" * 80)
            print("Message: %s" % self.__class__.__name__)
            print("-" * 80)
            print(self.doc.toprettyxml())
            print("-" * 80)
            print("Backstage Response")
            print("-" * 80)
            print(self.responsexml.documentElement.toprettyxml())
            print("-" * 80)


class JMFKnownMessages(JMFMessage):
    """Send a JMF KnownMessages request to BackStage."""

    def __init__(self):
        """Document initialization."""
        super(JMFKnownMessages, self).__init__()

        query = self.doc.createElement("Query")
        query.setAttribute("ID", "Link1290_5")
        query.setAttribute("Type", "KnownMessages")

        self.doc_root.appendChild(query)  # type: ignore
        self.doc.appendChild(self.doc_root)


class JMFKnownDevices(JMFMessage):
    """Send a JMF KnownDevices request to BackStage."""

    def __init__(self):
        """Document initialization."""
        super(JMFKnownDevices, self).__init__()

        query = self.doc.createElement("Query")
        query.setAttribute("ID", "Link1290_5")
        query.setAttribute("Type", "KnownDevices")

        self.doc_root.appendChild(query)  # type: ignore
        self.doc.appendChild(self.doc_root)


class JMFSubscription(JMFMessage):
    """Subscribes to a certain kind of event in Backstage."""

    def __init__(self, url, event_type="Events", xsi_type="QueryEvents", debug=False):
        """Document initialization."""
        super(JMFSubscription, self).__init__(debug=debug)

        query = self.doc.createElement("Query")
        query.setAttribute("ID", "Subscribe")
        query.setAttribute("Type", event_type)
        # query.setAttribute('xsi:type', xsi_type)

        subscription = self.doc.createElement("Subscription")
        subscription.setAttribute("URL", url)
        query.appendChild(subscription)

        self.doc_root.appendChild(query)  # type: ignore
        self.doc.appendChild(self.doc_root)


class JMFUnsubscribe(JMFMessage):
    """Unsubscribes a URL."""

    def __init__(self, url, debug=False):
        """Document initialization."""
        super(JMFUnsubscribe, self).__init__(debug=debug)

        query = self.doc.createElement("Command")
        query.setAttribute("ID", "Unsubscribe")
        # query.setAttribute('Type', 'Events')
        # query.setAttribute('xsi:type', 'QueryEvents')
        query.setAttribute("Type", "StopPersistentChannel")
        query.setAttribute("xsi:type", "CommandStopPersistentChannel")

        subscription = self.doc.createElement("StopPersChParams")
        subscription.setAttribute("URL", url)
        query.appendChild(subscription)

        self.doc_root.appendChild(query)  # type: ignore
        self.doc.appendChild(self.doc_root)


class JMFSubmitQueueEntry(JMFMessage):
    """Send a JMF SubmitQueueEntry request to Backstage. This is done to order
    Backstage to visit a URL to grab a JDF that is to be executed.
    """

    def __init__(self, url, debug=False):
        """Document initialization."""
        super(JMFSubmitQueueEntry, self).__init__(debug=debug)

        command = self.doc.createElement("Command")
        command.setAttribute("ID", "Job9043")
        command.setAttribute("Type", "SubmitQueueEntry")

        submission_params = self.doc.createElement("QueueSubmissionParams")
        submission_params.setAttribute("Hold", "false")
        submission_params.setAttribute("Priority", "50")
        submission_params.setAttribute("URL", settings.WEBSERVER_HOST + url)
        submission_params.setAttribute("ReturnJMF", "http://172.23.8.96:8001/xml/echo")
        command.appendChild(submission_params)

        self.doc_root.appendChild(command)  # type: ignore
        self.doc.appendChild(self.doc_root)


"""
Execute the following if this script is called directly through the shell.
Test cases.
"""
if __name__ == "__main__":
    # ex_sub = True
    ex_sub = False

    # ex_unsub = True
    ex_unsub = False

    ex_queue = True
    # ex_queue = False

    if ex_sub:
        t2 = JMFSubscription("http://172.23.8.96:8000/xml/echo", debug=True)
        # t2 = JMFSubscription('http://172.23.8.96:8000/xml/echo', event_type="QueueStatus", xsi_type="QueueStatus", debug=True)
        t2.execute()

    if ex_unsub:
        t2 = JMFUnsubscribe("http://172.23.8.96:8000/xml/echo", debug=True)
        t2.execute()

    if ex_queue:
        t = JMFSubmitQueueEntry(
            reverse("jdf-gen-item", args=[49297, 1, "fsb_proof"]), debug=True
        )
        # t = JMFKnownDevices()
        # t = JMFKnownMessages()
        t.execute()
