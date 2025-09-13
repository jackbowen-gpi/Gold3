from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from tests.factories import create_user


class HomePageTests(TestCase):
    def test_homepage_contains_nav_elements_for_regular_user(self):
        user = create_user(username="alice", password="password123")
        self.client.force_login(user)

        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        # Logo
        self.assertIn("img/gold2logo_sm.png", content)

        # Links that should always be present for authenticated users
        self.assertIn("HOME", content)
        self.assertIn("SEARCH", content)
        self.assertIn("REPORTS", content)
        self.assertIn("USER PREFS", content)
        self.assertIn("LOGOUT", content)

        # Username should be displayed
        self.assertIn("<strong>alice</strong>", content)

        # Admin link should not be present for regular user
        self.assertNotIn("/admin/", content)

    def test_homepage_shows_admin_for_staff(self):
        staff = create_user(username="bob", password="pw", is_staff=True)
        self.client.force_login(staff)

        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        # Admin link should be visible to staff users
        self.assertIn("/admin/", content)

    def test_todo_link_visible_based_on_permission(self):
        # User without permission should not see TO-DO LIST
        user = create_user(username="carol", password="pw")
        self.client.force_login(user)
        resp = self.client.get(reverse("home"))
        content = resp.content.decode("utf-8")
        self.assertNotIn("TO-DO LIST", content)

        # Create or get a Permission object with the expected codename and
        # assign it to the user so the template perms wrapper will expose it.
        ct, _ = ContentType.objects.get_or_create(app_label="accounts", model="user")
        perm, _ = Permission.objects.get_or_create(
            codename="in_artist_pulldown",
            name="Can see artist pulldown",
            content_type=ct,
        )
        user.user_permissions.add(perm)
        resp = self.client.get(reverse("home"))
        content = resp.content.decode("utf-8")
        self.assertIn("TO-DO LIST", content)
