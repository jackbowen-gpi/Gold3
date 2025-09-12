"""
Test utilities and helper functions for GOLD3 project.

This module contains common test fixtures, helper functions, and utilities
that can be used across different test files.

Usage:
    from tests.utils.test_helpers import create_test_user, create_test_site
"""

import pytest
from django.contrib.auth.models import User
from django.test import TestCase

from gchub_db.apps.workflow.models import Site, ItemCatalog


@pytest.fixture
def test_user():
    """Pytest fixture for creating a test user."""
    return User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")


@pytest.fixture
def test_site():
    """Pytest fixture for creating a test site."""
    return Site.objects.create(domain="test.example.com", name="Test Site")


@pytest.fixture
def test_catalog(test_site):
    """Pytest fixture for creating a test item catalog."""
    return ItemCatalog.objects.create(size="Test Size 12oz", workflow=test_site)


def create_test_user(username="testuser", email="test@example.com", password="testpass123"):
    """Helper function to create a test user."""
    return User.objects.create_user(username=username, email=email, password=password)


def create_test_site(domain="test.example.com", name="Test Site"):
    """Helper function to create a test site."""
    return Site.objects.create(domain=domain, name=name)


def create_test_catalog(site, size="Test Size 12oz"):
    """Helper function to create a test item catalog."""
    return ItemCatalog.objects.create(size=size, workflow=site)


class BaseTestCase(TestCase):
    """Base test case with common setup and helper methods."""

    def setUp(self):
        """Set up common test data."""
        super().setUp()
        self.user = create_test_user()
        self.site = create_test_site()
        self.catalog = create_test_catalog(self.site)

    def tearDown(self):
        """Clean up test data."""
        super().tearDown()
        # Add any cleanup logic here if needed


def assert_model_fields(model_instance, expected_fields):
    """
    Assert that a model instance has the expected field values.

    Args:
        model_instance: The model instance to check
        expected_fields: Dict of field_name -> expected_value

    """
    for field_name, expected_value in expected_fields.items():
        actual_value = getattr(model_instance, field_name)
        assert actual_value == expected_value, f"Field '{field_name}' mismatch: expected {expected_value}, got {actual_value}"


def assert_queryset_count(queryset, expected_count):
    """
    Assert that a queryset has the expected number of items.

    Args:
        queryset: The queryset to check
        expected_count: Expected number of items

    """
    actual_count = queryset.count()
    assert actual_count == expected_count, f"Queryset count mismatch: expected {expected_count}, got {actual_count}"


def assert_model_exists(model_class, **kwargs):
    """
    Assert that a model instance exists with the given field values.

    Args:
        model_class: The model class to query
        **kwargs: Field lookups

    """
    exists = model_class.objects.filter(**kwargs).exists()
    assert exists, f"No {model_class.__name__} found with {kwargs}"


def assert_model_not_exists(model_class, **kwargs):
    """
    Assert that no model instance exists with the given field values.

    Args:
        model_class: The model class to query
        **kwargs: Field lookups

    """
    exists = model_class.objects.filter(**kwargs).exists()
    assert not exists, f"Unexpected {model_class.__name__} found with {kwargs}"


def get_or_create_test_data():
    """
    Get or create common test data.

    Returns:
        dict: Dictionary containing test user, site, and catalog

    """
    user, _ = User.objects.get_or_create(
        username="common_test_user",
        defaults={"email": "common@example.com", "password": "testpass123"},
    )

    site, _ = Site.objects.get_or_create(domain="common.example.com", defaults={"name": "Common Test Site"})

    catalog, _ = ItemCatalog.objects.get_or_create(size="Common Size 12oz", defaults={"workflow": site})

    return {"user": user, "site": site, "catalog": catalog}
