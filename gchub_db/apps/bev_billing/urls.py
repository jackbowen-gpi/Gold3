from django.urls import re_path as url

from gchub_db.apps.bev_billing.views import (
    InvoiceQueue,
    get_bev_invoice_pdf,
    view_invoice,
)

urlpatterns = [
    url(r"^invoice/queue/$", InvoiceQueue.as_view(), name="invoice_queue"),
    url(r"^invoice/view/(?P<invoice_id>\d+)/$", view_invoice, name="view_invoice"),
    url(
        r"^invoice/get_pdf/(?P<invoice_id>\d+)/$",
        get_bev_invoice_pdf,
        name="bev_billing-get_bev_invoice_pdf",
    ),
]
