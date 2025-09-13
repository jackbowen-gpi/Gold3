from django.apps import apps
from django.test import Client, TestCase


class AdminLogSmokeTest(TestCase):
    def test_app_registered(self):
        self.assertIn("admin_log", [a.label for a in apps.get_app_configs()])

    def test_root(self):
        resp = Client().get("/")
        self.assertIn(resp.status_code, (200, 302))
