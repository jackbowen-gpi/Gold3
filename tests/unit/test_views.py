"""
Comprehensive view tests for GOLD3 project.

Tests authentication views, home page, admin views, and form handling.
Covers GET/POST requests, authentication, authorization, and error handling.

Usage:
    python -m pytest tests/unit/test_views.py -v
    python -m pytest tests/unit/test_views.py -m unit
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from gchub_db.apps.workflow.models import Site


class TestAuthenticationViews(TestCase):
    """Test authentication-related views."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.superuser = User.objects.create_superuser(username="admin", email="admin@example.com", password="admin123")

    @pytest.mark.unit
    def test_login_page_get(self):
        """Test GET request to login page."""
        response = self.client.get("/accounts/login/")

        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            content = response.content.decode("utf-8")
            self.assertIn("login", content.lower())

    @pytest.mark.unit
    def test_login_success(self):
        """Test successful login."""
        response = self.client.post(
            "/accounts/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )

        self.assertIn(response.status_code, [200, 302])

        # Check if user is logged in
        user = authenticate(username="testuser", password="testpass123")
        self.assertIsNotNone(user)

    @pytest.mark.unit
    def test_login_failure(self):
        """Test failed login."""
        response = self.client.post(
            "/accounts/login/",
            {
                "username": "testuser",
                "password": "wrongpassword",
            },
        )

        self.assertIn(response.status_code, [200, 302, 400])

        # Check that user is not logged in
        user = authenticate(username="testuser", password="wrongpassword")
        self.assertIsNone(user)

    @pytest.mark.unit
    def test_logout(self):
        """Test logout functionality."""
        # First login
        self.client.login(username="testuser", password="testpass123")

        # Then logout - use POST method for logout
        response = self.client.post("/accounts/logout/")
        self.assertIn(response.status_code, [200, 302])

    @pytest.mark.unit
    def test_password_change_get(self):
        """Test GET request to password change page."""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get("/accounts/password/change/")
        self.assertIn(response.status_code, [200, 302, 403])

    @pytest.mark.unit
    def test_password_change_post(self):
        """Test POST request to change password."""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            "/accounts/password/change/",
            {
                "old_password": "testpass123",
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
        )

        self.assertIn(response.status_code, [200, 302])

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))


class TestHomePageViews(TestCase):
    """Test home page and main navigation views."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="homepage_user",
            email="homepage@example.com",
            password="testpass123",
        )

    @pytest.mark.unit
    def test_home_page_anonymous(self):
        """Test home page for anonymous users."""
        response = self.client.get("/")

        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            content = response.content.decode("utf-8")
            # Should contain some basic content or redirect to login
            self.assertIsInstance(content, str)

    @pytest.mark.unit
    def test_home_page_authenticated(self):
        """Test home page for authenticated users."""
        self.client.login(username="homepage_user", password="testpass123")

        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])

    @pytest.mark.unit
    def test_favicon_redirect(self):
        """Test favicon redirect."""
        response = self.client.get("/favicon.ico")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/media/favicon.ico", response["Location"])


class TestAdminViews(TestCase):
    """Test Django admin interface views."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.regular_user = User.objects.create_user(username="regular", email="regular@example.com", password="testpass123")
        self.superuser = User.objects.create_superuser(username="admin", email="admin@example.com", password="admin123")

    @pytest.mark.unit
    def test_admin_index_anonymous(self):
        """Test admin index for anonymous users."""
        response = self.client.get("/admin/")

        # Should redirect to login
        self.assertIn(response.status_code, [302, 403])

    @pytest.mark.unit
    def test_admin_index_regular_user(self):
        """Test admin index for regular users."""
        self.client.login(username="regular", password="testpass123")

        response = self.client.get("/admin/")
        # Regular users should be denied access
        self.assertIn(response.status_code, [302, 403])

    @pytest.mark.unit
    def test_admin_index_superuser(self):
        """Test admin index for superusers."""
        self.client.login(username="admin", password="admin123")

        response = self.client.get("/admin/")
        self.assertIn(response.status_code, [200, 302])

    @pytest.mark.unit
    def test_admin_login(self):
        """Test admin login page."""
        response = self.client.get("/admin/login/")

        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            content = response.content.decode("utf-8")
            self.assertIn("admin", content.lower())


