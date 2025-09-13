from django.contrib import admin

from gchub_db.apps.qc.models import (
    QCCategory,
    QCQuestionDefinition,
    QCResponse,
    QCResponseDoc,
    QCWhoops,
)


class QCQuestionDefinitionAdmin(admin.ModelAdmin):
    list_display = ("workflow", "category", "order", "question", "help_url")


admin.site.register(QCQuestionDefinition, QCQuestionDefinitionAdmin)


class QCCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "order")


admin.site.register(QCCategory, QCCategoryAdmin)


class QCResponseDocAdmin(admin.ModelAdmin):
    list_display = ("job", "reviewer", "review_date")
    search_fields = [
        "job__id",
        "reviewer__username",
        "reviewer__first_name",
        "reviewer__last_name",
    ]


admin.site.register(QCResponseDoc, QCResponseDocAdmin)


class QCResponseAdmin(admin.ModelAdmin):
    list_display = ("qcdoc", "category", "response", "comments")
    exclude = ("qcdoc",)
    search_fields = ["qcdoc__job__id"]


admin.site.register(QCResponse, QCResponseAdmin)


class QCWhoopsAdmin(admin.ModelAdmin):
    list_display = (
        "qc_response",
        "details",
        "reported_date",
        "is_valid",
        "resolution_date",
    )
    exclude = ("qcdoc",)
    search_fields = ["qc_response__qcdoc__job__id"]


admin.site.register(QCWhoops, QCWhoopsAdmin)
