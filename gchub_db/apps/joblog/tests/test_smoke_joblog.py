from importlib import import_module

from django.test import SimpleTestCase


class JobLogSmokeTest(SimpleTestCase):
    def test_models_importable(self):
        """Ensure the app's models module can be imported and exposes job-related symbols."""
        m = import_module("gchub_db.apps.joblog.models")
        names = dir(m)
        has_job = any(n.lower().startswith("job") for n in names)
        self.assertTrue(
            has_job,
            f"expected a Job* symbol in gchub_db.apps.joblog.models, found: {names[:20]}",
        )
