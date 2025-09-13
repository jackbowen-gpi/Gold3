# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from gchub_db.apps.timesheet.models import TimeSheet, TimeSheetCategory


class TimeSheetAdmin(admin.ModelAdmin):
    list_display = ("job", "artist", "date", "category", "hours")
    ordering = ("date",)
    exclude = ("job",)


admin.site.register(TimeSheet, TimeSheetAdmin)


class TimeSheetCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "order")
    ordering = ("order",)


admin.site.register(TimeSheetCategory, TimeSheetCategoryAdmin)
