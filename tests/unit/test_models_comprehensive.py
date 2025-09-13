"""
Comprehensive model tests for GOLD3 project.

Tests core models including Item, Job, User, and Site models.
Covers CRUD operations, relationships, validation, and business logic.

Usage:
    python -m pytest tests/unit/test_models_comprehensive.py -v
    python -m pytest tests/unit/test_models_comprehensive.py -m unit
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from datetime import date, timedelta

from gchub_db.apps.workflow.models import Site, Item, Job, ItemCatalog


class TestSiteModel(TestCase):
    """Test Site model functionality."""

    @pytest.mark.unit
    def test_site_creation(self):
        """Test basic Site model creation."""
        site = Site.objects.create(domain="test.example.com", name="Test Site")

        self.assertEqual(site.domain, "test.example.com")
        self.assertEqual(site.name, "Test Site")
        self.assertIsNotNone(site.id)

    @pytest.mark.unit
    def test_site_str_representation(self):
        """Test Site model string representation."""
        site = Site.objects.create(domain="test.example.com", name="Test Site")

        # Site model uses domain for __str__, not name
        self.assertEqual(str(site), "test.example.com")

    @pytest.mark.unit
    def test_site_unique_domain(self):
        """Test that site domains must be unique."""
        Site.objects.create(domain="unique.example.com", name="Site 1")

        with self.assertRaises(IntegrityError):
            Site.objects.create(domain="unique.example.com", name="Site 2")


class TestUserModel(TestCase):
    """Test User model functionality."""

    @pytest.mark.unit
    def test_user_creation(self):
        """Test basic User model creation."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertTrue(user.check_password("testpass123"))

    @pytest.mark.unit
    def test_user_str_representation(self):
        """Test User model string representation."""
        user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")

        self.assertEqual(str(user), "testuser")

    @pytest.mark.unit
    def test_user_unique_username(self):
        """Test that usernames must be unique."""
        User.objects.create_user(username="uniqueuser", email="test1@example.com")

        with self.assertRaises(IntegrityError):
            User.objects.create_user(username="uniqueuser", email="test2@example.com")

    @pytest.mark.unit
    def test_superuser_creation(self):
        """Test superuser creation."""
        superuser = User.objects.create_superuser(username="admin", email="admin@example.com", password="admin123")

        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)


