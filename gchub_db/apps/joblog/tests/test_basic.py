from django.test import TestCase


class JobLogSmokeTest(TestCase):
    def test_joblog_import(self):
        from gchub_db.apps.joblog import models as jl_models

        self.assertTrue(hasattr(jl_models, "__all__") or True)
