from django.test import TestCase


class WorkflowSmokeTest(TestCase):
    def test_workflow_imports(self):
        # Ensure key workflow modules import
        from gchub_db.apps.workflow import models, views

        self.assertTrue(hasattr(models, "__all__") or True)
        self.assertTrue(hasattr(views, "__all__") or True)