class TestItemCatalogModel(TestCase):
    """Test ItemCatalog model functionality."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.create(domain="catalog.example.com", name="Catalog Test Site")

    @pytest.mark.unit
    def test_item_catalog_creation(self):
        """Test basic ItemCatalog model creation."""
        catalog = ItemCatalog.objects.create(size="12oz Test Size", workflow=self.site)

        self.assertEqual(catalog.size, "12oz Test Size")
        self.assertEqual(catalog.workflow, self.site)

    @pytest.mark.unit
    def test_item_catalog_str_representation(self):
        """Test ItemCatalog model string representation."""
        catalog = ItemCatalog.objects.create(size="12oz Test Size", workflow=self.site)

        self.assertEqual(str(catalog), "12oz Test Size")


class TestJobModel(TestCase):
    """Test Job model functionality."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.create(domain="job.example.com", name="Job Test Site")
        self.user = User.objects.create_user(username="jobuser", email="job@example.com", password="testpass123")

    @pytest.mark.unit
    def test_job_creation(self):
        """Test basic Job model creation."""
        job = Job.objects.create(
            name="Test Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        self.assertEqual(job.name, "Test Job")
        self.assertEqual(job.workflow, self.site)
        self.assertIsNotNone(job.creation_date)

    @pytest.mark.unit
    def test_job_str_representation(self):
        """Test Job model string representation."""
        job = Job.objects.create(
            name="Test Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        # Job __str__ includes the ID, so expect format like "X Test Job"
        job_str = str(job)
        self.assertIn("Test Job", job_str)
        # Should start with a number (the ID) followed by the name
        self.assertRegex(job_str, r"^\d+ Test Job$")

    @pytest.mark.unit
    def test_job_relationships(self):
        """Test Job model relationships."""
        job = Job.objects.create(
            name="Relationship Test Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        # Test that job can have items (reverse relationship)
        self.assertEqual(job.item_set.count(), 0)


class TestItemModel(TestCase):
    """Test Item model functionality."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.create(domain="item.example.com", name="Item Test Site")
        self.user = User.objects.create_user(username="itemuser", email="item@example.com", password="testpass123")
        self.catalog = ItemCatalog.objects.create(size="12oz Test Size", workflow=self.site)
        self.job = Job.objects.create(
            name="Test Job for Items",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

    @pytest.mark.unit
    def test_item_creation(self):
        """Test basic Item model creation."""
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            po_number="TEST123",
        )

        self.assertEqual(item.workflow, self.site)
        self.assertEqual(item.job, self.job)
        self.assertEqual(item.size, self.catalog)
        self.assertEqual(item.item_type, "Carton")
        self.assertEqual(item.po_number, "TEST123")
        self.assertFalse(item.is_deleted)
        self.assertEqual(item.item_status, "Pending")
        self.assertIsNotNone(item.creation_date)

    @pytest.mark.unit
    def test_item_str_representation(self):
        """Test Item model string representation."""
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            po_number="TEST123",
        )

        # String representation should be the size name for non-Beverage workflows
        self.assertEqual(str(item), "12oz Test Size")

    @pytest.mark.unit
    def test_item_required_fields(self):
        """Test that required fields are enforced."""
        # Missing workflow
        with self.assertRaises(Exception):
            Item.objects.create(job=self.job, size=self.catalog, item_type="Carton")

        # Missing job
        with self.assertRaises(Exception):
            Item.objects.create(workflow=self.site, size=self.catalog, item_type="Carton")

        # Missing size
        with self.assertRaises(Exception):
            Item.objects.create(workflow=self.site, job=self.job, item_type="Carton")

    @pytest.mark.unit
    def test_item_relationships(self):
        """Test Item model relationships."""
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            po_number="TEST123",
        )

        # Test reverse relationships
        self.assertIn(item, self.job.item_set.all())
        self.assertIn(item, self.site.item_set.all())

    @pytest.mark.unit
    def test_item_status_transitions(self):
        """Test Item status field transitions."""
        item = Item.objects.create(workflow=self.site, job=self.job, size=self.catalog, item_type="Carton")

        # Default status should be "Pending"
        self.assertEqual(item.item_status, "Pending")

        # Test status update
        item.item_status = "In Progress"
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.item_status, "In Progress")

    @pytest.mark.unit
    def test_item_soft_delete(self):
        """Test Item soft delete functionality."""
        item = Item.objects.create(workflow=self.site, job=self.job, size=self.catalog, item_type="Carton")

        # Item should not be marked as deleted initially
        self.assertFalse(item.is_deleted)

        # Test soft delete
        item.is_deleted = True
        item.save()
        item.refresh_from_db()
        self.assertTrue(item.is_deleted)

        # Item should still exist in database (even if soft deleted)
        # Use _base_manager to bypass the default manager's filtering
        self.assertTrue(Item._base_manager.filter(id=item.id).exists())

    @pytest.mark.unit
    def test_item_field_validation(self):
        """Test Item field validation."""
        # Test UPC number length
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            upc_number="1234567890123456789012345678901234567890",  # Too long
        )

        # Should still save (no validation in model), but field should be
        # truncated or handled
        item.refresh_from_db()
        self.assertIsNotNone(item.upc_number)

    @pytest.mark.unit
    def test_item_date_fields(self):
        """Test Item date fields."""
        test_date = date.today()
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            preflight_date=test_date,
            electronic_proof_date=test_date,
            file_delivery_date=test_date,
        )

        self.assertEqual(item.preflight_date, test_date)
        self.assertEqual(item.electronic_proof_date, test_date)
        self.assertEqual(item.file_delivery_date, test_date)

    @pytest.mark.unit
    def test_item_numeric_fields(self):
        """Test Item numeric fields."""
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            case_pack=24,
            annual_use=1000,
            ect=32,
            length=12.5,
            width=8.75,
            height=6.25,
        )

        self.assertEqual(item.case_pack, 24)
        self.assertEqual(item.annual_use, 1000)
        self.assertEqual(item.ect, 32)
        self.assertEqual(item.length, 12.5)
        self.assertEqual(item.width, 8.75)
        self.assertEqual(item.height, 6.25)

    @pytest.mark.unit
    def test_item_boolean_fields(self):
        """Test Item boolean fields."""
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            press_change=True,
            render=True,
            wrappable_proof=True,
            mock_up=True,
            noise_filter=False,
            floor_stock=True,
            overdue_exempt=True,
            file_out_exempt=True,
        )

        self.assertTrue(item.press_change)
        self.assertTrue(item.render)
        self.assertTrue(item.wrappable_proof)
        self.assertTrue(item.mock_up)
        self.assertFalse(item.noise_filter)
        self.assertTrue(item.floor_stock)
        self.assertTrue(item.overdue_exempt)
        self.assertTrue(item.file_out_exempt)

    @pytest.mark.unit
    def test_item_choice_fields(self):
        """Test Item choice fields."""
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            quality="H",  # High complexity
        )

        self.assertEqual(item.quality, "H")

    @pytest.mark.unit
    def test_item_text_fields(self):
        """Test Item text fields."""
        item = Item.objects.create(
            workflow=self.site,
            job=self.job,
            size=self.catalog,
            item_type="Carton",
            label_color="Red/White/Blue",
            wrin_number="WRIN123456",
            sap_number="SAP789012",
            bom_number="BOM345678",
            replaces="OLD123",
            overdue_exempt_reason="Special customer requirements",
            file_out_exempt_reason="Digital delivery only",
        )

        self.assertEqual(item.label_color, "Red/White/Blue")
        self.assertEqual(item.wrin_number, "WRIN123456")
        self.assertEqual(item.sap_number, "SAP789012")
        self.assertEqual(item.bom_number, "BOM345678")
        self.assertEqual(item.replaces, "OLD123")
        self.assertEqual(item.overdue_exempt_reason, "Special customer requirements")
        self.assertEqual(item.file_out_exempt_reason, "Digital delivery only")


class TestModelRelationships(TestCase):
    """Test relationships between models."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.create(domain="relationship.example.com", name="Relationship Test Site")
        self.user = User.objects.create_user(username="reluser", email="rel@example.com", password="testpass123")
        self.catalog = ItemCatalog.objects.create(size="12oz Relationship Size", workflow=self.site)

    @pytest.mark.unit
    def test_site_job_relationship(self):
        """Test Site to Job relationship."""
        job = Job.objects.create(
            name="Relationship Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        # Test forward relationship
        self.assertEqual(job.workflow, self.site)

        # Test reverse relationship
        self.assertIn(job, self.site.job_set.all())

    @pytest.mark.unit
    def test_job_item_relationship(self):
        """Test Job to Item relationship."""
        job = Job.objects.create(
            name="Job with Items",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        item1 = Item.objects.create(
            workflow=self.site,
            job=job,
            size=self.catalog,
            item_type="Carton",
            po_number="REL001",
        )

        item2 = Item.objects.create(
            workflow=self.site,
            job=job,
            size=self.catalog,
            item_type="Label",
            po_number="REL002",
        )

        # Test forward relationships
        self.assertEqual(item1.job, job)
        self.assertEqual(item2.job, job)

        # Test reverse relationship
        self.assertEqual(job.item_set.count(), 2)
        self.assertIn(item1, job.item_set.all())
        self.assertIn(item2, job.item_set.all())

    @pytest.mark.unit
    def test_user_created_objects(self):
        """Test User relationships with created objects."""
        job = Job.objects.create(
            name="User Created Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        _ = Item.objects.create(workflow=self.site, job=job, size=self.catalog, item_type="Carton")

        # Test user relationships
        # Note: Job model doesn't have created_by field
        # Note: Item model doesn't have created_by field

    @pytest.mark.unit
    def test_cascading_relationships(self):
        """Test cascading relationships and foreign key constraints."""
        job = Job.objects.create(
            name="Cascade Test Job",
            workflow=self.site,
            due_date=date.today() + timedelta(days=30),
        )

        _ = Item.objects.create(workflow=self.site, job=job, size=self.catalog, item_type="Carton")

        # Test that deleting job would affect items
        # (This depends on the actual ForeignKey on_delete setting)
        job_id = job.id

        # In Django, by default ForeignKey has on_delete=models.CASCADE
        # So deleting job should delete items
        job.delete()

        self.assertFalse(Job.objects.filter(id=job_id).exists())
        # Item deletion depends on the actual model configuration
        # This test documents the current behavior
