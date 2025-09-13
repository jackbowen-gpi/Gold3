"""Finds BoxItem objects that have no associated BoxItemSpec objects."""

import os
import sys

# Setup the Django environment
sys.path.insert(0, "../../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
from gchub_db.apps.auto_corrugated.models import BoxItem


def main():
    for boxitem in BoxItem.objects.all():
        num_specs = boxitem.boxitemspec_set.count()
        if num_specs < 1:
            print("%s (#%d)" % (boxitem.item_name, boxitem.id))


if __name__ == "__main__":
    main()
