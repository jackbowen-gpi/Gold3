"""Test utilities for Item model testing."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.utils import timezone

from gchub_db.apps.workflow.models import (
    Item, Job, ItemCatalog, PrintLocation, PlatePackage, SpecialMfgConfiguration,
    ItemColor, BeverageCenterCode, BeverageLiquidContents, BeverageBrandCode,
    CartonProfile
)


class ItemTestMixin:
    """Mixin providing utilities for Item model testing."""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level test data."""
        super().setUpClass()
    
    def setUp(self):
        """Set up test data for Item tests."""
        super().setUp()
        
        # Create test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test site/workflow
        self.test_site = Site.objects.create(
            name='Test Workflow',
            domain='test.example.com'
        )
        
        # Create test job
        self.test_job = Job.objects.create(
            name='Test Job',
            workflow=self.test_site,
            creation_date=timezone.now(),
            due_date=date.today() + timedelta(days=30),
            brand_name='Test Brand',
            status='active',
            customer_name='Test Customer'
        )
        
        # Create test item catalog
        self.test_item_catalog = ItemCatalog.objects.create(
            name='Test Size',
            width=Decimal('10.5'),
            height=Decimal('8.5'),
            depth=Decimal('2.0')
        )
        
    def create_test_item(self, **kwargs):
        """Create a test Item with default values."""
        defaults = {
            'workflow': self.test_site,
            'job': self.test_job,
            'size': self.test_item_catalog,
            'item_type': 'Test Item Type',
            'item_status': 'Pending',
            'po_number': 'PO12345',
            'path_to_file': '/test/path/file.pdf',
            'upc_number': '123456789012',
            'case_pack': 24,
            'annual_use': 10000,
            'wrin_number': 'WRIN123',
            'sap_number': 'SAP456',
            'bom_number': 'BOM789',
            'description': 'Test item description',
            'material': 'Test material',
            'length': Decimal('10.5'),
            'width': Decimal('8.5'),
            'height': Decimal('2.0'),
            'num_up': 1,
            'num_colors_req': 4,
            'plant_comments': 'Test plant comments'
        }
        
        # Update defaults with any provided kwargs
        defaults.update(kwargs)
        
        return Item.objects.create(**defaults)
    
    def create_beverage_item(self, **kwargs):
        """Create a test Item specifically for beverage workflow."""
        # Set up beverage workflow
        bev_site = Site.objects.create(
            name='Beverage',
            domain='beverage.example.com'
        )
        
        bev_job = Job.objects.create(
            name='Beverage Job',
            workflow=bev_site,
            creation_date=timezone.now(),
            due_date=date.today() + timedelta(days=30),
            brand_name='Beverage Brand',
            status='active',
            customer_name='Beverage Customer'
        )
        
        # Create beverage-specific related objects
        bev_center_code = BeverageCenterCode.objects.create(
            code='TEST',
            name='Test Center Code'
        )
        
        bev_liquid_code = BeverageLiquidContents.objects.create(
            code='COLA',
            name='Cola Beverage'
        )
        
        bev_brand_code = BeverageBrandCode.objects.create(
            code='CC',
            name='Coca Cola'
        )
        
        defaults = {
            'workflow': bev_site,
            'job': bev_job,
            'size': self.test_item_catalog,
            'bev_item_name': 'Test Beverage Item',
            'bev_center_code': bev_center_code,
            'bev_liquid_code': bev_liquid_code,
            'bev_brand_code': bev_brand_code,
            'bev_panel_center': 'Test Panel Center',
            'bev_panel_end': 'Test Panel End',
            'bev_alt_code': 'ALT123'
        }
        
        defaults.update(kwargs)
        return Item.objects.create(**defaults)
    
    def create_fsb_item(self, **kwargs):
        """Create a test Item specifically for FSB workflow."""
        # Set up FSB workflow
        fsb_site = Site.objects.create(
            name='Food Service Board',
            domain='fsb.example.com'
        )
        
        fsb_job = Job.objects.create(
            name='FSB Job',
            workflow=fsb_site,
            creation_date=timezone.now(),
            due_date=date.today() + timedelta(days=30),
            brand_name='FSB Brand',
            status='active',
            customer_name='FSB Customer'
        )
        
        defaults = {
            'workflow': fsb_site,
            'job': fsb_job,
            'size': self.test_item_catalog,
            'fsb_nine_digit': '123456789',
            'fsb_nine_digit_date': date.today(),
            'case_pack': 100,
            'annual_use': 50000,
            'floor_stock': True,
            'replaces': 'OLD123'
        }
        
        defaults.update(kwargs)
        return Item.objects.create(**defaults)


class ItemTestData:
    """Provides test data constants for Item testing."""
    
    # Sample item types
    ITEM_TYPES = [
        'Carton', 'Label', 'Sleeve', 'Wrap', 'Box', 'Container'
    ]
    
    # Sample statuses
    ITEM_STATUSES = [
        'Pending', 'In Progress', 'Proofing', 'Approved', 'Complete', 'On Hold'
    ]
    
    # Sample materials
    MATERIALS = [
        'SBS', 'Kraft', 'Clay Coated', 'White Board', 'Corrugated'
    ]
    
    # Sample UPC numbers
    UPC_NUMBERS = [
        '123456789012', '987654321098', '111222333444', '555666777888'
    ]
    
    # Sample descriptions
    DESCRIPTIONS = [
        'Premium product packaging',
        'Standard retail carton',
        'Economy packaging solution',
        'Custom branded container',
        'Promotional item wrapper'
    ]
    
    @classmethod
    def get_sample_item_data(cls, count=1):
        """Get sample item data for testing."""
        import random
        
        data = []
        for i in range(count):
            data.append({
                'item_type': random.choice(cls.ITEM_TYPES),
                'item_status': random.choice(cls.ITEM_STATUSES),
                'material': random.choice(cls.MATERIALS),
                'upc_number': random.choice(cls.UPC_NUMBERS),
                'description': random.choice(cls.DESCRIPTIONS),
                'po_number': f'PO{random.randint(10000, 99999)}',
                'case_pack': random.randint(12, 144),
                'annual_use': random.randint(1000, 100000),
                'num_colors_req': random.randint(1, 8),
                'length': Decimal(str(random.uniform(5.0, 20.0))),
                'width': Decimal(str(random.uniform(3.0, 15.0))),
                'height': Decimal(str(random.uniform(1.0, 5.0)))
            })
            
        return data if count > 1 else data[0]
    
    @classmethod
    def get_beverage_item_data(cls):
        """Get beverage-specific item data."""
        return {
            'bev_item_name': 'Coca Cola 12oz Can',
            'bev_panel_center': '12 FL OZ (355mL)',
            'bev_panel_end': 'COCA COLA',
            'bev_alt_code': 'CC12',
            'num_colors_req': 6
        }
    
    @classmethod
    def get_fsb_item_data(cls):
        """Get FSB-specific item data."""
        return {
            'fsb_nine_digit': '123456789',
            'case_pack': 100,
            'annual_use': 50000,
            'floor_stock': True,
            'replaces': 'OLD_ITEM_123'
        }
