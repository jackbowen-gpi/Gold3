"""
The urls.py file handles URL dispatching for the workflow module. Requests
that begin with /workflow are sent here. The major models get their own
URL matching sections below, which are combined into urlpatterns at the end
of the file for matching.
"""

from django.urls import re_path as url

from gchub_db.apps.item_catalog.views import (
    catalog_search,
    get_pdf_template,
    home,
    itemcat_popup,
    list_templates,
)

urlpatterns = [
    url(r"^$", home, name="item_catalog_home"),
    url(r"^search/$", catalog_search, name="item_catalog_search"),
    url(
        r"^itemcat_popup/new/$",
        itemcat_popup,
        name="item_catalog_itemcat_popup_new_itemcatalog",
    ),
    url(
        r"^itemcat_popup/edit/(?P<itemcat_id>\d+)/$",
        itemcat_popup,
        name="item_catalog_itemcat_popup_edit_itemcatalog",
    ),
    url(r"^pdf_templates/$", list_templates, name="list_templates"),
    url(
        r"^get_pdf_template/(?P<size_id>\d+)/$",
        get_pdf_template,
        name="get_pdf_template",
    ),
]
