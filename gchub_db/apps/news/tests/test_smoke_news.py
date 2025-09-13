from django.apps import apps
from django.test import Client, TestCase


class NewsSmokeTest(TestCase):
    def test_app_registered(self):
        self.assertIn("news", [a.label for a in apps.get_app_configs()])

    def test_root(self):
        self.assertIn(Client().get("/").status_code, (200, 302))
