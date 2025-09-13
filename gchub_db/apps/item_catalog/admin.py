from django.contrib import admin

from gchub_db.apps.item_catalog.models import ProductSubCategory


class ProductSubCategoryAdmin(admin.ModelAdmin):
    list_display = ("main_category", "sub_category")


admin.site.register(ProductSubCategory, ProductSubCategoryAdmin)
