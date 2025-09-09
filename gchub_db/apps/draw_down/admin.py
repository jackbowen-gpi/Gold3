from django.contrib import admin

from gchub_db.apps.draw_down.models import Drawdown, DrawDownItem, DrawDownRequest


class DrawdownAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "job_number",
        "requested_by",
        "print_location",
        "creation_date",
        "date_needed",
        "request_complete",
    )
    search_fields = [
        "customer_name",
        "job_number",
        "print_location__plant__name",
        "print_location__press__name",
    ]


admin.site.register(Drawdown, DrawdownAdmin)


class DrawDownRequestAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "job_number",
        "requested_by",
        "creation_date",
        "date_needed",
        "request_complete",
    )
    search_fields = ["customer_name", "job_number"]


admin.site.register(DrawDownRequest, DrawDownRequestAdmin)


class DrawDownItemAdmin(admin.ModelAdmin):
    list_display = ("item_number", "print_location")
    search_fields = ["print_location__plant__name", "print_location__press__name"]


admin.site.register(DrawDownItem, DrawDownItemAdmin)
