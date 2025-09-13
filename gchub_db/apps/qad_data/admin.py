from django.contrib import admin

from gchub_db.apps.qad_data.models import QAD_CasePacks, QAD_PrintGroups


class QAD_PrintGroupsAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


admin.site.register(QAD_PrintGroups, QAD_PrintGroupsAdmin)


class QAD_CasePacksAdmin(admin.ModelAdmin):
    search_fields = ["size__size", "case_pack"]
    ordering = ("size", "case_pack")
    list_display = ("size", "case_pack")


admin.site.register(QAD_CasePacks, QAD_CasePacksAdmin)
