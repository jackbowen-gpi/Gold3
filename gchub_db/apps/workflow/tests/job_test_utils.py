"""
Job model test utilities and fixtures.
Provides common test data and helper methods for Job model testing.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from gchub_db.apps.workflow.models.job import Job
from tests.factories import create_site, create_user


class JobTestMixin:
    """Mixin providing common job test utilities."""

    def create_test_job(self, **kwargs):
        """Create a job with sensible defaults for testing."""
        defaults = {
            "name": f"Test Job {uuid.uuid4().hex[:8]}",
            "workflow": getattr(self, "site", None) or self.create_test_site(),
            "brand_name": "Test Brand",
            "status": "Active",
            "due_date": date.today() + timedelta(days=7),
            "is_deleted": False,
        }
        defaults.update(kwargs)

        return Job.objects.create(**defaults)

    def create_test_site(self, **kwargs):
        """Create a test site with sensible defaults."""
        defaults = {
            "domain": f"test-{uuid.uuid4().hex[:8]}.local",
            "name": f"Test Site {uuid.uuid4().hex[:8]}",
        }
        defaults.update(kwargs)

        return create_site(**defaults)

    def create_test_user(self, **kwargs):
        """Create a test user with sensible defaults."""
        defaults = {"username_prefix": f"testuser{uuid.uuid4().hex[:8]}"}
        defaults.update(kwargs)

        return create_user(**defaults)

    def create_jobs_with_different_statuses(self, site=None):
        """Create a set of jobs with different statuses for testing."""
        if not site:
            site = getattr(self, "site", None) or self.create_test_site()

        jobs = {}
        statuses = ["Active", "Pending", "Complete", "On Hold", "Cancelled"]

        for status in statuses:
            jobs[status.lower().replace(" ", "_")] = self.create_test_job(name=f"{status} Job", workflow=site, status=status)

        return jobs

    def create_jobs_with_different_priorities(self, site=None):
        """Create jobs with different creation dates since priority field doesn't exist."""
        if not site:
            site = getattr(self, "site", None) or self.create_test_site()

        jobs = {}
        # Use creation date differences instead of priority
        for i, delay in enumerate([0, 1, 2, 3, 4]):
            job = self.create_test_job(name=f"Job {i+1}", workflow=site)
            # Mock the creation_date if needed
            jobs[f"job_{i+1}"] = job

        return jobs

    def create_jobs_with_different_due_dates(self, site=None):
        """Create jobs with different due dates for testing."""
        if not site:
            site = getattr(self, "site", None) or self.create_test_site()

        jobs = {}
        today = date.today()

        date_configs = [
            ("overdue", today - timedelta(days=7)),
            ("due_today", today),
            ("due_tomorrow", today + timedelta(days=1)),
            ("due_next_week", today + timedelta(days=7)),
            ("due_next_month", today + timedelta(days=30)),
        ]

        for key, due_date in date_configs:
            jobs[key] = self.create_test_job(
                name=f'{key.replace("_", " ").title()} Job',
                workflow=site,
                due_date=due_date,
            )

        return jobs

    def create_jobs_for_different_sites(self):
        """Create jobs across different site types for testing."""
        sites = {
            "beverage": self.create_test_site(name="Beverage Site", domain=f"beverage-{uuid.uuid4().hex[:8]}.local"),
            "carton": self.create_test_site(name="Carton Site", domain=f"carton-{uuid.uuid4().hex[:8]}.local"),
            "food": self.create_test_site(name="Food Site", domain=f"food-{uuid.uuid4().hex[:8]}.local"),
            "regular": self.create_test_site(name="Regular Site", domain=f"regular-{uuid.uuid4().hex[:8]}.local"),
        }

        jobs = {}
        for site_type, site in sites.items():
            jobs[site_type] = self.create_test_job(name=f"{site_type.title()} Job", workflow=site)

        return jobs, sites

    def create_job_with_mock_items(self, item_count=3, complete_count=2):
        """Create a job and mock its items for testing completion status."""
        from unittest.mock import Mock

        job = self.create_test_job()

        # Create mock items
        items = []
        for i in range(item_count):
            item = Mock()
            if i < complete_count:
                item.final_file_date.return_value = timezone.now()
            else:
                item.final_file_date.return_value = None
            item.is_deleted = False
            items.append(item)

        # Mock the get_item_qset method
        job.get_item_qset = Mock(return_value=items)

        return job, items

    def assert_job_fields_equal(self, job1, job2, fields=None):
        """Assert that specified fields are equal between two jobs."""
        if fields is None:
            fields = ["name", "workflow", "brand_name", "status", "due_date"]

        for field in fields:
            self.assertEqual(
                getattr(job1, field),
                getattr(job2, field),
                f"Field '{field}' differs between jobs",
            )

    def assert_job_has_required_fields(self, job):
        """Assert that a job has all required fields populated."""
        required_fields = ["name", "workflow", "created"]

        for field in required_fields:
            value = getattr(job, field)
            self.assertIsNotNone(value, f"Required field '{field}' is None")

        # Additional type checks
        self.assertIsInstance(job.name, str)
        self.assertTrue(len(job.name) > 0)

    def get_job_field_values(self, job, fields=None):
        """Get a dictionary of field values for a job."""
        if fields is None:
            fields = [
                "id",
                "name",
                "workflow",
                "brand_name",
                "status",
                "due_date",
                "creation_date",
                "is_deleted",
            ]

        return {field: getattr(job, field, None) for field in fields}


