"""
Integration tests for Job model interactions with other components.
Tests the Job model in realistic scenarios with other models and systems.
"""

from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase, TransactionTestCase
from django.db import transaction
from django.utils import timezone

from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models.job import Job
from .job_test_utils import JobTestMixin


class JobModelIntegrationTests(TestCase, JobTestMixin):
    """Integration tests for Job model with other system components."""

    def setUp(self):
        """Set up test data."""
        self.user = self.create_test_user()
        self.site = self.create_test_site()

    def test_job_creation_with_joblog_integration(self):
        """Test that job creation properly integrates with job logging."""
        initial_log_count = JobLog.objects.count()

        job = self.create_test_job(name="Integration Job")

        # Should have created a job log entry
        final_log_count = JobLog.objects.count()
        self.assertEqual(final_log_count, initial_log_count + 1)

        # Verify the log entry details
        job_logs = JobLog.objects.filter(job=job)
        self.assertTrue(job_logs.exists())

        log = job_logs.first()
        self.assertEqual(log.job, job)

    def test_job_workflow_site_relationship_integrity(self):
        """Test the integrity of job-site relationships."""
        # Create multiple sites and jobs
        sites = [self.create_test_site() for _ in range(3)]
        jobs_per_site = 2

        all_jobs = []
        for site in sites:
            for i in range(jobs_per_site):
                job = self.create_test_job(name=f"Site {site.id} Job {i + 1}", workflow=site)
                all_jobs.append(job)

        # Verify relationships are correct
        for i, site in enumerate(sites):
            site_jobs = Job.objects.filter(workflow=site)
            self.assertEqual(site_jobs.count(), jobs_per_site)

            for job in site_jobs:
                self.assertEqual(job.workflow, site)

    def test_job_user_relationship_tracking(self):
        """Test job relationships with users (created_by, modified_by)."""
        user1 = self.create_test_user()
        user2 = self.create_test_user()

        # Mock threadlocals for user tracking
        with patch("gchub_db.middleware.threadlocals.get_current_user", return_value=user1):
            job = self.create_test_job(name="User Tracked Job")

            # Check if created_by is set (if field exists)
            if hasattr(job, "created_by"):
                self.assertEqual(job.created_by, user1)

        # Update job as different user
        with patch("gchub_db.middleware.threadlocals.get_current_user", return_value=user2):
            job.name = "Updated Job Name"
            job.save()
            job.refresh_from_db()

            # Check if last_modified_by is updated
            if hasattr(job, "last_modified_by"):
                self.assertEqual(job.last_modified_by, user2)

    def test_job_status_workflow_integration(self):
        """Test job status changes and their effects on workflow."""
        job = self.create_test_job(status="Pending")

        # Mock items completion
        job.all_items_complete = Mock(return_value=True)

        # Perform status update
        job.do_status_update()
        job.refresh_from_db()

        # Verify status changed and flags set
        self.assertEqual(job.status, "Complete")
        self.assertTrue(job.needs_etools_update)

    def test_job_bulk_operations_integrity(self):
        """Test that bulk operations maintain data integrity."""
        # Create multiple jobs
        jobs_data = []
        for i in range(10):
            jobs_data.append(
                {
                    "name": f"Bulk Job {i + 1}",
                    "workflow": self.site,
                    "brand_name": f"Brand {i + 1}",
                    "status": "Active" if i % 2 == 0 else "Pending",
                }
            )

        jobs = []
        for data in jobs_data:
            jobs.append(Job(**data))

        Job.objects.bulk_create(jobs)

        # Verify all jobs were created correctly
        created_jobs = Job.objects.filter(workflow=self.site, name__startswith="Bulk Job")
        self.assertEqual(created_jobs.count(), 10)

        # Verify relationships are intact
        for job in created_jobs:
            self.assertEqual(job.workflow, self.site)
            self.assertIn(job.status, ["Active", "Pending"])

    def test_job_deletion_cascade_behavior(self):
        """Test job deletion and its effects on related objects."""
        job = self.create_test_job()
        job_id = job.id

        # Mock delete_folder to avoid filesystem operations
        job.delete_folder = Mock()

        # Delete the job (soft delete)
        job.delete()
        job.refresh_from_db()

        # Verify soft delete behavior
        self.assertTrue(job.is_deleted)
        job.delete_folder.assert_called_once()

        # Job should still exist in database
        self.assertTrue(Job.objects.filter(id=job_id).exists())

    def test_job_search_and_filtering_integration(self):
        """Test job search functionality with realistic data."""
        # Create jobs with different characteristics
        test_jobs = [
            {"name": "Website Project", "brand_name": "TechCorp", "status": "Active"},
            {"name": "Mobile App", "brand_name": "StartupInc", "status": "Pending"},
            {
                "name": "Database Migration",
                "brand_name": "TechCorp",
                "status": "Complete",
            },
            {"name": "API Development", "brand_name": "Enterprise", "status": "Active"},
        ]

        created_jobs = []
        for job_data in test_jobs:
            job_data["workflow"] = self.site
            job = self.create_test_job(**job_data)
            created_jobs.append(job)

        # Test name-based search
        website_jobs = Job.objects.filter(name__icontains="Website")
        self.assertEqual(website_jobs.count(), 1)
        self.assertEqual(website_jobs.first().name, "Website Project")

        # Test brand-based search
        techcorp_jobs = Job.objects.filter(brand_name="TechCorp")
        self.assertEqual(techcorp_jobs.count(), 2)

        # Test status-based filtering
        active_jobs = Job.objects.filter(status="Active", workflow=self.site)
        self.assertEqual(active_jobs.count(), 2)

        # Test complex filtering
        active_techcorp = Job.objects.filter(status="Active", brand_name="TechCorp", workflow=self.site)
        self.assertEqual(active_techcorp.count(), 1)

    def test_job_date_calculations_integration(self):
        """Test date calculations in different site contexts."""
        # Create different types of sites
        food_site = self.create_test_site(name="Food Processing")
        regular_site = self.create_test_site(name="Regular Site")

        # Test date calculation for food site
        food_job = self.create_test_job(workflow=food_site)
        friday = date(2025, 8, 29)  # A Friday
        food_job.due_date = friday
        food_job.calculate_real_due_date()

        # For food sites, Friday should be moved to Thursday
        expected_date = friday - timedelta(days=1)
        self.assertEqual(food_job.real_due_date, expected_date)

        # Test date calculation for regular site
        regular_job = self.create_test_job(workflow=regular_site)
        saturday = date(2025, 8, 30)  # A Saturday
        regular_job.due_date = saturday
        regular_job.calculate_real_due_date()

        # Should move Saturday back to Friday
        expected_regular = saturday - timedelta(days=1)
        self.assertEqual(regular_job.real_due_date, expected_regular)

    def test_job_creation_date_ordering_integration(self):
        """Test job ordering by creation date."""
        # Create jobs with different creation dates
        jobs = []
        base_date = timezone.now() - timedelta(days=5)

        for i in range(5):
            job = self.create_test_job(name=f"Job {i + 1}", creation_date=base_date + timedelta(days=i))
            jobs.append(job)

        # Test ordering by creation date
        ordered_jobs = Job.objects.filter(workflow=self.site).order_by("creation_date")
        ordered_dates = [job.creation_date for job in ordered_jobs]

        # Verify they are in chronological order
        for i in range(len(ordered_dates) - 1):
            self.assertLessEqual(ordered_dates[i], ordered_dates[i + 1])

    def test_job_status_calculations_integration(self):
        """Test status-related calculations and validations."""
        job = self.create_test_job(name="Test Job", status="active")

        # Test status validation
        self.assertIn(job.status, ["draft", "active", "completed", "cancelled", "on_hold"])

        # Test status change
        job.status = "completed"
        job.save()

        # Verify status was updated
        updated_job = Job.objects.get(id=job.id)
        self.assertEqual(updated_job.status, "completed")

    def test_job_keyword_generation_integration(self):
        """Test keyword generation with realistic job data."""
        job = self.create_test_job(
            name="Website Redesign Project",
            brand_name="TechCorp Industries",
            customer_name="Important Client",
        )

        # Clear and regenerate keywords
        job.generated_keywords = ""
        job.save()
        job.refresh_from_db()

        # Verify keywords contain relevant terms
        keywords_lower = job.generated_keywords.lower()
        expected_terms = ["website", "redesign", "project", "techcorp", "industries"]

        for term in expected_terms:
            self.assertIn(term, keywords_lower)

    def test_job_icon_url_integration(self):
        """Test icon URL generation for different site types."""
        # Test different site types
        site_configs = [
            ("beverage", "bullet_green.png"),
            ("carton", "bullet_purple.png"),
            ("regular", "bullet_black.png"),
        ]

        for site_type, expected_icon in site_configs:
            site = self.create_test_site(name=f"{site_type.title()} Site")
            job = self.create_test_job(workflow=site)

            icon_url = job.get_icon_url()
            self.assertIn(expected_icon, icon_url)

    def test_job_completion_status_integration(self):
        """Test job completion status with mock items."""
        job, mock_items = self.create_job_with_mock_items(
            item_count=5,
            complete_count=3,  # 3 out of 5 complete
        )

        # Should not be complete (3/5)
        self.assertFalse(job.all_items_complete())

        # Update to all complete
        for item in mock_items:
            item.final_file_date.return_value = timezone.now()

        # Should now be complete
        self.assertTrue(job.all_items_complete())

        # Test status update integration
        original_status = job.status
        job.do_status_update()
        job.refresh_from_db()

        if original_status != "Complete":
            self.assertEqual(job.status, "Complete")
            self.assertTrue(job.needs_etools_update)


