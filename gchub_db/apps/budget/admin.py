from django.contrib import admin

from gchub_db.apps.budget.models import Budget, InvoiceAmt


class BudgetAdmin(admin.ModelAdmin):
    list_display = ("year", "workflow")


admin.site.register(Budget, BudgetAdmin)


class InvoiceAmtAdmin(admin.ModelAdmin):
    list_display = ("budget",)


admin.site.register(InvoiceAmt, InvoiceAmtAdmin)
