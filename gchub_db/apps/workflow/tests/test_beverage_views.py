from django.test import Client, TestCase

from tests.factories import create_site, create_user


class BeverageViewTests(TestCase):
    def setUp(self):
        # Ensure the Beverage site exists
        create_site(name="Beverage", defaults={"domain": "localhost"})
        self.client = Client()
        # create and login a test user

        u, _ = create_user(username="testuser")
        u.set_password("password")
        u.save()
        self.client.login(username="testuser", password="password")

    def test_new_beverage_get(self):
        resp = self.client.get("/workflow/job/new/beverage/", HTTP_HOST="127.0.0.1:8002")
        self.assertIn(resp.status_code, (200, 302))
        if resp.status_code == 200:
            self.assertIn("<form", resp.content.decode("utf-8"))
