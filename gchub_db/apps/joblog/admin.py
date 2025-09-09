from django.contrib import admin

from gchub_db.apps.joblog.models import JobLog


class JobLogAdmin(admin.ModelAdmin):
    list_display = ("job", "item", "type", "user", "event_time", "log_text")
    list_filter = ("type",)
    date_hierarchy = "event_time"
    ordering = ("-event_time",)
    search_fields = ["job__id"]
    # TODO: Read-only fields.
    exclude = (
        "job",
        "item",
    )


admin.site.register(JobLog, JobLogAdmin)
