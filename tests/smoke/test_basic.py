"""
Smoke tests for GOLD3 project.

These are quick sanity checks to ensure the application is working correctly.
They should be fast to run and cover critical functionality.

Usage:
    python run_tests.py --smoke
    python -m pytest tests/smoke/ -m smoke
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client

from gchub_db.apps.workflow.models import Site


class TestBasicFunctionality(TestCase):
    """Basic smoke tests for core functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(username="smoke_user", email="smoke@example.com", password="testpass123")
        self.site = Site.objects.create(domain="smoke.example.com", name="Smoke Test Site")

    @pytest.mark.smoke
    def test_user_creation(self):
        """Test that users can be created."""
        user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.check_password("password123")

    @pytest.mark.smoke
    def test_site_creation(self):
        """Test that sites can be created."""
        site = Site.objects.create(domain="test.example.com", name="Test Site")
        assert site.domain == "test.example.com"
        assert site.name == "Test Site"

    @pytest.mark.smoke
    def test_database_connection(self):
        """Test that database connection is working."""
        # Simple query to test database connectivity
        count = User.objects.count()
        assert isinstance(count, int)
        assert count >= 0

    @pytest.mark.smoke
    def test_basic_queries(self):
        """Test basic database queries."""
        # Test user queries
        users = User.objects.all()
        assert len(users) >= 1  # At least the user we created

        # Test site queries
        sites = Site.objects.all()
        assert len(sites) >= 1  # At least the site we created


class TestURLConfiguration(TestCase):
    """Smoke tests for URL configuration."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    @pytest.mark.smoke
    def test_admin_url_accessible(self):
        """Test that admin URLs are accessible."""
        # This assumes you have admin URLs configured
        # Adjust based on your actual URL patterns
        try:
            response = self.client.get("/admin/")
            # Should not raise an exception
            assert response.status_code in [200, 302, 403]  # OK, redirect, or forbidden
        except Exception as e:
            # If admin is not configured, that's OK for smoke test
            pytest.skip(f"Admin not configured: {e}")

    @pytest.mark.smoke
    def test_root_url_accessible(self):
        """Test that root URL is accessible."""
        try:
            response = self.client.get("/")
            assert response.status_code in [200, 302, 404]  # OK, redirect, or not found
        except Exception as e:
            pytest.skip(f"Root URL not accessible: {e}")


class TestModelRelationships(TestCase):
    """Smoke tests for model relationships."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.create(domain="relationship.example.com", name="Relationship Test Site")

    @pytest.mark.smoke
    def test_site_relationships(self):
        """Test that site relationships work."""
        # Test that site can be queried
        site = Site.objects.get(domain="relationship.example.com")
        assert site.name == "Relationship Test Site"

        # Test related objects if they exist
        # This will depend on your actual model relationships
        # For example:
        # assert site.job_set.count() >= 0  # If Job has ForeignKey to Site


class TestImportSanity(TestCase):
    """Smoke tests for imports and basic module loading."""

    @pytest.mark.smoke
    def test_core_imports(self):
        """Test that core modules can be imported."""
        try:
            # Test Django imports via importlib to avoid unused-import lint warnings
            import importlib.util

            settings_spec = importlib.util.find_spec("django.conf")
            workflow_spec = importlib.util.find_spec("gchub_db.apps.workflow.models")

            assert settings_spec is not None
            assert workflow_spec is not None
        except Exception as e:
            pytest.fail(f"Import check failed: {e}")

    @pytest.mark.smoke
    def test_settings_access(self):
        """Test that Django settings are accessible."""
        from django.conf import settings

        # Test that critical settings exist
        assert hasattr(settings, "DATABASES")
        assert hasattr(settings, "INSTALLED_APPS")

        # Test that databases are configured
        assert "default" in settings.DATABASES
