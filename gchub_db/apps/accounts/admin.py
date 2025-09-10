from django.contrib import admin

from gchub_db.apps.accounts.models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone_number", "last_page_request")
    search_fields = ["user__username", "user__first_name", "user__last_name"]


admin.site.register(UserProfile, UserProfileAdmin)

# Customize admin site
admin.site.site_header = "GHub Database Administration"
admin.site.site_title = "GHub Admin"
admin.site.index_title = "Welcome to GHub Administration"
