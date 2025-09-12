#!/usr/bin/env python
"""Transfers all associated items from one ItemCatalog object to another."""

import sys
from optparse import OptionParser

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from gchub_db.apps.workflow.models import ItemCatalog


def main():
    """
    Main entry point for transferring items/specs between catalogs.

    Expects two positional arguments: oldid and newid.
    """
    usage = "usage: %prog oldid newid"
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()
    # print options, args

    if len(args) != 2:
        parser.error("incorrect number of arguments (2 required)")

    old_cat = ItemCatalog.objects.get(id=int(args[0]))
    new_cat = ItemCatalog.objects.get(id=int(args[1]))

    print("Old cat: %d %s %s" % (old_cat.id, old_cat, old_cat.mfg_name))
    print("New cat: %d %s %s" % (new_cat.id, new_cat, new_cat.mfg_name))

    matching_items = old_cat.item_set.count()
    print("Searching for items using old cat: %d found" % matching_items)
    matching_specs = old_cat.itemspec_set.count()
    print("Searching for item specs: %d found" % matching_specs)

    if matching_items > 0 or matching_specs > 0:
        do_transfer = input("Transfer items/specs from old to new cat? (y/n) ")
        if do_transfer.lower() == "y":
            for item in old_cat.item_set.all():
                print(" - Item: %s" % item)
                item.size = new_cat
                item.save()
            for spec in old_cat.acts_like_item_set.all():
                print(" - Acts like: %s" % spec)
                spec.acts_like = new_cat
                spec.save()
            for code in old_cat.bevitemcolorcodes_set.all():
                print(" - BevItemColorCode: %s" % code)
                code.size = new_cat
                code.save()
            for spec in old_cat.itemspec_set.all():
                print(" - Spec: %s" % spec)
                spec.size = new_cat
                spec.save()
        else:
            print("Aborting.")
            sys.exit(0)

    do_delete = input("Delete old cat? (y/n) ")
    if do_delete.lower() == "y":
        print("Deleting %s" % old_cat)
        old_cat.delete()


if __name__ == "__main__":
    main()
