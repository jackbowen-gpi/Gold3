from django.test import TestCase
from django.urls import reverse
from tests.factories import create_user


class AddedAccountsTests(TestCase):
    def test_create_user_and_login(self):
        user = create_user(username="extra_user", password="pw123")
        logged = self.client.login(username=user.username, password="pw123")
        self.assertTrue(logged, "created user should be able to log in with given password")
        # home view should be reachable for logged-in users
        resp = self.client.get(reverse("home"))
        self.assertIn(resp.status_code, (200, 302))

    def test_public_home_is_accessible(self):
        """Anonymous public home should be reachable by guests."""
        resp = self.client.get(reverse("public_home"))
        self.assertEqual(resp.status_code, 200)