class JobModelTransactionTests(TransactionTestCase, JobTestMixin):
    """Tests that require transaction control."""

    def test_job_creation_transaction_integrity(self):
        """Test job creation in transaction scenarios."""
        site = self.create_test_site()

        # Test successful transaction
        with transaction.atomic():
            job = self.create_test_job(workflow=site)
            self.assertIsNotNone(job.id)

        # Verify job exists after transaction
        self.assertTrue(Job.objects.filter(id=job.id).exists())

    def test_job_creation_rollback_scenario(self):
        """Test job creation rollback behavior."""
        site = self.create_test_site()
        initial_count = Job.objects.count()

        try:
            with transaction.atomic():
                self.create_test_job(workflow=site)
                # Force an error to trigger rollback
                raise Exception("Forced rollback")
        except Exception:
            pass

        # Job count should be unchanged due to rollback
        final_count = Job.objects.count()
        self.assertEqual(final_count, initial_count)

    def test_job_bulk_operation_transaction(self):
        """Test bulk operations within transactions."""
        site = self.create_test_site()

        with transaction.atomic():
            jobs = []
            for i in range(5):
                job_data = {
                    "name": f"Transaction Job {i + 1}",
                    "workflow": site,
                    "brand_name": f"Brand {i + 1}",
                }
                jobs.append(Job(**job_data))

            Job.objects.bulk_create(jobs)

        # Verify all jobs were created
        created_jobs = Job.objects.filter(workflow=site, name__startswith="Transaction Job")
        self.assertEqual(created_jobs.count(), 5)


