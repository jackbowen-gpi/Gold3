"""Admin interface models. Automatically detected by admin.autodiscover()."""

from django.contrib import admin

from .models import BoxItem, BoxItemSpec, GeneratedBox, GeneratedLabel


class BoxItemSpecInline(admin.TabularInline):
    model = BoxItemSpec


class BoxItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "english_description", "french_description", "active")
    ordering = ("item_name",)
    search_fields = ["item_name"]
    inlines = [BoxItemSpecInline]


admin.site.register(BoxItem, BoxItemAdmin)


class GeneratedBoxAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item",
        "spec",
        "plant",
        "six_digit_num",
        "nine_digit_num",
        "approved",
        "job",
    )
    ordering = ("-id",)


admin.site.register(GeneratedBox, GeneratedBoxAdmin)


class GeneratedLabelAdmin(admin.ModelAdmin):
    list_display = ("id", "nine_digit_num", "fourteen_digit_num")
    ordering = ("-id",)


admin.site.register(GeneratedLabel, GeneratedLabelAdmin)
