"""
Minimal test to isolate issues.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.test_settings")

import django

django.setup()

from django.test import TestCase
from django.test import Client


class MinimalTest(TestCase):
    """Minimal test case."""

    def test_basic_assertion(self):
        """Basic test."""
        self.assertTrue(True)

    def test_client_creation(self):
        """Test client creation."""
        client = Client()
        self.assertIsNotNone(client)
