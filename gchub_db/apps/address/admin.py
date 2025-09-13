from django.contrib import admin

from gchub_db.apps.address.models import Contact


class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "job_title",
        "company",
        "city",
        "state",
        "email",
        "active",
    )
    search_fields = ["first_name", "last_name", "email"]


admin.site.register(Contact, ContactAdmin)
