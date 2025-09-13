from django.contrib import admin

from gchub_db.apps.bev_billing.models import BevInvoice


class BevInvoiceAdmin(admin.ModelAdmin):
    search_fields = ["invoice_number"]
    list_display = (
        "id",
        "invoice_number",
        "job",
        "creation_date",
        "invoice_entry_date",
    )
    exclude = ("job",)


admin.site.register(BevInvoice, BevInvoiceAdmin)