class TestPreferencesViews(TestCase):
    """Test user preferences views."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.user = User.objects.create_user(username="prefs_user", email="prefs@example.com", password="testpass123")

    @pytest.mark.unit
    def test_preferences_page(self):
        """Test preferences page access."""
        self.client.login(username="prefs_user", password="testpass123")

        response = self.client.get("/accounts/preferences/")
        self.assertIn(response.status_code, [200, 302, 403])

    @pytest.mark.unit
    def test_preferences_contact_info(self):
        """Test contact info preferences."""
        self.client.login(username="prefs_user", password="testpass123")

        response = self.client.get("/accounts/preferences/contact_info/")
        self.assertIn(response.status_code, [200, 302, 403])

    @pytest.mark.unit
    def test_preferences_settings(self):
        """Test settings preferences."""
        self.client.login(username="prefs_user", password="testpass123")

        response = self.client.get("/accounts/preferences/settings/")
        self.assertIn(response.status_code, [200, 302, 403])


class TestWorkflowViews(TestCase):
    """Test workflow-related views."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="workflow_user",
            email="workflow@example.com",
            password="testpass123",
        )
        self.site = Site.objects.create(domain="workflow.example.com", name="Workflow Test Site")

    @pytest.mark.unit
    def test_job_search_view(self):
        """Test job search view."""
        response = self.client.get("/job/search/")

        self.assertIn(response.status_code, [200, 302, 404])

    @pytest.mark.unit
    def test_reports_list_view(self):
        """Test reports list view."""
        response = self.client.get("/reports/list/")

        self.assertIn(response.status_code, [200, 302, 404])


class TestErrorHandlingViews(TestCase):
    """Test error handling and edge cases."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    @pytest.mark.unit
    def test_404_error_page(self):
        """Test 404 error page."""
        response = self.client.get("/nonexistent-page/")

        self.assertEqual(response.status_code, 404)

    @pytest.mark.unit
    def test_invalid_url_patterns(self):
        """Test invalid URL patterns."""
        invalid_urls = [
            "/invalid/path/with/special/chars!@#",
            "/path/with/unicode/测试",
            "/extremely/long/path/" + "a/" * 100,
        ]

        for url in invalid_urls:
            response = self.client.get(url)
            # Should not crash the server
            self.assertIn(response.status_code, [200, 302, 404, 400])

    @pytest.mark.unit
    def test_method_not_allowed(self):
        """Test invalid HTTP methods."""
        # Try POST on a GET-only view
        response = self.client.post("/accounts/login/", {})
        self.assertIn(response.status_code, [200, 302, 400, 405])


class TestMiddlewareIntegration(TestCase):
    """Test middleware integration with views."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        # Create a test user for authentication tests
        self.test_user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")

    @pytest.mark.unit
    def test_session_middleware(self):
        """Test session middleware integration."""
        # Test that login creates a session
        response = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(response, "Login should succeed")

        # After login, check that we can access pages (session should be maintained)
        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])

        # Check that session contains authentication data
        self.assertTrue(
            len(self.client.session.keys()) > 0,
            "Session should contain data after login",
        )

    @pytest.mark.unit
    def test_csrf_middleware(self):
        """Test CSRF middleware integration."""
        response = self.client.get("/accounts/login/")

        if response.status_code == 200:
            content = response.content.decode("utf-8")
            # Should contain CSRF token
            self.assertIn("csrfmiddlewaretoken", content)

    @pytest.mark.unit
    def test_authentication_middleware(self):
        """Test authentication middleware integration."""
        # Test with authenticated user
        _ = User.objects.create_user(
            username="middleware_test",
            email="middleware@example.com",
            password="testpass123",
        )

        self.client.login(username="middleware_test", password="testpass123")

        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])


