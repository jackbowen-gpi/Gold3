from django.contrib import admin

from gchub_db.apps.archives.models import KentonArchive, RenMarkArchive


class KentonArchiveAdmin(admin.ModelAdmin):
    list_display = ("file", "cd", "art_reference", "job_name", "item_number")
    search_fields = ["file", "item_number", "job_name", "art_reference"]


admin.site.register(KentonArchive, KentonArchiveAdmin)


class RenMarkArchiveAdmin(admin.ModelAdmin):
    list_display = ("item", "size", "folder_creation", "folder_items")
    search_fields = ["item"]


admin.site.register(RenMarkArchive, RenMarkArchiveAdmin)
