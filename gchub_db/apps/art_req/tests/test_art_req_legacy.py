"""
Legacy small tests moved from apps/art_req/tests.py into the tests package so
unittest discovery doesn't confuse the module and package named `tests`.
"""

from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """Tests that 1 + 1 always equals 2."""
        self.assertEqual(1 + 1, 2)


__test__ = {
    "doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
""",
}
