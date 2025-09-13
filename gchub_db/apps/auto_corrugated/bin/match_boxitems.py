"""Matches BoxItem objects to ItemCatalog objects."""

import os
import sys

# Setup the Django environment
sys.path.insert(0, "../../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
from gchub_db.apps.auto_corrugated.models import BoxItem
from gchub_db.apps.workflow.models import ItemCatalog


def main():
    for boxitem in BoxItem.objects.exclude(item_name=""):
        try:
            itemcat = ItemCatalog.objects.get(size=boxitem.item_name)
        except ItemCatalog.DoesNotExist:
            print("No ItemCatalog match: %s" % boxitem.item_name)
            itemcat = None
        boxitem.item = itemcat
        boxitem.save()


if __name__ == "__main__":
    main()
