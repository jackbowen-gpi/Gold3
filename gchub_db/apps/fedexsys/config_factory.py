"""
This module handles the creation of FedexConfig objects for consumption
elsewhere in the app. It is merely a shortcut.
"""

from django.conf import settings

try:
    from fedex.config import FedexConfig
except Exception:
    # Provide a lightweight fallback FedexConfig for local development
    class FedexConfig:
        def __init__(
            self,
            key=None,
            password=None,
            account_number=None,
            meter_number=None,
            use_test_server=False,
        ):
            self.key = key
            self.password = password
            self.account_number = account_number
            self.meter_number = meter_number
            self.use_test_server = use_test_server


def create_fedex_config(test_server=False):
    """
    Returns a FedexConfig object for usage in a FedexRequest.

    test_server: (bool) If True, return a FedexConfig object that points
                        to the Fedex test server.
    """
    if test_server:
        return FedexConfig(
            key=settings.FEDEX_TEST_KEY,
            password=settings.FEDEX_TEST_PASSWORD,
            account_number=settings.FEDEX_TEST_ACCOUNT_NUM,
            meter_number=settings.FEDEX_TEST_METER_NUM,
            use_test_server=True,
        )
    else:
        return FedexConfig(
            key=settings.FEDEX_KEY,
            password=settings.FEDEX_PASSWORD,
            account_number=settings.FEDEX_ACCOUNT_NUM,
            meter_number=settings.FEDEX_METER_NUM2,
            use_test_server=False,
        )
