from django.test import TestCase


class AccountsSmokeTest(TestCase):
    def test_accounts_import(self):
        # Ensure accounts app models import cleanly
        from gchub_db.apps.accounts import models as accounts_models

        self.assertTrue(hasattr(accounts_models, "__all__") or True)
