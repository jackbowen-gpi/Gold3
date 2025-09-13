from django.contrib import admin

from gchub_db.apps.admin_log.models import AdminLog


class AdminLogAdmin(admin.ModelAdmin):
    date_hierarchy = "event_time"
    list_display = ("event_time", "type", "origin", "log_text")
    list_filter = ("type", "event_time")
    ordering = ("-event_time",)
    search_fields = ["log_text"]


admin.site.register(AdminLog, AdminLogAdmin)
