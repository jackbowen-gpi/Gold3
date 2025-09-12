"""
Module gchub_db\apps\\workflow\tests\test_general.py
"""

from unittest import mock
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.contrib.sites.models import Site

from gchub_db.apps.workflow.models.general import (
    Plant,
    Press,
    PrintLocation,
    ItemCatalog,
    ItemSpec,
    StepSpec,
    ChargeCategory,
    ChargeType,
    Charge,
    JobAddress,
    ItemColor,
    ItemReview,
    Revision,
)
from gchub_db.apps.workflow.models.item import Item
from gchub_db.apps.workflow.models.job import Job


# Minimal stubs/mocks for related models
class DummyJob:
    def __init__(self, workflow_name="Beverage", prepress_supplier=None, artist=None):
        self.workflow = mock.Mock()
        self.workflow.name = workflow_name
        self.prepress_supplier = prepress_supplier
        self.artist = artist
        self.name = "TestJob"
        self.id = 1
        self.temp_printlocation = mock.Mock()
        self.temp_printlocation.plant = mock.Mock()
        self.temp_printlocation.press = mock.Mock()
        self.temp_printlocation.plant.name = "Raleigh"
        self.temp_printlocation.press.name = "BHS"

    def save(self):
        pass

    def growl_at_artist(self, *args, **kwargs):
        pass


class DummyItem:
    def __init__(self, job=None, size=None, is_deleted=False, num_in_job=1):
        self.job = job or DummyJob()
        self.size = size or mock.Mock()
        self.size.size = "Quart"
        self.is_deleted = is_deleted
        self.num_in_job = num_in_job
        self.fsb_nine_digit = "123456789"
        self.itemcolor_set = mock.Mock()
        self.itemcolor_set.all.return_value = []
        self.get_inkbook_display = mock.Mock(return_value="PMS")
        self.final_file_date = mock.Mock(return_value=date.today())
        self.get_num_colors_carton = mock.Mock(return_value=2)

    def do_create_joblog_entry(self, *args, **kwargs):
        pass


