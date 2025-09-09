from django.contrib import admin

from gchub_db.apps.calendar.models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "event_date",
        "employee",
        "description",
    )
    ordering = ("-event_date",)


admin.site.register(Event, EventAdmin)
