from django.contrib import admin

from gchub_db.apps.carton_billing.models import CartonSapEntry


class CartonSapEntryAdmin(admin.ModelAdmin):
    list_display = (
        "job",
        "creation_date",
        "qad_entry_date",
        "qad_entry_user",
    )
    exclude = ("job",)


admin.site.register(CartonSapEntry, CartonSapEntryAdmin)
