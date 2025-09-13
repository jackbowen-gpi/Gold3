from django.test import TestCase


class SimpleTest(TestCase):
    def test_simple(self):
        from django.contrib.sites.models import Site

        site = Site.objects.create(domain="test.com", name="TestSite")
        self.assertEqual(site.name, "TestSite")
