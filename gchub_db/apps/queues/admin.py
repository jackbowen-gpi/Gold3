from django.contrib import admin

from gchub_db.apps.queues.models import *


class ColorKeyQueueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item",
        "item_job",
        "date_queued",
        "date_processed",
        "number_of_attempts",
    )
    list_display_links = ("id", "item")

    def item_job(self, obj):
        return "%s - %s" % (obj.item.job, obj.item.num_in_job)


admin.site.register(ColorKeyQueue, ColorKeyQueueAdmin)


class TiffToPDFAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "date_queued", "date_processed")
    list_display_links = ("id", "item")


admin.site.register(TiffToPDF, TiffToPDFAdmin)
