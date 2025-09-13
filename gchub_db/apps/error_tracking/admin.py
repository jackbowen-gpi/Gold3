from django.contrib import admin

from gchub_db.apps.error_tracking.models import Error


class ErrorAdmin(admin.ModelAdmin):
    list_display = ("job", "item", "stage", "reported_by", "reported_date")
    list_filter = ("stage",)
    # TODO: Read-only fields.
    exclude = ("job", "item")
    date_hierarchy = "reported_date"


admin.site.register(Error, ErrorAdmin)
