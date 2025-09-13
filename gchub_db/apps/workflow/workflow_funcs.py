"""Functions used throughout the workflow app."""

from django.core.cache import cache
import hashlib
import json


def recalc_bev_nomenclature(
    size,
    bev_itemcolorcode,
    printlocation,
    platepackage,
    bev_alt_code,
    bev_center_code,
    bev_liquid_code,
    prepress_supplier,
):
    """
    Separating this out so both the model and Javascript can access.
    Need to be able to calculate without attachment to an existing item
    Build the Evergreen nomenclature from size/color, center code, & end code.
    """
    # Create a cache key from all the parameters
    cache_key_data = {
        "size_id": size.id if size else None,
        "bev_itemcolorcode_id": bev_itemcolorcode.id if bev_itemcolorcode else None,
        "printlocation_id": printlocation.id if printlocation else None,
        "platepackage_id": platepackage.id if platepackage else None,
        "bev_alt_code": bev_alt_code,
        "bev_center_code_id": bev_center_code.id if bev_center_code else None,
        "bev_liquid_code_id": bev_liquid_code.id if bev_liquid_code else None,
        "prepress_supplier": prepress_supplier,
    }

    # Create a hash of the parameters for the cache key
    cache_key = "bev_nomenclature_" + hashlib.md5(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Calculate the result
    result = _calc_bev_nomenclature(
        size,
        bev_itemcolorcode,
        printlocation,
        platepackage,
        bev_alt_code,
        bev_center_code,
        bev_liquid_code,
        prepress_supplier,
    )

    # Cache the result for 1 hour
    cache.set(cache_key, result, 3600)
    return result


def _calc_bev_nomenclature(
    size,
    bev_itemcolorcode,
    printlocation,
    platepackage,
    bev_alt_code,
    bev_center_code,
    bev_liquid_code,
    prepress_supplier,
):
    """
    Separating this out so both the model and Javascript can access.
    Need to be able to calculate without attachment to an existing item
    Build the Evergreen nomenclature from size/color, center code, & end code.
    """
    # Note:, 'item_code' refers to the prefix of the nomenclature.

    if printlocation:
        # Handle panel sizes. Nomenclature should read similar to:
        # SV-415-091L or V479-MilkCow-HPT or something...
        if size.is_bev_panel():
            if bev_alt_code:
                # Optional code that analyst can enter for panels.
                item_code = bev_alt_code
            else:
                if platepackage.platemaker.name == "Shelbyville":
                    item_code = "SV"
                elif platepackage.platemaker.name == "Hughes":
                    item_code = "HU"
                else:
                    item_code = "Panel"
            nomenclature = item_code + "-" + str(bev_center_code.code) + "-" + str(bev_liquid_code.code)
        # Else, assume carton.
        else:
            # Raleigh is the only plant with a BHS press, and it gets different nomenclature.
            if printlocation.plant.name in ("Kalamazoo", "Framingham", "Turlock", "Raleigh") and printlocation.press.name != "BHS":
                # This will be the majority of items.
                if bev_itemcolorcode:
                    # Looksup a alphanumeric code based on the size and the number of colors.
                    item_code = bev_itemcolorcode.code
                else:
                    item_code = "Carton"
                nomenclature = item_code
                # Append center code if given one.
                if bev_center_code:
                    nomenclature = nomenclature + "-" + str(bev_center_code.code)
                # Append end/liquid code if given one.
                if bev_liquid_code:
                    nomenclature = nomenclature + "-" + str(bev_liquid_code.code)
            # Items printing in Plant City & Raleigh BHS have entirely different naming. Oh boy!
            elif printlocation.plant.name in ("Plant City"):
                # Plant city names their items with codes like, '1145'
                try:
                    item_code = bev_alt_code
                except Exception:
                    item_code = "HE Carton"
                nomenclature = item_code
            elif printlocation.plant.name in ("Raleigh") and printlocation.press.name == "BHS":
                # Use the alt code as the item prefix, then append the prepress supplier code.
                try:
                    item_code = bev_alt_code
                except Exception:
                    item_code = "HE Carton"
                # Work done through Clemson/Optihue.
                if prepress_supplier in ("Optihue", "", None, "OPT"):
                    supplier_code = "CGH"
                # Work done through Phototype
                elif prepress_supplier in ("Phototype", "PHT"):
                    supplier_code = "PT"
                # Work done through Shawk or South Graphics.
                elif prepress_supplier in ("Southern Graphics", "SGS", "SHK"):
                    supplier_code = "ST"
                else:
                    supplier_code = ""
                nomenclature = item_code + supplier_code
            else:
                nomenclature = "ERROR"
    else:
        # Set a default error code in event of total failure to calculate.
        nomenclature = "No Print Location"

    return nomenclature