class TestItemCatalog(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test.com", name="TestSite")
        self.catalog = ItemCatalog.objects.create(size="250ml", workflow=self.site)

    def test_is_metric_true(self):
        self.catalog.size = "250ml"
        assert self.catalog.is_metric() is True
        self.catalog.size = "500ml"
        assert self.catalog.is_metric() is True
        self.catalog.size = "liter"
        assert self.catalog.is_metric() is True
        self.catalog.size = "1liter"
        assert self.catalog.is_metric() is True

    def test_is_metric_false(self):
        self.catalog.size = "Quart"
        assert self.catalog.is_metric() is False

    def test_get_stripped_size(self):
        self.catalog.size = "  Quart  "
        assert self.catalog.get_stripped_size() == "quart"

    def test_get_coating_type(self):
        # Patch UNCOATED_SUBSTRATES
        with mock.patch("gchub_db.apps.workflow.models.general.UNCOATED_SUBSTRATES", [1, 2]):
            self.catalog.product_substrate = 1
            assert self.catalog.get_coating_type() == "Uncoated"
            assert self.catalog.get_coating_type(True) == "U"
            self.catalog.product_substrate = 99
            assert self.catalog.get_coating_type() == "Coated"
            assert self.catalog.get_coating_type(True) == "C"

    def test_pdf_template_exists_true(self):
        with mock.patch(
            "gchub_db.apps.workflow.models.general.fs_api.get_pdf_template",
            return_value=True,
        ):
            assert self.catalog.pdf_template_exists() is True

    def test_pdf_template_exists_false(self):
        with mock.patch(
            "gchub_db.apps.workflow.models.general.fs_api.get_pdf_template",
            side_effect=Exception,
        ):
            assert self.catalog.pdf_template_exists() is False


class TestStepSpec(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test.com", name="TestSite")
        self.plant = Plant.objects.create(name="Plant1", workflow=self.site)
        self.press = Press.objects.create(name="Press1", short_name="P1", workflow=self.site)
        self.printlocation = PrintLocation.objects.create(plant=self.plant, press=self.press)
        self.catalog = ItemCatalog.objects.create(size="Quart", workflow=self.site)
        self.itemspec = ItemSpec.objects.create(size=self.catalog, printlocation=self.printlocation)
        self.stepspec = StepSpec.objects.create(itemspec=self.itemspec)

    def test_stepspec_pre_save_sets_num_blanks(self):
        self.stepspec.step_around = 2
        self.stepspec.step_across = 3
        self.stepspec.save()
        self.stepspec.refresh_from_db()
        assert self.stepspec.num_blanks == 6

    def test_stepspec_pre_save_sets_num_blanks_none(self):
        self.stepspec.step_around = None
        self.stepspec.step_across = 3
        self.stepspec.save()
        self.stepspec.refresh_from_db()
        assert self.stepspec.num_blanks is None


class TestChargeType(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test.com", name="Carton")
        self.cat = ChargeCategory.objects.create(name="Proof")
        self.charge_type = ChargeType.objects.create(
            type="Prepress Production",
            category=self.cat,
            base_amount=100,
            rush_type="FSBMULTH",
            workflow=self.site,
            active=True,
        )
        self.item = DummyItem()

    def test_actual_charge_basic(self):
        self.charge_type.adjust_for_colors = True
        self.charge_type.save()
        amount = self.charge_type.actual_charge(num_colors=2)
        assert amount == 200

    def test_actual_charge_quality(self):
        self.charge_type.adjust_for_quality = True
        self.charge_type.save()
        amount = self.charge_type.actual_charge(quality="B")
        self.assertAlmostEqual(amount, 67, places=0)

    def test_actual_charge_rush(self):
        self.charge_type.rush_type = "FSBMULTH"
        self.charge_type.save()
        amount = self.charge_type.actual_charge(rush_days=0)
        assert amount == 200


class TestCharge(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test.com", name="Beverage")
        self.cat = ChargeCategory.objects.create(name="Proof")
        self.charge_type = ChargeType.objects.create(
            type="Proof",
            category=self.cat,
            base_amount=100,
            rush_type="FSBMULTH",
            workflow=self.site,
            active=True,
        )
        # Create actual Job and Item instances
        self.job = Job.objects.create(name="TestJob", workflow=self.site, brand_name="TestBrand")
        self.catalog = ItemCatalog.objects.create(size="Quart", workflow=self.site)
        self.item = Item.objects.create(
            job=self.job,
            num_in_job=1,
            size=self.catalog,
            workflow=self.site,
            fsb_nine_digit="123456789",
        )
        self.charge = Charge.objects.create(item=self.item, description=self.charge_type, amount=100)

    def test_is_billable_true(self):
        self.item.is_deleted = False
        self.item.final_file_date = mock.Mock(return_value=date(2025, 9, 11))
        self.item.job.prepress_supplier = None
        self.charge.invoice_date = None
        assert self.charge.is_billable(2025, 9) is True

    def test_is_billable_false_invoice(self):
        self.charge.invoice_date = date.today()
        assert self.charge.is_billable(date.today().year, date.today().month) is False

    def test_is_billable_false_deleted(self):
        self.charge.invoice_date = None
        self.item.is_deleted = True
        assert self.charge.is_billable(date.today().year, date.today().month) is False

    def test_is_billable_false_supplier(self):
        self.item.is_deleted = False
        self.item.job.prepress_supplier = "PHT"
        assert self.charge.is_billable(date.today().year, date.today().month) is False


class TestJobAddress(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test.com", name="TestSite")
        # Create actual Job instance
        self.job = Job.objects.create(name="TestJob", workflow=self.site, brand_name="TestBrand")
        self.address = JobAddress.objects.create(
            job=self.job,
            name="John Doe",
            company="TestCo",
            address1="123 Main",
            city="Testville",
            state="TS",
            zip="12345",
            country="USA",
        )

    def test_copy_to_contacts(self):
        with mock.patch("gchub_db.apps.workflow.models.general.Contact.save") as save_mock:
            contact = self.address.copy_to_contacts()
            assert contact.first_name == "John"
            assert contact.last_name == "Doe"
            save_mock.assert_called_once()

    def test_do_create_joblog_entry(self):
        with mock.patch("gchub_db.apps.workflow.models.general.JobLog.save") as save_mock:
            self.address.do_create_joblog_entry(job_id=self.job, logtype="test")
            save_mock.assert_called_once()


class TestItemColor(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test.com", name="Foodservice")
        # Create the Art Request ChargeType required by item_post_save
        self.art_request_cat = ChargeCategory.objects.create(name="Art Request Category")
        self.art_request_type = ChargeType.objects.create(
            type="Art Request",
            category=self.art_request_cat,
            base_amount=50,
            workflow=self.site,
            active=True,
        )
        # Create actual Job and Item instances
        self.job = Job.objects.create(name="TestJob", workflow=self.site, brand_name="TestBrand")
        self.catalog = ItemCatalog.objects.create(size="Quart", workflow=self.site)
        self.item = Item.objects.create(
            job=self.job,
            num_in_job=1,
            size=self.catalog,
            workflow=self.site,
            fsb_nine_digit="123456789",
        )
        self.itemcolor = ItemColor.objects.create(item=self.item, color="1234567")

    def test_fsb_display_name_special_match(self):
        self.itemcolor.color = "12345678"
        assert self.itemcolor.fsb_display_name() == "12345678"

    def test_fsb_display_name_other(self):
        self.itemcolor.color = "QPO123"
        assert self.itemcolor.fsb_display_name() == "QPO123"

    def test_calculate_plate_code(self):
        self.itemcolor.sequence = 2
        code = self.itemcolor.calculate_plate_code()
        assert code.startswith("123456789 1B")
        assert self.itemcolor.plate_code.startswith("123456789 1B")


class TestItemReview(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test.com", name="TestSite")
        # Create actual Job and Item instances
        self.job = Job.objects.create(name="TestJob", workflow=self.site, brand_name="TestBrand")
        self.catalog = ItemCatalog.objects.create(size="Quart", workflow=self.site)
        self.item = Item.objects.create(
            job=self.job,
            num_in_job=1,
            size=self.catalog,
            workflow=self.site,
            fsb_nine_digit="123456789",
        )
        self.review = ItemReview.objects.create(item=self.item, review_catagory="plant")

    def test_status_ok(self):
        self.review.review_ok = True
        status = self.review.status()
        assert status["status"] == "OK"

    def test_status_rejected(self):
        self.review.review_ok = False
        self.review.review_date = date.today()
        status = self.review.status()
        assert status["status"] == "Rejected"

    def test_status_expired(self):
        self.review.review_ok = False
        self.review.review_date = None
        self.review.review_initiated_date = datetime.now() - timedelta(days=10)
        with mock.patch(
            "gchub_db.apps.workflow.models.general.general_funcs._utcnow_naive",
            return_value=datetime.now(),
        ):
            status = self.review.status()
            assert status["status"] in ["Time Expired", "Waiting"]

    def test_expires_weekend(self):
        # Saturday
        self.review.review_initiated_date = datetime(2024, 6, 8)
        exp = self.review.expires()
        assert isinstance(exp, datetime)


class TestRevision(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test.com", name="TestSite")
        # Create actual Job and Item instances
        self.job = Job.objects.create(name="TestJob", workflow=self.site, brand_name="TestBrand")
        self.catalog = ItemCatalog.objects.create(size="Quart", workflow=self.site)
        self.item = Item.objects.create(
            job=self.job,
            num_in_job=1,
            size=self.catalog,
            workflow=self.site,
            fsb_nine_digit="123456789",
        )
        self.revision = Revision.objects.create(item=self.item, due_date=date.today(), comments="Test")

    def test_complete_revision(self):
        self.revision.complete_revision()
        self.revision.refresh_from_db()
        assert self.revision.complete_date == date.today()
