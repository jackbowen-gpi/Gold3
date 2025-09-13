from django.apps import apps
from django.test import Client, TestCase


class DjangoSuSmokeTest(TestCase):
    def test_app_registered(self):
        self.assertIn("django_su", [a.label for a in apps.get_app_configs()])

    def test_root(self):
        self.assertIn(Client().get("/").status_code, (200, 302))
