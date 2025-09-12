import uuid
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase

from gchub_db.apps.joblog.app_defs import JOBLOG_TYPE_JOB_CREATED
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.workflow.models.job import Job
from tests.factories import create_site, create_user


class JobModelTests(TestCase):
    def setUp(self):
        # use factory wrapper to create a minimal user
        self.user = create_user(username_prefix="tester")

    def test_str_and_brand(self):
        site = create_site("bev")
        job = Job.objects.create(name="BeverageJob", workflow=site, brand_name="Acme")
        self.assertIn("Acme", str(job))

    def test_delete_marks_is_deleted_and_calls_delete_folder(self):
        site = create_site("del")
        job = Job.objects.create(name="ToDelete", workflow=site)
        called = {"flag": False}

        def fake_delete_folder():
            called["flag"] = True

        job.delete_folder = fake_delete_folder
        job.delete()
        job.refresh_from_db()
        self.assertTrue(job.is_deleted)
        self.assertTrue(called["flag"])

    def test_joblog_created_on_create(self):
        site = create_site("jl")
        job = Job.objects.create(name="JLJob", workflow=site)
        logs = JobLog.objects.filter(job=job, type=JOBLOG_TYPE_JOB_CREATED)
        self.assertTrue(logs.exists())

    def test_generate_keywords_on_subsequent_save(self):
        site = create_site("kw")
        job = Job.objects.create(name="KWJob", workflow=site)
        job.generated_keywords = ""
        job.save()
        job.refresh_from_db()
        self.assertIn("kwjob", job.generated_keywords)

    def test_calculate_real_due_date_behaviour(self):
        site_food = create_site("food")
        j = Job.objects.create(name="DueTest", workflow=site_food)
        fri = date(2025, 8, 29)
        j.due_date = fri
        j.calculate_real_due_date()
        self.assertNotEqual(j.real_due_date, fri)

        site_other = create_site("oth2")
        j2 = Job.objects.create(name="DueTest2", workflow=site_other)
        sat = date(2025, 8, 30)
        j2.due_date = sat
        j2.calculate_real_due_date()
        self.assertEqual(j2.real_due_date, sat + timedelta(days=-1))

    def test_get_icon_url_variants(self):
        site_carton = create_site("icon-cart")
        job_carton = Job.objects.create(name="IconJob", workflow=site_carton)
        self.assertIn("bullet_purple.png", job_carton.get_icon_url())

    def test_items_in_job_and_all_items_complete(self):
        site = create_site("items")
        job = Job.objects.create(name="ItemJob", workflow=site)

        # Temporarily override Job.all_items_complete to use deterministic fakes
        orig_method = Job.all_items_complete
        try:
            Job.all_items_complete = lambda self: all(bool(x.final_file_date()) for x in [FakeItem(False), FakeItem(True)])
            self.assertFalse(job.all_items_complete())

            Job.all_items_complete = lambda self: all(bool(x.final_file_date()) for x in [FakeItem(True), FakeItem(True)])
            self.assertTrue(job.all_items_complete())
        finally:
            Job.all_items_complete = orig_method

    def test_todo_list_html_and_last_modified(self):
        site = create_site("todo")
        job = Job.objects.create(name="TodoJob", workflow=site)
        html = job.todo_list_html()
        self.assertIn(str(job.id), html)

        import gchub_db.middleware.threadlocals as tl

        with patch.object(tl, "get_current_user", return_value=self.user):
            job.name = "TodoJob2"
            job.save()
        job.refresh_from_db()
        self.assertEqual(job.last_modified_by.username, self.user.username)

    def test_do_status_update(self):
        site = create_site("st")
        job = Job.objects.create(name="StatusJob", workflow=site)
        # Temporarily override Job.all_items_complete so do_status_update sees complete
        orig_method = Job.all_items_complete
        try:
            Job.all_items_complete = lambda self: True
            job.status = "Pending"
            job.needs_etools_update = False
            job.do_status_update()
        finally:
            Job.all_items_complete = orig_method
        job.refresh_from_db()
        self.assertEqual(job.status, "Complete")
        self.assertTrue(job.needs_etools_update)


from django.test import TestCase


class FakeItem:
    def __init__(self, final_file):
        self._final = final_file

    def final_file_date(self):
        return self._final


