from django.test import TestCase
from django.urls import reverse


class PublicHomeTests(TestCase):
    def test_public_homepage_shows_welcome_and_login_link(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        self.assertIn("Welcome to GOLD", content)
        self.assertIn("/accounts/login/", content)
