"""Integration tests for the Item model with other system components."""

from datetime import date

from django.db import transaction
from django.test import TestCase

from gchub_db.apps.workflow.models import Item, Job
from gchub_db.apps.workflow.tests.item_test_utils import ItemTestMixin


class ItemModelIntegrationTests(TestCase, ItemTestMixin):
    """Integration tests for Item model with other system components."""

    def setUp(self):
        super().setUp()

    def test_item_job_relationship_integrity(self):
        """Test the integrity of item-job relationships."""
        # Create multiple items for the same job
        item1 = self.create_test_item(po_number="PO001")
        item2 = self.create_test_item(po_number="PO002")
        item3 = self.create_test_item(po_number="PO003")

        # Verify job has all items
        job_items = self.test_job.item_set.all()
        self.assertEqual(job_items.count(), 3)
        self.assertIn(item1, job_items)
        self.assertIn(item2, job_items)
        self.assertIn(item3, job_items)

        # Test reverse relationship
        for item in [item1, item2, item3]:
            self.assertEqual(item.job, self.test_job)

    def test_item_workflow_site_relationship_integrity(self):
        """Test the integrity of item-workflow site relationships."""
        item = self.create_test_item()

        # Item workflow should match job workflow
        self.assertEqual(item.workflow, item.job.workflow)
        self.assertEqual(item.workflow, self.test_site)

    def test_item_deletion_cascade_behavior(self):
        """Test item deletion and its effects on related objects."""
        item = self.create_test_item()
        item_id = item.id

        # Soft delete item
        item.delete()

        # Item should be soft deleted
        self.assertTrue(Item._base_manager.get(id=item_id).is_deleted)

        # Item should not appear in normal queries
        self.assertFalse(Item.objects.filter(id=item_id).exists())

        # Job should still exist
        self.assertTrue(Job.objects.filter(id=self.test_job.id).exists())

    def test_item_with_different_workflows(self):
        """Test items in different workflow contexts."""
        # Create beverage item
        bev_item = self.create_beverage_item()

        # Create FSB item
        fsb_item = self.create_fsb_item()

        # Create regular item
        regular_item = self.create_test_item()

        # Each should have appropriate workflow
        self.assertEqual(bev_item.workflow.name, "Beverage")
        self.assertEqual(fsb_item.workflow.name, "Food Service Board")
        self.assertEqual(regular_item.workflow.name, "Test Workflow")

        # String representations should work for all
        self.assertIsNotNone(str(bev_item))
        self.assertIsNotNone(str(fsb_item))
        self.assertIsNotNone(str(regular_item))

    def test_item_beverage_nomenclature_integration(self):
        """Test beverage nomenclature functionality."""
        bev_item = self.create_beverage_item(bev_item_name="Coca Cola 12oz Can")

        # Test that beverage items use bev_item_name for designation
        designation = bev_item.get_item_designation()
        self.assertEqual(designation, "Coca Cola 12oz Can")

        # Test string representation uses designation
        item_str = str(bev_item)
        self.assertEqual(item_str, "Coca Cola 12oz Can")

    def test_item_status_workflow_integration(self):
        """Test item status changes and their effects on workflow."""
        item = self.create_test_item(item_status="Pending")

        # Test status progression
        statuses = ["Pending", "In Progress", "Proofing", "Approved", "Complete"]

        for status in statuses:
            item.item_status = status
            item.save()

            item.refresh_from_db()
            self.assertEqual(item.item_status, status)

    def test_item_date_tracking_integration(self):
        """Test date field tracking and relationships."""
        item = self.create_test_item()
        creation_time = item.creation_date
        last_modified_time = item.last_modified

        # Modify item
        item.item_status = "Updated"
        item.save()

        item.refresh_from_db()

        # Creation date should not change
        self.assertEqual(item.creation_date, creation_time)

        # Last modified should update
        self.assertGreater(item.last_modified, last_modified_time)

    def test_item_search_and_filtering_integration(self):
        """Test item search functionality with realistic data."""
        # Create items with various attributes
        items_data = [
            {"po_number": "PO001", "item_status": "Pending", "material": "SBS"},
            {"po_number": "PO002", "item_status": "Complete", "material": "Kraft"},
            {"po_number": "PO003", "item_status": "Pending", "material": "SBS"},
            {
                "po_number": "PO004",
                "item_status": "In Progress",
                "material": "Clay Coated",
            },
        ]

        created_items = []
        for data in items_data:
            item = self.create_test_item(**data)
            created_items.append(item)

        # Test filtering by status
        pending_items = Item.objects.filter(item_status="Pending")
        self.assertEqual(pending_items.count(), 2)

        # Test filtering by material
        sbs_items = Item.objects.filter(material="SBS")
        self.assertEqual(sbs_items.count(), 2)

        # Test complex filtering
        pending_sbs = Item.objects.filter(item_status="Pending", material="SBS")
        self.assertEqual(pending_sbs.count(), 2)

        # Test search by PO number
        po001_items = Item.objects.filter(po_number="PO001")
        self.assertEqual(po001_items.count(), 1)

    def test_item_bulk_operations_integrity(self):
        """Test that bulk operations maintain data integrity."""
        # Create multiple items
        items = []
        for i in range(10):
            item = Item(
                workflow=self.test_site,
                job=self.test_job,
                size=self.test_item_catalog,
                po_number=f"PO{i:04d}",
                item_status="Pending",
            )
            items.append(item)

        # Bulk create
        Item.objects.bulk_create(items)

        # Verify all created
        self.assertEqual(Item.objects.filter(job=self.test_job).count(), 10)

        # Bulk update
        Item.objects.filter(job=self.test_job).update(item_status="Updated")

        # Verify all updated
        updated_count = Item.objects.filter(job=self.test_job, item_status="Updated").count()
        self.assertEqual(updated_count, 10)

    def test_item_user_relationship_tracking(self):
        """Test item relationships with users (plant_reviewer)."""
        item = self.create_test_item(
            plant_reviewer=self.test_user,
            plant_review_date=date.today(),
            plant_comments="Review completed",
        )

        # Test user relationship
        self.assertEqual(item.plant_reviewer, self.test_user)

        # Test reverse relationship
        reviewed_items = Item.objects.filter(plant_reviewer=self.test_user)
        self.assertIn(item, reviewed_items)

    def test_item_creation_with_related_objects(self):
        """Test item creation with various related objects."""
        item = self.create_test_item(printlocation=self.test_print_location)

        # Test that related objects are properly linked
        self.assertEqual(item.printlocation, self.test_print_location)
        self.assertEqual(item.size, self.test_item_catalog)

        # Test that item appears in related object queries
        location_items = Item.objects.filter(printlocation=self.test_print_location)
        self.assertIn(item, location_items)

    def test_item_beverage_specific_integration(self):
        """Test beverage-specific functionality integration."""
        bev_item = self.create_beverage_item()

        # Test beverage-specific fields
        self.assertIsNotNone(bev_item.bev_center_code)
        self.assertIsNotNone(bev_item.bev_liquid_code)
        self.assertIsNotNone(bev_item.bev_brand_code)

        # Test beverage nomenclature
        self.assertIsNotNone(bev_item.bev_item_name)

        # Verify workflow context
        self.assertEqual(bev_item.workflow.name, "Beverage")

    def test_item_fsb_specific_integration(self):
        """Test FSB-specific functionality integration."""
        fsb_item = self.create_fsb_item()

        # Test FSB-specific fields
        self.assertIsNotNone(fsb_item.fsb_nine_digit)
        self.assertTrue(fsb_item.floor_stock)

        # Verify workflow context
        self.assertEqual(fsb_item.workflow.name, "Food Service Board")