class JobTestData:
    """Static test data for job testing."""

    COMMON_JOB_NAMES = [
        "Website Redesign",
        "Database Migration",
        "API Development",
        "Mobile App Update",
        "Security Audit",
        "Performance Optimization",
        "Content Management",
        "User Interface Refresh",
        "System Integration",
        "Quality Assurance",
    ]

    COMMON_BRAND_NAMES = [
        "Acme Corp",
        "Global Industries",
        "Tech Solutions",
        "Digital Dynamics",
        "Innovation Labs",
        "Future Systems",
        "Premier Products",
        "Elite Enterprises",
        "Advanced Analytics",
        "Smart Solutions",
    ]

    VALID_STATUSES = [
        "Active",
        "Pending",
        "Complete",
        "On Hold",
        "Cancelled",
        "In Progress",
        "Under Review",
        "Approved",
        "Rejected",
    ]

    SITE_TYPES = {
        "beverage": "Beverage Production",
        "carton": "Carton Manufacturing",
        "foodservice": "Food Processing",  # Changed from 'food' to 'foodservice'
        "regular": "General Workflow",
    }

    @classmethod
    def get_sample_job_data(cls, count=1):
        """Get sample job data for testing."""
        import random

        data = []
        for i in range(count):
            data.append(
                {
                    "name": random.choice(cls.COMMON_JOB_NAMES),
                    "brand_name": random.choice(cls.COMMON_BRAND_NAMES),
                    "status": random.choice(cls.VALID_STATUSES),
                    "due_date": date.today() + timedelta(days=random.randint(1, 60)),
                    "customer_name": f"Customer {i+1}",
                    "comments": f"Sample comments for job {i+1}",
                }
            )

        return data if count > 1 else data[0]

    @classmethod
    def get_edge_case_data(cls):
        """Get edge case data for testing."""
        return {
            "empty_name": {"name": ""},
            "very_long_name": {"name": "X" * 1000},
            "special_chars_name": {"name": "Job with §pecial ¢haråcters & symbols!@#$%"},
            "unicode_name": {"name": "Job with Ünícødé 中文 العربية"},
            "past_due_date": {"due_date": date.today() - timedelta(days=30)},
            "far_future_due_date": {"due_date": date.today() + timedelta(days=3650)},
            "zero_budget": {
                "budget_amount": Decimal("0.00"),
                "budget_hours": Decimal("0.0"),
            },
            "negative_budget": {
                "budget_amount": Decimal("-100.00"),
                "budget_hours": Decimal("-10.0"),
            },
            "very_high_priority": {"priority": 999},
            "very_low_priority": {"priority": -999},
        }


def create_sample_jobs(site, count=10):
    """Create a set of sample jobs for testing purposes."""
    jobs = []
    sample_data = JobTestData.get_sample_job_data(count)

    for i, data in enumerate(sample_data if isinstance(sample_data, list) else [sample_data]):
        data["workflow"] = site
        data["name"] = f"{data['name']} {i+1}"  # Make names unique
        jobs.append(Job.objects.create(**data))

    return jobs
