from django.contrib import admin

from gchub_db.apps.news.models import CodeChange


class CodeChangeAdmin(admin.ModelAdmin):
    list_display = ("change", "creation_date")
    search_fields = ["change"]
    date_hierarchy = "creation_date"


admin.site.register(CodeChange, CodeChangeAdmin)
