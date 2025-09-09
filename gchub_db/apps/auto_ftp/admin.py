from django.contrib import admin

from gchub_db.apps.auto_ftp.models import AutoFTPTiff


class AutoFTPTiffAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item_number",
        "job",
        "destination",
        "date_queued",
        "date_processed",
    )
    list_display_links = ("id", "job")
    exclude = ("job", "items")


admin.site.register(AutoFTPTiff, AutoFTPTiffAdmin)
