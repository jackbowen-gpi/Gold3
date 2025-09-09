from django.contrib import admin

from gchub_db.apps.sbo.models import SBO


class SBOAdmin(admin.ModelAdmin):
    list_display = (
        "observed",
        "date_added",
        "date_observed",
        "observer",
        "task",
        "behavior",
        "behavior_type",
        "reason",
        "communication",
        "describe_communication",
        "additional_comments",
    )
    ordering = ("date_added",)


admin.site.register(SBO, SBOAdmin)
