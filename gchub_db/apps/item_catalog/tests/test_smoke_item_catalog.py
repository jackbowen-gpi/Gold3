from django.apps import apps
from django.test import Client, TestCase


class ItemCatalogSmokeTest(TestCase):
    def test_app_is_registered(self):
        labels = [a.label for a in apps.get_app_configs()]
        self.assertIn("item_catalog", labels)

    def test_item_catalog_root(self):
        client = Client()
        resp = client.get("/")
        self.assertIn(resp.status_code, (200, 302))
