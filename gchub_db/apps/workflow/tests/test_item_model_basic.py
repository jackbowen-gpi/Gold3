"""Simple working tests for the Item model."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from gchub_db.apps.workflow.models import Item, Job, Site, ItemCatalog


class ItemModelBasicTests(TestCase):
    """Basic tests for the Item model that should work."""
    
    def setUp(self):
        """Set up basic test data."""
        # Create test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test site
        self.test_site = Site.objects.create(
            domain='test.example.com',
            name='Test Site'
        )
        
        # Create test item catalog
        self.test_item_catalog = ItemCatalog.objects.create(
            size='Test Size 12oz',
            workflow=self.test_site
        )
        
        # Create test job
        self.test_job = Job.objects.create(
            name='Test Job',
            workflow=self.test_site,
            due_date=date.today() + timedelta(days=30)
        )
    
    def test_item_creation_basic(self):
        """Test basic item creation."""
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Carton',
            po_number='PO12345'
        )
        
        self.assertIsInstance(item, Item)
        self.assertEqual(item.job, self.test_job)
        self.assertEqual(item.workflow, self.test_site)
        self.assertEqual(item.size, self.test_item_catalog)
        self.assertEqual(item.item_type, 'Carton')
        self.assertEqual(item.po_number, 'PO12345')
        self.assertFalse(item.is_deleted)
    
    def test_item_string_representation(self):
        """Test item string representation."""
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Test Item'
        )
        
        # Test string representation
        self.assertIsNotNone(str(item))
        self.assertIsNotNone(item.__unicode__())
    
    def test_item_with_dimensions(self):
        """Test item creation with dimensions."""
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Carton',
            length=Decimal('12.5'),
            width=Decimal('9.0'),
            height=Decimal('3.25'),
            ect=32
        )
        
        self.assertEqual(item.length, Decimal('12.5'))
        self.assertEqual(item.width, Decimal('9.0'))
        self.assertEqual(item.height, Decimal('3.25'))
        self.assertEqual(item.ect, 32)
    
    def test_item_soft_delete(self):
        """Test that item deletion is soft delete."""
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Test Item'
        )
        item_id = item.id
        
        # Verify item exists
        self.assertTrue(Item.objects.filter(id=item_id).exists())
        
        # Delete item
        item.delete()
        
        # Verify item is soft deleted
        item.refresh_from_db()
        self.assertTrue(item.is_deleted)
        
        # Verify item is filtered out by default manager
        self.assertFalse(Item.objects.filter(id=item_id).exists())
    
    def test_item_absolute_url(self):
        """Test get_absolute_url method."""
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Test Item'
        )
        
        url = item.get_absolute_url()
        # get_absolute_url returns the job detail URL, not item URL
        # The actual implementation returns reverse("job_detail", args=[self.num_in_job])
        self.assertIsNotNone(url)
        self.assertIn('/workflow/job/', url)
    
    def test_item_boolean_defaults(self):
        """Test that boolean fields have correct defaults."""
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Test Item'
        )
        
        self.assertFalse(item.is_deleted)
        self.assertFalse(item.preflight_ok)
        self.assertFalse(item.press_change)
        self.assertFalse(item.render)
        self.assertFalse(item.wrappable_proof)
        self.assertFalse(item.mock_up)
        self.assertTrue(item.noise_filter)  # Default True
        self.assertFalse(item.floor_stock)
        self.assertFalse(item.overdue_exempt)
        self.assertFalse(item.file_out_exempt)
    
    def test_item_with_dates(self):
        """Test item creation with date fields."""
        preflight_date = date.today() + timedelta(days=5)
        proof_date = date.today() + timedelta(days=7)
        delivery_date = date.today() + timedelta(days=10)
        
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Test Item',
            preflight_date=preflight_date,
            electronic_proof_date=proof_date,
            file_delivery_date=delivery_date
        )
        
        self.assertEqual(item.preflight_date, preflight_date)
        self.assertEqual(item.electronic_proof_date, proof_date)
        self.assertEqual(item.file_delivery_date, delivery_date)
        self.assertIsNotNone(item.creation_date)
        self.assertIsNotNone(item.last_modified)
    
    def test_item_manager_filtering(self):
        """Test that the custom manager filters out deleted items."""
        # Create normal item
        item1 = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Item 1',
            po_number='PO001'
        )
        
        # Create and delete item
        item2 = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Item 2',
            po_number='PO002'
        )
        item2.delete()
        
        # Manager should only return non-deleted items
        active_items = Item.objects.all()
        self.assertEqual(active_items.count(), 1)
        self.assertIn(item1, active_items)
        self.assertNotIn(item2, active_items)
    
    def test_item_relationships(self):
        """Test foreign key relationships."""
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog,
            item_type='Test Item'
        )
        
        # Test job relationship
        self.assertEqual(item.job, self.test_job)
        self.assertIn(item, self.test_job.item_set.all())
        
        # Test workflow relationship
        self.assertEqual(item.workflow, self.test_site)
        
        # Test size relationship
        self.assertEqual(item.size, self.test_item_catalog)
