from django.urls import re_path

# Provide a compatibility alias for legacy `url()` calls used across the codebase.
url = re_path

from gchub_db.apps.address.views import (
    AddressSearchResults,
    address_home,
    attach_address,
    delete_address,
    edit_contact,
    new_address,
    search_address,
    view_contact,
)

urlpatterns = [
    url(r"^$", address_home, name="address_home"),
    url(r"^browse/$", AddressSearchResults.as_view(), name="address_browse"),
    url(r"^view/(?P<contact_id>\d+)/$", view_contact, name="address_view"),
    url(r"^edit/(?P<contact_id>\d+)/$", edit_contact, name="address_edit"),
    url(r"^attach/(?P<contact_id>\d+)/$", attach_address, name="address_attach"),
    url(r"^new/$", new_address, name="address_new"),
    url(r"^delete/(?P<contact_id>\d+)/$", delete_address, name="address_delete"),
    url(r"^search/$", search_address, name="address_search"),
]
