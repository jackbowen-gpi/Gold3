"""Simplified test utilities for Item model testing."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User

from gchub_db.apps.workflow.models import Item, Job, Site, ItemCatalog


class ItemTestMixin:
    """Mixin providing test setup and utilities for Item model tests."""

    def setUp(self):
        """Set up basic test data."""
        # Create test user
        self.test_user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")

        # Create test site (workflow)
        self.test_site = Site.objects.create(name="Test Site", full_name="Test Site Full Name", active=True)

        # Create test item catalog (size)
        self.test_item_catalog = ItemCatalog.objects.create(
            name="Test Size",
            min_length=Decimal("10.0"),
            max_length=Decimal("20.0"),
            min_width=Decimal("8.0"),
            max_width=Decimal("15.0"),
            min_height=Decimal("2.0"),
            max_height=Decimal("6.0"),
        )

        # Create test job
        self.test_job = Job.objects.create(
            name="Test Job",
            workflow=self.test_site,
            creator=self.test_user,
            quantity=1000,
            due_date=date.today() + timedelta(days=30),
        )

    def create_test_item(self, **kwargs):
        """Create a test item with default values."""
        defaults = {
            "workflow": self.test_site,
            "job": self.test_job,
            "size": self.test_item_catalog,
            "item_type": "Test Item",
            "po_number": "PO12345",
            "is_deleted": False,
        }
        defaults.update(kwargs)

        return Item.objects.create(**defaults)

    def create_beverage_item(self, **kwargs):
        """Create a test beverage item with beverage-specific fields."""
        beverage_defaults = {
            "bev_panel_center": "12 FL OZ",
            "bev_panel_end": "TEST BRAND",
            "bev_alt_code": "TB12",
            "bev_item_name": "Test Beverage Item",
        }
        beverage_defaults.update(kwargs)

        return self.create_test_item(**beverage_defaults)

    def create_fsb_item(self, **kwargs):
        """Create a test FSB item with FSB-specific fields."""
        fsb_defaults = {
            "fsb_nine_digit": "123456789",
            "case_pack": 24,
            "annual_use": 10000,
        }
        fsb_defaults.update(kwargs)

        return self.create_test_item(**fsb_defaults)


class ItemTestData:
    """Static test data for Item model testing."""

    @staticmethod
    def get_sample_item_data(count=1):
        """Return sample item data for testing."""
        sample_data = []

        for i in range(count):
            data = {
                "item_type": f"Test Item {i + 1}",
                "po_number": f"PO{i + 1:04d}",
                "description": f"Test item description {i + 1}",
                "length": Decimal("12.5"),
                "width": Decimal("9.0"),
                "height": Decimal("3.25"),
                "ect": 32,
                "num_colors_req": 4,
                "item_status": "Pending" if i % 2 == 0 else "Complete",
            }
            sample_data.append(data)

        return sample_data

    @staticmethod
    def get_beverage_test_data():
        """Return beverage-specific test data."""
        return {
            "bev_panel_center": "12 FL OZ (355mL)",
            "bev_panel_end": "COCA COLA",
            "bev_alt_code": "CC12",
            "bev_item_name": "Coca Cola 12oz Can",
            "bev_panel_description": "Classic Coca Cola",
        }

    @staticmethod
    def get_fsb_test_data():
        """Return FSB-specific test data."""
        return {
            "fsb_nine_digit": "123456789",
            "case_pack": 100,
            "annual_use": 50000,
            "floor_stock": True,
        }
