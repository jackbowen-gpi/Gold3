from django.contrib import admin

from gchub_db.apps.color_mgt.models import ColorDefinition


class ColorDefinitionAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = (
        "name",
        "lab_l",
        "lab_a",
        "lab_b",
        "hexvalue",
        "coating",
        "pantone_plus",
        "do_compare",
    )
    list_filter = ("coating", "pantone_plus")


admin.site.register(ColorDefinition, ColorDefinitionAdmin)
