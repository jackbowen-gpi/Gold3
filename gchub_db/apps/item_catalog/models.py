"""Item Catalog models. Used for management of items, specs, etc..."""

from django.db import models

from gchub_db.apps.workflow.app_defs import *


class ProductSubCategory(models.Model):
    """Subcategories of products."""

    main_category = models.IntegerField(choices=PRODUCT_CATEGORIES)
    sub_category = models.CharField(unique=True, max_length=69)

    class Meta:
        app_label = "item_catalog"
        verbose_name_plural = "Product Subcategory"
        ordering = ["sub_category"]
        ordering = ["main_category", "sub_category"]

    def __str__(self):
        return str(self.get_main_category_display()) + " - " + str(self.sub_category)
