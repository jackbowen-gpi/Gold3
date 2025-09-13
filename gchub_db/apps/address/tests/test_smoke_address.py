from django.apps import apps
from django.test import Client, TestCase


class AddressSmokeTest(TestCase):
    def test_app_registered(self):
        labels = [a.label for a in apps.get_app_configs()]
        self.assertIn("address", labels)

    def test_root(self):
        client = Client()
        resp = client.get("/")
        self.assertIn(resp.status_code, (200, 302))
