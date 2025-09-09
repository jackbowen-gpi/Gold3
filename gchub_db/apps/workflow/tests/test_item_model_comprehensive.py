"""Comprehensive unit tests for the Item model."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from gchub_db.apps.workflow.models import Item, Job, ItemCatalog
from gchub_db.apps.workflow.tests.item_test_utils import ItemTestMixin, ItemTestData


class ItemModelComprehensiveTests(ItemTestMixin, TestCase):
    """Comprehensive tests for the Item model core functionality."""
    
    def test_item_creation_basic(self):
        """Test basic item creation and string representation."""
        item = self.create_test_item(
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
        
        # Test string representation
        self.assertIsNotNone(str(item))
        self.assertIsNotNone(item.__unicode__())
    
    def test_item_creation_with_dimensions(self):
        """Test item creation with physical dimensions."""
        item = self.create_test_item(
            length=Decimal('12.5'),
            width=Decimal('9.0'),
            height=Decimal('3.25'),
            ect=32
        )
        
        self.assertEqual(item.length, Decimal('12.5'))
        self.assertEqual(item.width, Decimal('9.0'))
        self.assertEqual(item.height, Decimal('3.25'))
        self.assertEqual(item.ect, 32)
    
    def test_item_creation_with_dates(self):
        """Test item creation with various date fields."""
        preflight_date = date.today() + timedelta(days=5)
        proof_date = date.today() + timedelta(days=7)
        delivery_date = date.today() + timedelta(days=10)
        
        item = self.create_test_item(
            preflight_date=preflight_date,
            electronic_proof_date=proof_date,
            file_delivery_date=delivery_date
        )
        
        self.assertEqual(item.preflight_date, preflight_date)
        self.assertEqual(item.electronic_proof_date, proof_date)
        self.assertEqual(item.file_delivery_date, delivery_date)
        self.assertIsNotNone(item.creation_date)
        self.assertIsNotNone(item.last_modified)
    
    def test_item_soft_delete(self):
        """Test that item deletion is soft delete (sets is_deleted=True)."""
        item = self.create_test_item()
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
        
        # Verify item still exists in database
        all_items = Item._base_manager.filter(id=item_id)
        self.assertTrue(all_items.exists())
    
    def test_item_manager_filtering(self):
        """Test that the custom manager filters out deleted items."""
        # Create normal item
        item1 = self.create_test_item(po_number='PO001')
        
        # Create and delete item
        item2 = self.create_test_item(po_number='PO002')
        item2.delete()
        
        # Manager should only return non-deleted items
        active_items = Item.objects.all()
        self.assertEqual(active_items.count(), 1)
        self.assertIn(item1, active_items)
        self.assertNotIn(item2, active_items)
        
        # not_deleted() method should work the same
        not_deleted_items = Item.objects.not_deleted()
        self.assertEqual(not_deleted_items.count(), 1)
        self.assertIn(item1, not_deleted_items)
    
    def test_item_designation_regular_workflow(self):
        """Test get_item_designation for regular workflows."""
        item = self.create_test_item()
        
        # For non-beverage workflows, should return size name
        designation = item.get_item_designation()
        self.assertEqual(designation, self.test_item_catalog.name)
    
    def test_item_absolute_url(self):
        """Test get_absolute_url method."""
        item = self.create_test_item()
        
        url = item.get_absolute_url()
        expected_url = f'/workflow/item/{item.id}/'
        self.assertEqual(url, expected_url)
    
    def test_item_required_fields(self):
        """Test that required fields are enforced."""
        # workflow, job, and size are required
        with self.assertRaises((IntegrityError, ValidationError)):
            item = Item(item_type='Test')
            item.save()
    
    def test_item_boolean_defaults(self):
        """Test that boolean fields have correct defaults."""
        item = self.create_test_item()
        
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
    
    def test_item_ordering(self):
        """Test default ordering of items."""
        # Create items with different num_in_job values
        item1 = self.create_test_item(po_number='PO001')
        item1.num_in_job = 2
        item1.save()
        
        item2 = self.create_test_item(po_number='PO002')
        item2.num_in_job = 1
        item2.save()
        
        # Should be ordered by job, then num_in_job
        items = list(Item.objects.filter(job=self.test_job))
        self.assertEqual(items[0], item2)  # num_in_job = 1
        self.assertEqual(items[1], item1)  # num_in_job = 2
    
    def test_item_relationships(self):
        """Test foreign key relationships."""
        item = self.create_test_item()
        
        # Test job relationship
        self.assertEqual(item.job, self.test_job)
        self.assertIn(item, self.test_job.item_set.all())
        
        # Test workflow relationship
        self.assertEqual(item.workflow, self.test_site)
        
        # Test size relationship
        self.assertEqual(item.size, self.test_item_catalog)
    
    def test_item_status_tracking(self):
        """Test item status field functionality."""
        item = self.create_test_item(item_status='Pending')
        
        # Test initial status
        self.assertEqual(item.item_status, 'Pending')
        
        # Test status change
        item.item_status = 'In Progress'
        item.save()
        
        item.refresh_from_db()
        self.assertEqual(item.item_status, 'In Progress')
    
    def test_item_file_path_handling(self):
        """Test path_to_file field functionality."""
        test_path = '/test/path/to/file.pdf'
        item = self.create_test_item(path_to_file=test_path)
        
        self.assertEqual(item.path_to_file, test_path)
    
    def test_item_color_requirements(self):
        """Test color-related fields."""
        item = self.create_test_item(
            num_colors_req=6,
            upc_ink_color='Black',
            label_color='Red, Blue, Yellow'
        )
        
        self.assertEqual(item.num_colors_req, 6)
        self.assertEqual(item.upc_ink_color, 'Black')
        self.assertEqual(item.label_color, 'Red, Blue, Yellow')
    
    def test_beverage_specific_fields(self):
        """Test beverage-specific field functionality."""
        item = self.create_beverage_item(
            bev_panel_center='12 FL OZ (355mL)',
            bev_panel_end='COCA COLA',
            bev_alt_code='CC12'
        )
        
        self.assertEqual(item.bev_panel_center, '12 FL OZ (355mL)')
        self.assertEqual(item.bev_panel_end, 'COCA COLA')
        self.assertEqual(item.bev_alt_code, 'CC12')
        self.assertIsNotNone(item.bev_center_code)
        self.assertIsNotNone(item.bev_liquid_code)
        self.assertIsNotNone(item.bev_brand_code)
    
    def test_fsb_specific_fields(self):
        """Test FSB-specific field functionality."""
        item = self.create_fsb_item(
            fsb_nine_digit='123456789',
            case_pack=100,
            annual_use=50000,
            floor_stock=True
        )
        
        self.assertEqual(item.fsb_nine_digit, '123456789')
        self.assertEqual(item.case_pack, 100)
        self.assertEqual(item.annual_use, 50000)
        self.assertTrue(item.floor_stock)
    
    def test_item_review_fields(self):
        """Test review-related fields."""
        review_date = date.today()
        item = self.create_test_item(
            plant_review_date=review_date,
            plant_reviewer=self.test_user,
            plant_comments='Looks good',
            mkt_review_date=review_date,
            mkt_review_ok=True,
            mkt_review_comments='Approved',
            mkt_review_needed=True
        )
        
        self.assertEqual(item.plant_review_date, review_date)
        self.assertEqual(item.plant_reviewer, self.test_user)
        self.assertEqual(item.plant_comments, 'Looks good')
        self.assertEqual(item.mkt_review_date, review_date)
        self.assertTrue(item.mkt_review_ok)
        self.assertEqual(item.mkt_review_comments, 'Approved')
        self.assertTrue(item.mkt_review_needed)


class ItemModelEdgeCaseTests(ItemTestMixin, TestCase):
    """Test edge cases and error conditions for the Item model."""
    
    def test_item_with_null_optional_fields(self):
        """Test item creation with null optional fields."""
        item = Item.objects.create(
            workflow=self.test_site,
            job=self.test_job,
            size=self.test_item_catalog
        )
        
        # Check that optional fields can be null
        self.assertIsNone(item.num_in_job)
        self.assertIsNone(item.printlocation)
        self.assertIsNone(item.platepackage)
        self.assertIsNone(item.preflight_date)
        self.assertIsNone(item.electronic_proof_date)
        self.assertIsNone(item.file_delivery_date)
    
    def test_item_with_extreme_dimensions(self):
        """Test item with extreme dimension values."""
        item = self.create_test_item(
            length=Decimal('9999.9999'),
            width=Decimal('0.0001'),
            height=Decimal('5000.0000')
        )
        
        self.assertEqual(item.length, Decimal('9999.9999'))
        self.assertEqual(item.width, Decimal('0.0001'))
        self.assertEqual(item.height, Decimal('5000.0000'))
    
    def test_item_with_negative_numbers(self):
        """Test item behavior with negative numbers where inappropriate."""
        # Negative values should be allowed by model but may be validated elsewhere
        item = self.create_test_item(
            case_pack=-10,
            annual_use=-1000,
            num_colors_req=-1
        )
        
        self.assertEqual(item.case_pack, -10)
        self.assertEqual(item.annual_use, -1000)
        self.assertEqual(item.num_colors_req, -1)
    
    def test_item_with_very_long_text_fields(self):
        """Test item with maximum length text fields."""
        long_description = 'x' * 254  # Just under 255 limit
        long_comments = 'x' * 499    # Just under 500 limit
        
        item = self.create_test_item(
            description=long_description,
            plant_comments=long_comments,
            overdue_exempt_reason=long_comments
        )
        
        self.assertEqual(len(item.description), 254)
        self.assertEqual(len(item.plant_comments), 499)
        self.assertEqual(len(item.overdue_exempt_reason), 499)
    
    def test_item_with_future_dates(self):
        """Test item with dates far in the future."""
        future_date = date.today() + timedelta(days=3650)  # 10 years
        
        item = self.create_test_item(
            preflight_date=future_date,
            electronic_proof_date=future_date,
            file_delivery_date=future_date
        )
        
        self.assertEqual(item.preflight_date, future_date)
        self.assertEqual(item.electronic_proof_date, future_date)
        self.assertEqual(item.file_delivery_date, future_date)
    
    def test_item_with_past_dates(self):
        """Test item with dates in the past."""
        past_date = date.today() - timedelta(days=3650)  # 10 years ago
        
        item = self.create_test_item(
            preflight_date=past_date,
            electronic_proof_date=past_date,
            file_delivery_date=past_date
        )
        
        self.assertEqual(item.preflight_date, past_date)
        self.assertEqual(item.electronic_proof_date, past_date)
        self.assertEqual(item.file_delivery_date, past_date)
    
    def test_item_cascading_deletion(self):
        """Test that deleting related objects affects items properly."""
        item = self.create_test_item()
        item_id = item.id
        
        # Deleting job should delete item (CASCADE)
        self.test_job.delete()
        
        # Item should be gone (hard deleted due to cascade)
        self.assertFalse(Item._base_manager.filter(id=item_id).exists())
    
    def test_item_without_required_foreign_keys(self):
        """Test item creation without required foreign keys."""
        with self.assertRaises((IntegrityError, ValidationError)):
            Item.objects.create(
                workflow=self.test_site,
                # Missing job and size
                item_type='Test'
            )


class ItemModelPerformanceTests(ItemTestMixin, TestCase):
    """Test performance aspects of the Item model."""
    
    def test_bulk_item_creation(self):
        """Test creating multiple items efficiently."""
        items_data = ItemTestData.get_sample_item_data(count=10)
        
        items = []
        for data in items_data:
            item = Item(
                workflow=self.test_site,
                job=self.test_job,
                size=self.test_item_catalog,
                **data
            )
            items.append(item)
        
        # Bulk create
        created_items = Item.objects.bulk_create(items)
        
        self.assertEqual(len(created_items), 10)
        self.assertEqual(Item.objects.filter(job=self.test_job).count(), 10)
    
    def test_item_filtering_performance(self):
        """Test performance of common item filtering operations."""
        # Create multiple items
        for i in range(20):
            self.create_test_item(
                po_number=f'PO{i:04d}',
                item_status='Pending' if i % 2 == 0 else 'Complete'
            )
        
        # Test filtering by status
        pending_items = Item.objects.filter(item_status='Pending')
        self.assertEqual(pending_items.count(), 10)
        
        # Test filtering by job
        job_items = Item.objects.filter(job=self.test_job)
        self.assertEqual(job_items.count(), 20)
        
        # Test complex filtering
        complex_filter = Item.objects.filter(
            job=self.test_job,
            item_status='Pending',
            is_deleted=False
        )
        self.assertEqual(complex_filter.count(), 10)
    
    def test_item_queryset_efficiency(self):
        """Test that item queries are efficient."""
        # Create items with relationships
        for i in range(5):
            self.create_test_item(po_number=f'PO{i:04d}')
        
        # Test select_related efficiency
        items_with_relations = Item.objects.select_related(
            'job', 'workflow', 'size'
        ).filter(job=self.test_job)
        
        # This should not trigger additional queries
        for item in items_with_relations:
            _ = item.job.name
            _ = item.workflow.name
            _ = item.size.name
        
        self.assertEqual(items_with_relations.count(), 5)
