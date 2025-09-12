"""Sets all FSB items in the catalog to active."""

import os
import sys

# Setup the Django environment
sys.path.insert(0, "../../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
from gchub_db.apps.item_catalog.models import ProductSubCategory
from gchub_db.apps.workflow.models import ItemCatalog

HOT_CUPS = [
    "SMR-4",
    "SMR-6",
    "SMR-6",
    "SMR-10",
    "SMM-10",
    "SMR-12",
    "SMR-16",
    "SMR-20",
    "SMT-24",
    "SMRH-10",
    "SMRH-4",
    "SMRH-6",
    "SMRH-8",
]
HOT_CUP_LIDS = [
    "LHRM-4",
    "LHRL-6",
    "LHRL-8",
    "LHRDS-8",
    "LHRDSB-8",
    "LHRL-10",
    "LHRDS-10",
    "LHRDSB-10",
    "LHRL-16",
    "LHRDS-16",
    "LHRDSB-16",
    "LHRLB-16",
]
KX2_HOT_CUPS = ["IMR-12", "IMR-16", "IMR-20"]
KX2_LIDS = ["LHIDS-16", "LHIDSB-16", "LHIL-16"]
ECOTAINER_HOT_CUPS = ["SMRE-4", "SMRE-8", "SMME-10", "SMRE-12", "SMRE-16", "SMRE-20"]
VENDING_HOT_CUPS = ["SVR-8", "SVR-10", "SVR-12", "SVS-12"]
VENDING_HOT_CUP_LIDS = ["LHSL-8", "LHSL-9", "LHSL-12"]
CUP_BUDDY = ["RSW-20", "RSK-20"]
CUP_CARRIERS = ["FCD-191025", "FCD-181822"]
PAPER_COLD_CUPS = [
    "DMR-4",
    "DMR-5",
    "DMR-7",
    "DMR-9",
    "DMM-10",
    "DMR-12",
    "DMS-12",
    "DMR-16",
    "DMT-16",
    "DMR-18",
    "DMT-20",
    "DMR-22",
    "DMT-24",
    "DMR-30",
    "DMR-32",
    "DMR-42",
    "DMT-44",
]
PAPER_COLD_LIDS = [
    "LCRS-7",
    "LCRS-9",
    "LCMS-10",
    "LCRS-12",
    "LCRS-22",
    "LCRO-22",
    "LCRDO-22",
    "LCRSA-22",
    "LCRS-32",
    "LCRSL-32",
    "LCRO-32",
    "LCRDO-32",
    "LCRSA-32",
    "LCTS-44",
    "LCTSL-44",
    "LCTDO-44",
    "LCTSA-44",
]
ECOTAINER_COLD_CUPS = ["DMRE-16", "DMRE-22", "DMRE-32", "DMRE-9"]
PLASTIC_CAR_CUPS = ["PTM-32", "PTM-44"]
PLASTIC_CAR_CUP_LIDS = ["LCRS-32", "LCRDO-32", "LCTSL-44"]
CLEAR_PLASTIC_COLD_CUPS = [
    "PMRK-10",
    "PMRK-12",
    "PMRK-20",
    "PMRK-16",
    "PMRK-24",
    "PMRK-32",
]
CLEAR_PLASTIC_COLD_LID = [
    "LPRSA-10",
    "LPRSA-20",
    "LPRDO-20",
    "LPRSA-24",
    "LPRDO-24",
    "LPRSA-32",
    "LPRDO-32",
]
PAPER_VENDING_COLD_CUPS = ["DVR-12"]
VENDING_COLD_LIDS = ["LHSL-9"]
CUP_CARRIER = ["FCD-191025"]
FOOD_CONTAINERS = [
    "DFR-3",
    "DFR-4",
    "DFR-5",
    "DFR-6",
    "DFR-8",
    "DFR-10",
    "DFT-16",
    "DFR-12",
    "DFS-16",
    "DFR-32",
]
FOOD_CONTAINER_COMBO_PACKS = ["DFRC-8", "DFTC-16", "DFRC-12", "DFSC-16", "DFRC-32"]
ECOTAINER_FOOD_CONTAINERS = ["DFRE-8", "DFRE-12", "DFSE-16", "DFRE-32"]
FOOD_CONTAINER_LIDS = [
    "LFRD-3",
    "LFRFA-3",
    "LFRFHM-4",
    "LFRFA-4",
    "LFRD-5",
    "LFRFA-5",
    "LFRD-10",
    "LFRD-12",
    "LFRFH-12",
    "LFRFHB-12",
    "LFRFHP-12",
    "LFTFA-16",
    "LFTFH-16",
    "LFTFHB-16",
    "LFTFHP-16",
    "LFRFA-32",
    "LFRD-32",
    "LFRFH-32",
    "LFRFHB-32",
    "LFRFHP-32",
]
FOOD_BUCKETS_AND_DIVIDERS = ["DFS-54", "DFM-85", "DMM-130", "DFM-170", "FM-130201"]
FOOD_BUCKET_LIDS = [
    "LFRHM-85",
    "LFMD-85",
    "LFRFHK-85",
    "LFRHM-130",
    "LFMD-130",
    "LFRHM-170",
]
POPCORN_CONTAINERS_BAGS = [
    "DMT-24",
    "SFR-32",
    "SFR-46",
    "SFR-64",
    "SFR-85",
    "SFR-130",
    "SFR-170",
    "BFR-46",
    "BFR-85",
    "BFR-130",
    "BFR-170",
]
FRENCH_FRY_SNACK_CONTAINERS = ["DMR-14", "DFF-16", "SFR-32"]
MEDIUM_WEIGHT_PLATES = ["PML-7", "PML-9"]
HEAVY_WEIGHT_PLATES = ["PHL-6", "PHL-7", "PHL-9", "PHL-10"]
WEB_CORNER_CARTONS = ["RW-545250", "RW-663500", "RW-856251", "RW-865350", "RW-856252"]
FORMED_CARTONS = ["RT-16", "RT-48", "RT-80"]
PORTION_CUPS = ["PPR-100", "PPR-200", "PPR-325", "PPR-400"]
PORTION_CUP_LIDS = ["LPP-1", "LPP-2", "LPP-4/5"]


def main():
    """
    For boxitem in BoxItem.objects.exclude(item_name=''):
    try:
        itemcat = ItemCatalog.objects.get(size=boxitem.item_name)
    except ItemCatalog.DoesNotExist:
        print("No ItemCatalog match: %s" % boxitem.item_name)
        itemcat = None
    boxitem.item = itemcat
    boxitem.save()
    """
    category = "Hot Cups"
    dict = HOT_CUPS
    try:
        prodcat = ProductSubCategory.objects.get(sub_category=category)
        for item in dict:
            try:
                itemcat = ItemCatalog.objects.get(size=item)
            except ItemCatalog.DoesNotExist:
                print(("No ItemCatalog match: %s" % item))
                continue
            itemcat.product_category = prodcat
            itemcat.save()
            print(("Saved:", itemcat))
    except ProductSubCategory.DoesNotExist:
        print(("No SubCategory match: %s" % category))


if __name__ == "__main__":
    main()
