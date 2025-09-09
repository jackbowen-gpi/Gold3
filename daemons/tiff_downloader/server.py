#!/usr/bin/env python
"""Simple Tornado-based webserver that serves TIFFs for platemaking.

This module provides small handlers used to download single TIFF files or a
ZIP archive of all TIFFs for an Item.
"""

import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
from django.conf import settings

sys.path.insert(0, os.path.join(settings.MAIN_PATH, "includes"))

import urllib.error
import urllib.parse
import urllib.request

import tornado.httpserver
import tornado.ioloop
import tornado.web

from gchub_db.apps.workflow.models import Item
from gchub_db.includes import fs_api


class SingleTiffDownloader(tornado.web.RequestHandler):
    """Handles requests for single tiff files.

    Minimal docstring added to satisfy docstring checks. The handler returns
    a 404 HTTP error when the item or tiff is not found.
    """

    def get(self, item_id, tiff_file):
        """Handle GET request for a single TIFF by item id and filename."""
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            error_msg = "SingleTiffDownloader: Item with ID %s not found." % item_id
            # Mask internal exception details when presenting a 404 to the user.
            raise tornado.web.HTTPError(404, error_msg) from None

        tiff_file = urllib.parse.unquote(tiff_file)
        try:
            filepath = fs_api.get_item_tiff_path(
                item.job.id, item.num_in_job, tiff_file
            )
        except fs_api.NoResultsFound:
            error_msg = "SingleTiffDownloader: Couldn't find tiff: %s" % tiff_file
            # Intentional masking: don't expose fs_api internals to the client.
            raise tornado.web.HTTPError(404, error_msg) from None

        with open(filepath, "rb") as f:
            data = f.read()

        self.set_header("Content-Type", "image/tiff")
        self.set_header(
            "Content-Disposition", 'attachment; filename="' + str(tiff_file) + '"'
        )
        self.write(data)


class ItemZipTiffDownloader(tornado.web.RequestHandler):
    """Zip and send all TIFFs that belong to an Item."""

    def get(self, item_id):
        """Handle GET request to return a ZIP of all TIFFs for an item."""
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            error_msg = "ItemZipTiffDownloader: Item with ID %s not found." % item_id
            # Mask internal exception details when returning a 404.
            raise tornado.web.HTTPError(404, error_msg) from None

        # Platemaking uses a specific file naming convention; handle that here.
        send_name = str(item.job.id) + "-" + str(item.num_in_job)
        if item.job.workflow.name == "Beverage":
            send_name = send_name + "-" + str(item.bev_nomenclature())
        if item.job.workflow.name == "Foodservice":
            if item.fsb_nine_digit:
                send_name = str(item.fsb_nine_digit) + "-" + send_name

        # This contains the raw contents of the zip archive containing the tiffs.
        zip_contents = fs_api.get_zip_all_tiffs(item.job.id, item.num_in_job)

        self.set_header("Content-Type", "application/zip")
        self.set_header(
            "Content-Disposition", 'attachment; filename="' + send_name + ".zip" + '"'
        )
        self.write(zip_contents)


"""
URL handling
"""
application = tornado.web.Application(
    [
        # Example path for a single TIFF download. Split across lines for
        # readability and to satisfy line-length checks.
        # /workflow/item/26038550/57270-1/smrp-4-31web_DQPO3902G.tif/get_single_tiff/
        (r"/workflow/item/([0-9]+)/(.+)/get_single_tiff/", SingleTiffDownloader),
        # http://localhost:8989/workflow/item/26038550/get_zipfile_tiff/
        (r"/workflow/item/([0-9]+)/get_zipfile_tiff/", ItemZipTiffDownloader),
    ]
)

if __name__ == "__main__":
    """
    Main application logic.
    """
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.bind(8000, address="172.23.8.59")
    http_server.start()
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print("\n\rShutting down. (Keyboard Interrupt)")
        tornado.ioloop.IOLoop.instance().stop()
        sys.exit(0)
