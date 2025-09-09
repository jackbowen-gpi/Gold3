from unittest import mock

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from gchub_db.apps.fedexsys.models import AddressValidationModel, Shipment


@pytest.fixture
def mock_address():
    class MockAddress:
        name = "John Doe"
        company = "Acme Corp"
        phone = "555-1234"
        address1 = "123 Main St"
        address2 = "Suite 100"
        city = "Metropolis"
        state = "NY"
        zip = "12345"
        zip_code = "12345"
        country = "United States"

    # Make this plain class look enough like a Django model for
    # ContentType.get_for_model() used in tests: provide a minimal
    # _meta with concrete_model attribute.
    try:
        MockAddress._meta = type("_MockMeta", (), {"concrete_model": MockAddress})
    except Exception:
        # If anything goes wrong, return the instance anyway; tests
        # will surface issues. This is intentionally conservative.
        pass

    return MockAddress()


@pytest.fixture
def mock_job():
    class MockJob:
        id = 42
        name = "Test Job"

    return MockJob()


@pytest.fixture
def shipment_instance(db, mock_address, mock_job):
    # Tests previously attempted to call get_for_model() on a plain
    # MockAddress which requires a Django model _meta; instead create
    # or get a harmless ContentType row to stand in for the address
    # content type during tests.
    ct, _ = ContentType.objects.get_or_create(
        app_label="gchub_db.apps.fedexsys", model="mockaddress"
    )
    # Create the Shipment without assigning a Job instance so tests
    # can monkeypatch `shipment_instance.job` with a plain mock when
    # required. Assigning a non-Job object to the ForeignKey fails.
    shipment = Shipment.objects.create(
        job=None,
        address_content_type=ct,
        address_id=1,
        # Use digits-only tracking number so project URL patterns
        # that expect \d+ will match during reverse() in tests.
        tracking_num="123456",
        ship_carrier_code="FDXE",
        ship_packaging="FEDEX_PAK",
        ship_weight=1.0,
        ship_service="PRIORITY_OVERNIGHT",
    )

    # Ensure the GenericForeignKey cache contains the mock address
    # object so tests don't trigger ContentType.model_class() lookup
    # (which can return None for made-up ContentType rows).
    try:
        shipment._state.fields_cache["address"] = mock_address
    except Exception:
        # Be conservative: if we can't set the cache, return the
        # shipment anyway and let tests surface issues.
        pass

    return shipment


def test_str_returns_ref_string(shipment_instance, mock_address, mock_job, monkeypatch):
    # Bypass the ForeignKey descriptor type-check by setting the
    # instance cache directly. Tests expect a simple object to be
    # used here, not an actual Job model instance.
    # Populate the instance-level cache for the FK to match original
    # test expectations (the test pops '_job_cache' from __dict__).
    shipment_instance.__dict__["_job_cache"] = mock_job
    # Avoid using monkeypatch.setattr on the instance which may trigger
    # __repr__ and access the GenericForeignKey; set the GFK cache
    # directly instead.
    # Patch the Shipment.address descriptor at the class level to return
    # the plain mock address object during this test. This avoids
    # triggering ContentType lookups against the mock.
    monkeypatch.setattr(
        Shipment, "address", property(lambda self: mock_address), raising=False
    )
    assert str(shipment_instance) == shipment_instance.get_ref_string()
    shipment_instance.__dict__.pop("_job_cache", None)
    assert shipment_instance.get_ref_string() == str(mock_address.name)


def test_get_recipient_returns_name_or_company(
    shipment_instance, mock_address, monkeypatch
):
    # Set the GenericForeignKey cache directly to avoid ContentType
    # resolution on the mock object.
    monkeypatch.setattr(
        Shipment, "address", property(lambda self: mock_address), raising=False
    )
    assert shipment_instance.get_recipient() == mock_address.name
    mock_address.name = ""
    assert shipment_instance.get_recipient() == mock_address.company


def test_is_international_true_false(shipment_instance, mock_address, monkeypatch):
    monkeypatch.setattr(
        Shipment, "address", property(lambda self: mock_address), raising=False
    )
    with mock.patch(
        "gchub_db.apps.fedexsys.countries.full_to_abbrev", return_value="CA"
    ):
        assert shipment_instance.is_international() is True
    with mock.patch(
        "gchub_db.apps.fedexsys.countries.full_to_abbrev", return_value="US"
    ):
        assert shipment_instance.is_international() is False


def test_print_label(monkeypatch, shipment_instance):
    shipment_instance.label_data = "U29tZUJhc2U2NERhdGE="  # "SomeBase64Data"
    monkeypatch.setattr(shipment_instance, "save", mock.Mock())
    monkeypatch.setattr("builtins.open", mock.mock_open())
    monkeypatch.setattr("binascii.a2b_base64", lambda x: b"binarydata")
    monkeypatch.setattr("django.conf.settings.FEDEX_LABEL_IMG_TYPE", "EPL2")
    shipment_instance.print_label(debug=True)
    assert shipment_instance.date_label_printed is not None
    shipment_instance.save.assert_called_once()


def test_get_shipment_request(monkeypatch, shipment_instance, mock_address):
    monkeypatch.setattr(
        Shipment, "address", property(lambda self: mock_address), raising=False
    )
    mock_config = mock.Mock(account_number="123456")
    mock_shipment = mock.Mock()
    mock_shipment.RequestedShipment = mock.Mock()
    mock_shipment.create_wsdl_object_of_type.side_effect = lambda x: mock.Mock()
    mock_shipment.add_package = mock.Mock()
    monkeypatch.setattr(
        "gchub_db.apps.fedexsys.models.create_fedex_config", lambda: mock_config
    )
    monkeypatch.setattr(
        "gchub_db.apps.fedexsys.models.FedexProcessShipmentRequest",
        lambda config: mock_shipment,
    )
    monkeypatch.setattr(
        "gchub_db.apps.fedexsys.countries.full_to_abbrev", lambda country: "US"
    )
    result = shipment_instance.get_shipment_request()
    assert result == mock_shipment
    mock_shipment.add_package.assert_called_once()


def test_get_absolute_url(shipment_instance):
    url = shipment_instance.get_absolute_url()
    assert url == reverse("shipment_track", args=[shipment_instance.tracking_num])


def test_address_validation_model(monkeypatch):
    # Give the dynamic TestModel an explicit app_label so Django's
    # ModelBase can find an app config without requiring the test
    # to be part of INSTALLED_APPS.
    class TestModel(AddressValidationModel):
        class Meta:
            app_label = "fedexsys"

        company = "Acme Corp"
        address1 = "123 Main St"
        address2 = "Suite 100"
        city = "Metropolis"
        state = "NY"
        zip_code = "12345"
        country = "United States"

    instance = TestModel()
    mock_config = mock.Mock()
    mock_request = mock.Mock()
    mock_address1 = mock.Mock()
    monkeypatch.setattr(
        "gchub_db.apps.fedexsys.models.create_fedex_config", lambda: mock_config
    )
    monkeypatch.setattr(
        "gchub_db.apps.fedexsys.models.FedexAddressValidationRequest",
        lambda config: mock_request,
    )
    mock_request.create_wsdl_object_of_type.return_value = mock_address1
    mock_request.add_address = mock.Mock()
    mock_request.send_request = mock.Mock()
    monkeypatch.setattr(
        "gchub_db.apps.fedexsys.countries.full_to_abbrev", lambda country: "US"
    )
    instance.validate_address()
    mock_request.add_address.assert_called_once_with(mock_address1)
    mock_request.send_request.assert_called_once()
