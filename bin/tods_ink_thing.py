#!/usr/bin/env python
"""Tod smells funny."""

import datetime
from datetime import timedelta

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from colormath.color_objects import RGBColor

from gchub_db.apps.workflow.models import Item, Press


def main():
    """
    Entry point: compute and print ink metrics for recent items.

    Prints summary info for manual inspection.
    """
    # Limit just to the FK press.
    fk_press = Press.objects.get(name="FK")

    # Limit the scope of this to about 6 months ago.
    today = datetime.date.today()
    entry_date_start_time = today + timedelta(weeks=(-4 * 6))

    # Find matching items.
    items = Item.objects.filter(printlocation__press=fk_press, creation_date__gte=entry_date_start_time).order_by(
        "job__id", "num_in_job"
    )

    for item in items:
        print("%d-%d %s" % (item.job.id, item.num_in_job, item.size.size))
        original_num_colors = item.itemcolor_set.count()
        if original_num_colors == 0:
            continue

        print(" @ Original # colors:", original_num_colors)
        for ic in item.itemcolor_set.all():
            print(" * %s" % ic.color)
            print("   Hex: %s" % ic.hexvalue)
            ic_rgb = RGBColor()
            ic_rgb.set_from_rgb_hex(ic.hexvalue)
            print("  ", ic_rgb)

            # Convert RGB to CMYK.
            ic_cmyk = ic_rgb.convert_to("cmyk")
            print("  ", ic_rgb.convert_to("cmy"))
            print("  ", ic_cmyk)
            print("   Coverage in^2: %f" % ic.coverage_sqin)

            c_ink_area = float(str(ic.coverage_sqin)) * ic_cmyk.cmyk_c
            m_ink_area = float(str(ic.coverage_sqin)) * ic_cmyk.cmyk_m
            y_ink_area = float(str(ic.coverage_sqin)) * ic_cmyk.cmyk_y
            k_ink_area = float(str(ic.coverage_sqin)) * ic_cmyk.cmyk_k

            print("    C in^2: %.2f" % c_ink_area)
            print("    M in^2: %.2f" % m_ink_area)
            print("    Y in^2: %.2f" % y_ink_area)
            print("    K in^2: %.2f" % k_ink_area)

        # Killing this after one item until testing concludes.
        break


if __name__ == "__main__":
    main()