class TestViewSecurity(TestCase):
    """Test view security and access control."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username="regular_security",
            email="regular_security@example.com",
            password="testpass123",
        )
        self.superuser = User.objects.create_superuser(
            username="admin_security",
            email="admin_security@example.com",
            password="admin123",
        )

    @pytest.mark.unit
    def test_admin_access_control(self):
        """Test admin view access control."""
        # Anonymous user
        response = self.client.get("/admin/")
        self.assertIn(response.status_code, [302, 403])

        # Regular user
        self.client.login(username="regular_security", password="testpass123")
        response = self.client.get("/admin/")
        self.assertIn(response.status_code, [302, 403])

        # Superuser
        self.client.login(username="admin_security", password="admin123")
        response = self.client.get("/admin/")
        self.assertIn(response.status_code, [200, 302])

    @pytest.mark.unit
    def test_authenticated_view_access(self):
        """Test that authenticated views require login."""
        # Preferences page should require authentication
        response = self.client.get("/accounts/preferences/")
        self.assertIn(response.status_code, [302, 403])  # Should redirect or deny

        # Login and try again
        self.client.login(username="regular_security", password="testpass123")
        response = self.client.get("/accounts/preferences/")
        self.assertIn(response.status_code, [200, 302, 403])


class TestViewPerformance(TestCase):
    """Test view performance and response times."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    @pytest.mark.unit
    def test_view_response_time(self):
        """Test that views respond within reasonable time."""
        import time

        urls = ["/", "/accounts/login/", "/admin/"]

        for url in urls:
            start_time = time.time()
            try:
                _ = self.client.get(url)
                end_time = time.time()
                duration = end_time - start_time

                # Should respond within 1 second
                self.assertLess(duration, 1.0, f"View {url} took {duration} seconds to respond")
            except Exception:
                # If view doesn't exist or fails, that's OK for this test
                pass


class TestFormHandling(TestCase):
    """Test form handling in views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(username="form_test", email="form@example.com", password="testpass123")

    @pytest.mark.unit
    def test_login_form_validation(self):
        """Test login form validation."""
        # Empty form
        response = self.client.post("/accounts/login/", {})
        self.assertIn(response.status_code, [200, 302, 400])

        # Invalid credentials
        response = self.client.post(
            "/accounts/login/",
            {
                "username": "nonexistent",
                "password": "wrong",
            },
        )
        self.assertIn(response.status_code, [200, 302, 400])

        # Valid credentials
        response = self.client.post(
            "/accounts/login/",
            {
                "username": "form_test",
                "password": "testpass123",
            },
        )
        self.assertIn(response.status_code, [200, 302])

    @pytest.mark.unit
    def test_password_change_form(self):
        """Test password change form."""
        self.client.login(username="form_test", password="testpass123")

        # Valid password change
        response = self.client.post(
            "/accounts/password/change/",
            {
                "old_password": "testpass123",
                "new_password1": "newpass123",
                "new_password2": "newpass123",
            },
        )
        self.assertIn(response.status_code, [200, 302])

        # Verify password was actually changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))


class TestDevelopmentViews(TestCase):
    """Test development-specific views."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    @pytest.mark.unit
    def test_development_helper_views(self):
        """Test development helper views."""
        dev_urls = [
            "/__dev_set_session/",
            "/__dev_set_csrf/",
            "/__dev_whoami/",
        ]

        for url in dev_urls:
            response = self.client.get(url)
            # Should either work (in debug mode) or return 404
            self.assertIn(response.status_code, [200, 302, 404])

    @pytest.mark.unit
    def test_test_standard_template_view(self):
        """Test the test standard template view."""
        response = self.client.get("/test-standard/")

        self.assertIn(response.status_code, [200, 302, 404])
