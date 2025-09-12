"""
Integration tests for GOLD3 project.

These tests verify that different components work together correctly.
They may be slower and can require database connections and external services.

Usage:
    python run_tests.py --integration
    python -m pytest tests/integration/ -m integration
"""

import pytest
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User

from gchub_db.apps.workflow.models import Item, Job, Site, ItemCatalog


class TestWorkflowIntegration(TransactionTestCase):
    """Integration tests for workflow functionality."""

    def setUp(self):
        """Set up integration test data."""
        # Create test user
        self.user = User.objects.create_user(
            username="integration_user",
            email="integration@example.com",
            password="testpass123",
        )

        # Create test site
        self.site = Site.objects.create(
            domain="integration.example.com", name="Integration Test Site"
        )

        # Create test item catalog
        self.catalog = ItemCatalog.objects.create(
            size="Integration Size 12oz", workflow=self.site
        )

    @pytest.mark.integration
    def test_complete_workflow_creation(self):
        """Test creating a complete workflow with all related objects."""
        from datetime import date, timedelta

        # Create job
        job = Job.objects.create(
            name="Integration Test Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        # Create item linked to job
        item = Item.objects.create(
            workflow=self.site,
            job=job,
            size=self.catalog,
            item_type="Carton",
            po_number="INT12345",
        )

        # Verify relationships
        assert item.job == job
        assert item.workflow == self.site
        assert item.size == self.catalog

        # Verify job has item
        assert job.item_set.count() == 1
        assert job.item_set.first() == item

    @pytest.mark.integration
    def test_bulk_item_creation(self):
        """Test creating multiple items efficiently."""
        from datetime import date, timedelta

        # Create job
        job = Job.objects.create(
            name="Bulk Test Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        # Create multiple items
        items_data = [
            {"item_type": "Carton", "po_number": f"PO{i:03d}"} for i in range(1, 11)
        ]  # Create 10 items

        items = []
        for data in items_data:
            item = Item.objects.create(
                workflow=self.site, job=job, size=self.catalog, **data
            )
            items.append(item)

        # Verify bulk creation
        assert len(items) == 10
        assert job.item_set.count() == 10

        # Verify all items belong to the job
        for item in items:
            assert item.job == job
            assert item.workflow == self.site


class TestDatabaseIntegration(TransactionTestCase):
    """Integration tests for database operations."""

    def setUp(self):
        """Set up integration test data."""
        # Create test user
        self.user = User.objects.create_user(
            username="db_integration_user",
            email="db_integration@example.com",
            password="testpass123",
        )

        # Create test site
        self.site = Site.objects.create(
            domain="db_integration.example.com", name="Database Integration Test Site"
        )

        # Create test item catalog
        self.catalog = ItemCatalog.objects.create(
            size="DB Integration Size 12oz", workflow=self.site
        )

    @pytest.mark.integration
    def test_database_constraints(self):
        """Test database constraints and relationships."""
        from django.db import IntegrityError

        # Test that required fields are enforced
        with pytest.raises(IntegrityError):
            Item.objects.create(
                item_type="Carton"
                # Missing required workflow field
            )

    @pytest.mark.integration
    def test_cascading_deletes(self):
        """Test cascading delete behavior."""
        from datetime import date, timedelta

        # Create related objects
        job = Job.objects.create(
            name="Cascade Test Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        _ = Item.objects.create(
            workflow=self.site,
            job=job,
            size=self.catalog,
            item_type="Carton",
            po_number="CASCADE123",
        )

        # Delete job and verify item is also deleted (if cascade is set up)
        job_id = job.id

        job.delete()

        # Check if items were deleted based on your model relationships
        assert not Job.objects.filter(id=job_id).exists()
        # Note: Whether items are deleted depends on your ForeignKey on_delete setting


class TestManagementCommandsIntegration(TestCase):
    """Integration tests for Django management commands."""

    @pytest.mark.integration
    def test_management_command_execution(self):
        """Test that management commands can be executed."""
        # This is a placeholder - replace with actual management commands
        # that should be tested
        try:
            # Example: test a custom management command
            # call_command('your_custom_command', verbosity=0)
            pass
        except Exception as e:
            self.fail(f"Management command failed: {e}")