class ItemModelConcurrencyTests(TestCase, ItemTestMixin):
    """Test concurrent access and race condition scenarios."""

    def setUp(self):
        super().setUp()

    def test_concurrent_item_updates(self):
        """Test handling of concurrent item updates."""
        item = self.create_test_item(item_status="Pending")

        # Simulate concurrent access
        item1 = Item.objects.get(id=item.id)
        item2 = Item.objects.get(id=item.id)

        # Both update different fields
        item1.item_status = "In Progress"
        item1.save()

        item2.plant_comments = "Updated comments"
        item2.save()

        # Verify both updates persisted
        final_item = Item.objects.get(id=item.id)
        self.assertEqual(final_item.item_status, "In Progress")
        self.assertEqual(final_item.plant_comments, "Updated comments")

    def test_item_creation_uniqueness(self):
        """Test item creation uniqueness handling."""
        # Create multiple items - should all succeed
        items = []
        for i in range(5):
            item = self.create_test_item(po_number=f"PO{i:04d}")
            items.append(item)

        # All should be unique
        item_ids = [item.id for item in items]
        self.assertEqual(len(item_ids), len(set(item_ids)))

    def test_item_deletion_concurrent_access(self):
        """Test concurrent access during item deletion."""
        item = self.create_test_item()
        item_id = item.id

        # Get two references
        item1 = Item.objects.get(id=item_id)
        item2 = Item.objects.get(id=item_id)

        # Delete through one reference
        item1.delete()

        # Verify other reference reflects deletion
        item2.refresh_from_db()
        self.assertTrue(item2.is_deleted)


class ItemModelTransactionTests(TestCase, ItemTestMixin):
    """Test transaction behavior with items."""

    def setUp(self):
        super().setUp()

    def test_item_creation_transaction_integrity(self):
        """Test item creation in transaction scenarios."""
        initial_count = Item.objects.count()

        try:
            with transaction.atomic():
                # Create item
                self.create_test_item()

                # Verify it exists within transaction
                self.assertEqual(Item.objects.count(), initial_count + 1)

                # Force rollback
                raise Exception("Force rollback")

        except Exception:
            pass

        # Verify rollback occurred
        self.assertEqual(Item.objects.count(), initial_count)

    def test_item_creation_rollback_scenario(self):
        """Test item creation rollback behavior."""
        initial_count = Item.objects.count()

        with self.assertRaises(Exception):
            with transaction.atomic():
                # Create multiple items
                self.create_test_item(po_number="PO001")
                self.create_test_item(po_number="PO002")

                # Verify they exist within transaction
                self.assertEqual(Item.objects.count(), initial_count + 2)

                # Force an error
                raise Exception("Test rollback")

        # Verify all rolled back
        self.assertEqual(Item.objects.count(), initial_count)

    def test_item_bulk_operation_transaction(self):
        """Test bulk operations within transactions."""
        initial_count = Item.objects.count()

        with transaction.atomic():
            # Bulk create items
            items = []
            for i in range(5):
                item = Item(
                    workflow=self.test_site,
                    job=self.test_job,
                    size=self.test_item_catalog,
                    po_number=f"PO{i:04d}",
                )
                items.append(item)

            Item.objects.bulk_create(items)

            # Verify count within transaction
            self.assertEqual(Item.objects.count(), initial_count + 5)

        # Verify commit occurred
        self.assertEqual(Item.objects.count(), initial_count + 5)
