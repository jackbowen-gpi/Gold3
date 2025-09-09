from django.contrib import admin

from gchub_db.apps.software.models import Software


class SoftwareAdmin(admin.ModelAdmin):
    search_fields = ["application_name", "vendor"]
    list_display = ("application_name", "version", "vendor", "installation_location")
    list_filter = (
        "os",
        "vendor",
    )
    ordering = ("application_name",)


admin.site.register(Software, SoftwareAdmin)
