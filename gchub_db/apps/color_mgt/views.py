"""Job and Item search views"""

from django.db.models import Avg, Max, Min
from django.shortcuts import render

from gchub_db.apps.color_mgt.models import ColorDefinition
from gchub_db.apps.workflow.models import ItemColor


def color_home(request):
    """Standard Color Mgt. Data - basic info"""
    data = {}
    colors = ItemColor.objects.filter(
        item__job__workflow__name="Foodservice", delta_e__isnull=False
    )

    # Run aggregate methods on color data.
    agg_colors = colors.aggregate(
        avg=Avg("delta_e"),
        max=Max("delta_e"),
        min=Min("delta_e"),
    )

    data["colors_measured"] = colors.count()
    data["average_delta_e"] = agg_colors["avg"]
    data["max_delta_e"] = agg_colors["max"]
    data["min_delta_e"] = agg_colors["min"]

    pagevars = {
        "page_title": "Color Mgt. Data",
        "data": data,
    }

    return render(request, "color_mgt/home.html", context=pagevars)


def color_stats(request):
    """Returns a list of colors that have actually been measured"""
    colors = ColorDefinition.objects.all()

    colors_used = []

    for x in colors:
        if x.fsb_usage_count() > 0:
            colors_used.append(x)

    pagevars = {
        "page_title": "Color Mgt. Data",
        "data": colors_used,
    }

    return render(request, "color_mgt/color_data.html", context=pagevars)


def color_stats_sorted(request):
    """Sorts measured colors and places them in lists named Red, Yellow, Green, Blue, or Gray based on chroma or hue."""
    color_defs = ColorDefinition.objects.all()

    color_defs_used = []
    grays = []
    reds = []
    yellows = []
    greens = []
    blues = []
    errors = []

    for x in color_defs:
        if x.fsb_usage_count() > 0:
            color_defs_used.append(x)

    for z in color_defs_used:
        if z.lch_c and z.lch_c <= 15.7:
            grays.append(z)
        elif z.lch_h and z.lch_h >= 0 and z.lch_h < 67:
            reds.append(z)
        elif z.lch_h and z.lch_h >= 67 and z.lch_h < 106:
            yellows.append(z)
        elif z.lch_h and z.lch_h >= 106 and z.lch_h < 222:
            greens.append(z)
        elif z.lch_h and z.lch_h >= 222 and z.lch_h < 295:
            blues.append(z)
        elif z.lch_h and z.lch_h >= 295 and z.lch_h < 359.999:
            reds.append(z)
        else:
            errors.append(z)

    # grays.sort(key=lambda grays: grays.lch_h, reverse=False)
    # reds.sort(key=lambda reds: reds.lch_h, reverse=False)
    # yellows.sort(key=lambda reds: reds.lch_h, reverse=False)
    # greens.sort(key=lambda greens: greens.lch_h, reverse=False)
    # blues.sort(key=lambda blues: blues.lch_h, reverse=False)

    pagevars = {
        "page_title": "Color Mgt. Data",
        "grays": grays,
        "reds": reds,
        "yellows": yellows,
        "greens": greens,
        "blues": blues,
        "errors": errors,
    }

    return render(request, "color_mgt/color_data_sort.html", context=pagevars)