class JobModelConcurrencyTests(TestCase, JobTestMixin):
    """Tests for concurrent access scenarios."""

    def setUp(self):
        """Set up test data."""
        self.site = self.create_test_site()

    def test_concurrent_job_updates(self):
        """Test handling of concurrent job updates."""
        job = self.create_test_job()

        # Simulate concurrent updates by modifying the same job
        job1 = Job.objects.get(id=job.id)
        job2 = Job.objects.get(id=job.id)

        # Update different fields
        job1.name = "Updated Name 1"
        job2.status = "Updated Status"

        # Save both (last one wins for conflicting updates)
        job1.save()
        job2.save()

        # Refresh and check final state
        job.refresh_from_db()
        self.assertEqual(job.status, "Updated Status")

    def test_job_creation_uniqueness(self):
        """Test job creation uniqueness handling."""
        # Create multiple jobs with similar data
        base_data = {
            "workflow": self.site,
            "brand_name": "Test Brand",
            "status": "Active",
        }

        job1 = self.create_test_job(name="Same Name", **base_data)
        job2 = self.create_test_job(name="Same Name", **base_data)

        # Both should be created successfully (unless unique constraint exists)
        self.assertNotEqual(job1.id, job2.id)
        self.assertEqual(job1.name, job2.name)

    def test_job_deletion_concurrent_access(self):
        """Test concurrent access during job deletion."""
        job = self.create_test_job()
        job_id = job.id

        # Mock delete_folder to avoid filesystem operations
        job.delete_folder = Mock()

        # Get two references to the same job
        job1 = Job.objects.get(id=job_id)
        job2 = Job.objects.get(id=job_id)

        # Delete using first reference
        job1.delete()

        # Try to delete using second reference
        job2.delete()  # Should handle gracefully

        # Verify job is marked as deleted
        final_job = Job.objects.get(id=job_id)
        self.assertTrue(final_job.is_deleted)
