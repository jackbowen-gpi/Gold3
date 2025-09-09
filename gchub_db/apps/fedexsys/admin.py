from django.contrib import admin

from gchub_db.apps.fedexsys.models import Shipment


class ShipmentAdmin(admin.ModelAdmin):
    exclude = ("job", "address_content_type")
    date_hierarchy = "date_shipped"
    list_display = (
        "id",
        "job",
        "tracking_num",
        "net_shipping_cost",
        "date_shipped",
        "date_label_printed",
    )
    list_display_links = ("id", "job")


admin.site.register(Shipment, ShipmentAdmin)