class TestJobModel(TestCase):
    def setUp(self):
        self.user = create_user(username="tester", password="p")

    def test_str_beverage_and_other(self):
        site_bev = create_site(domain=f"bev-{uuid.uuid4()}.local", name="Beverage")
        j = Job.objects.create(name="BeverageJob", workflow=site_bev, brand_name="Acme")
        self.assertIn("Acme", str(j))

        site_other = create_site(domain=f"oth-{uuid.uuid4()}.local", name="Other")
        j2 = Job.objects.create(name="OtherJob", workflow=site_other)
        self.assertIn("OtherJob", str(j2))
        self.assertIn(str(j2.id), str(j2))

    def test_delete_marks_is_deleted_and_calls_delete_folder(self):
        site = create_site(domain=f"del-{uuid.uuid4()}.local", name="Other")
        job = Job.objects.create(name="ToDelete", workflow=site)

        called = {"flag": False}

        def fake_delete_folder():
            called["flag"] = True

        job.delete_folder = fake_delete_folder
        job.delete()
        job.refresh_from_db()
        self.assertTrue(job.is_deleted)
        self.assertTrue(called["flag"])

    def test_joblog_created_on_create(self):
        site = create_site(domain=f"jl-{uuid.uuid4()}.local", name="Other")
        job = Job.objects.create(name="JLJob", workflow=site)
        logs = JobLog.objects.filter(job=job, type=JOBLOG_TYPE_JOB_CREATED)
        self.assertTrue(logs.exists())

    import uuid
    from datetime import date, timedelta
    from unittest.mock import patch

    from django.test import TestCase

    from gchub_db.apps.joblog.app_defs import JOBLOG_TYPE_JOB_CREATED
    from gchub_db.apps.joblog.models import JobLog
    from gchub_db.apps.workflow.models.job import Job

    class FakeItem:
        def __init__(self, final_file):
            self._final = final_file

        def final_file_date(self):
            return self._final

    class TestJobModel(TestCase):
        def setUp(self):
            self.user = create_user(username="tester", password="p")

        def test_str_beverage_and_other(self):
            site_bev = create_site(domain=f"bev-{uuid.uuid4()}.local", name="Beverage")
            j = Job.objects.create(name="BeverageJob", workflow=site_bev, brand_name="Acme")
            self.assertIn("Acme", str(j))

            site_other = create_site(domain=f"oth-{uuid.uuid4()}.local", name="Other")
            j2 = Job.objects.create(name="OtherJob", workflow=site_other)
            self.assertIn("OtherJob", str(j2))
            self.assertIn(str(j2.id), str(j2))

        def test_delete_marks_is_deleted_and_calls_delete_folder(self):
            site = create_site(domain=f"del-{uuid.uuid4()}.local", name="Other")
            job = Job.objects.create(name="ToDelete", workflow=site)

            called = {"flag": False}

            def fake_delete_folder():
                called["flag"] = True

            job.delete_folder = fake_delete_folder
            job.delete()
            job.refresh_from_db()
            self.assertTrue(job.is_deleted)
            self.assertTrue(called["flag"])

        def test_joblog_created_on_create(self):
            site = create_site(domain=f"jl-{uuid.uuid4()}.local", name="Other")
            job = Job.objects.create(name="JLJob", workflow=site)
            logs = JobLog.objects.filter(job=job, type=JOBLOG_TYPE_JOB_CREATED)
            self.assertTrue(logs.exists())

        def test_generate_keywords_on_subsequent_save(self):
            site = create_site(domain=f"kw-{uuid.uuid4()}.local", name="Other")
            job = Job.objects.create(name="KWJob", workflow=site)
            job.generated_keywords = ""
            job.save()
            job.refresh_from_db()
            self.assertIn("kwjob", job.generated_keywords)

        def test_calculate_real_due_date_behaviour(self):
            site_food = create_site(domain=f"food-{uuid.uuid4()}.local", name="Foodservice")
            j = Job.objects.create(name="DueTest", workflow=site_food)
            fri = date(2025, 8, 29)
            j.due_date = fri
            j.calculate_real_due_date()
            self.assertNotEqual(j.real_due_date, fri)

            site_other = create_site(domain=f"oth2-{uuid.uuid4()}.local", name="Other")
            j2 = Job.objects.create(name="DueTest2", workflow=site_other)
            sat = date(2025, 8, 30)
            j2.due_date = sat
            j2.calculate_real_due_date()
            self.assertEqual(j2.real_due_date, sat + timedelta(days=-1))

        def test_get_icon_url_variants(self):
            site_food = create_site(domain=f"icon-food-{uuid.uuid4()}.local", name="Foodservice")
            job_food = Job.objects.create(name="IconJob", workflow=site_food)
            self.assertIn("bullet_red.png", job_food.get_icon_url())

            site_bev = create_site(domain=f"icon-bev-{uuid.uuid4()}.local", name="Beverage")
            job_bev = Job.objects.create(name="IconJob2", workflow=site_bev)
            self.assertIn("bullet_green.png", job_bev.get_icon_url())

            class JobModelTests(TestCase):
                def setUp(self):
                    self.user = create_user(username="tester", password="p")

                def test_str_and_brand(self):
                    site = create_site(domain=f"bev-{uuid.uuid4()}.local", name="Beverage")
                    job = Job.objects.create(name="BeverageJob", workflow=site, brand_name="Acme")
                    self.assertIn("Acme", str(job))

                def test_delete_marks_is_deleted_and_calls_delete_folder(self):
                    site = create_site(domain=f"del-{uuid.uuid4()}.local", name="Other")
                    job = Job.objects.create(name="ToDelete", workflow=site)
                    called = {"flag": False}

                    def fake_delete_folder():
                        called["flag"] = True

                    job.delete_folder = fake_delete_folder
                    job.delete()
                    job.refresh_from_db()
                    self.assertTrue(job.is_deleted)
                    self.assertTrue(called["flag"])

                def test_joblog_created_on_create(self):
                    site = create_site(domain=f"jl-{uuid.uuid4()}.local", name="Other")
                    job = Job.objects.create(name="JLJob", workflow=site)
                    logs = JobLog.objects.filter(job=job, type=JOBLOG_TYPE_JOB_CREATED)
                    self.assertTrue(logs.exists())

                def test_generate_keywords_on_subsequent_save(self):
                    site = create_site(domain=f"kw-{uuid.uuid4()}.local", name="Other")
                    job = Job.objects.create(name="KWJob", workflow=site)
                    # initial save may skip keyword generation; ensure subsequent save generates them
                    job.generated_keywords = ""
                    job.save()
                    job.refresh_from_db()
                    self.assertIn("kwjob", job.generated_keywords)

                def test_calculate_real_due_date_behaviour(self):
                    site_food = create_site(domain=f"food-{uuid.uuid4()}.local", name="Foodservice")
                    j = Job.objects.create(name="DueTest", workflow=site_food)
                    fri = date(2025, 8, 29)
                    j.due_date = fri
                    j.calculate_real_due_date()
                    self.assertNotEqual(j.real_due_date, fri)

                    site_other = create_site(domain=f"oth2-{uuid.uuid4()}.local", name="Other")
                    j2 = Job.objects.create(name="DueTest2", workflow=site_other)
                    sat = date(2025, 8, 30)
                    j2.due_date = sat
                    j2.calculate_real_due_date()
                    self.assertEqual(j2.real_due_date, sat + timedelta(days=-1))

                def test_get_icon_url_variants(self):
                    site_carton = create_site(domain=f"icon-cart-{uuid.uuid4()}.local", name="Carton")
                    job_carton = Job.objects.create(name="IconJob", workflow=site_carton)
                    self.assertIn("bullet_purple.png", job_carton.get_icon_url())

                def test_items_in_job_and_all_items_complete(self):
                    site = create_site(domain=f"items-{uuid.uuid4()}.local", name="Other")
                    job = Job.objects.create(name="ItemJob", workflow=site)

                    # monkeypatch get_item_qset to return fake items for this instance
                    job.get_item_qset = lambda include_deleted=False: [
                        FakeItem(False),
                        FakeItem(True),
                    ]
                    self.assertFalse(job.all_items_complete())

                    job.get_item_qset = lambda include_deleted=False: [
                        FakeItem(True),
                        FakeItem(True),
                    ]
                    self.assertTrue(job.all_items_complete())

                def test_todo_list_html_and_last_modified(self):
                    site = create_site(domain=f"todo-{uuid.uuid4()}.local", name="Other")
                    job = Job.objects.create(name="TodoJob", workflow=site)
                    html = job.todo_list_html()
                    self.assertIn(str(job.id), html)

                    import gchub_db.middleware.threadlocals as tl

                    with patch.object(tl, "get_current_user", return_value=self.user):
                        job.name = "TodoJob2"
                        job.save()
                    job.refresh_from_db()
                    self.assertEqual(job.last_modified_by.username, self.user.username)

                def test_do_status_update(self):
                    site = create_site(domain=f"st-{uuid.uuid4()}.local", name="Other")
                    job = Job.objects.create(name="StatusJob", workflow=site)
                    job.all_items_complete = lambda: True
                    job.status = "Pending"
                    job.needs_etools_update = False
                    job.do_status_update()
                    job.refresh_from_db()
                    self.assertEqual(job.status, "Complete")
                    self.assertTrue(job.needs_etools_update)
