"""
Unit tests for GOLD3 project.

These tests are fast, isolated, and don't require external dependencies.
They focus on testing individual functions, classes, and methods in isolation.

Usage:
    python run_tests.py --unit
    python -m pytest tests/unit/ -m unit
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from gchub_db.apps.workflow.models import Item, Job, Site, ItemCatalog


class TestItemModelUnit(TestCase):
    """Unit tests for Item model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.site = Site.objects.create(domain="test.example.com", name="Test Site")
        self.catalog = ItemCatalog.objects.create(size="12oz Test Size", workflow=self.site)

    @pytest.mark.unit
    def test_item_creation(self):
        """Test basic item creation."""
        # Create a job first since Item requires a job
        job = Job.objects.create(name="Test Job", workflow=self.site)

        item = Item.objects.create(
            workflow=self.site,
            job=job,
            size=self.catalog,
            item_type="Carton",
            po_number="PO12345",
        )

        assert item.item_type == "Carton"
        assert item.po_number == "PO12345"
        assert item.workflow == self.site
        assert item.job == job

    @pytest.mark.unit
    def test_item_str_representation(self):
        """Test string representation of Item."""
        # Create a job first since Item requires a job
        job = Job.objects.create(name="Test Job", workflow=self.site)

        item = Item.objects.create(
            workflow=self.site,
            job=job,
            size=self.catalog,
            item_type="Carton",
            po_number="PO12345",
        )

        # String representation should be the size name for non-Beverage workflows
        assert str(item) == "12oz Test Size"


class TestJobModelUnit(TestCase):
    """Unit tests for Job model."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.create(domain="test.example.com", name="Test Site")
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.catalog = ItemCatalog.objects.create(size="12oz Test Size", workflow=self.site)

    @pytest.mark.unit
    def test_job_creation(self):
        """Test basic job creation."""
        from datetime import date, timedelta

        job = Job.objects.create(
            name="Test Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        assert job.name == "Test Job"
        assert job.workflow == self.site
        assert job.due_date is not None


class TestUtilityFunctions(TestCase):
    """Unit tests for utility functions."""

    @pytest.mark.unit
    def test_decimal_formatting(self):
        """Test decimal number formatting."""
        value = Decimal("123.45")
        formatted = f"{value:.2f}"

        assert formatted == "123.45"

    @pytest.mark.unit
    def test_string_manipulation(self):
        """Test basic string operations."""
        test_string = "  hello world  "
        cleaned = test_string.strip().title()

        assert cleaned == "Hello World"
