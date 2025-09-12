"""This module contains generally useful utility functions."""

from reportlab.lib.colors import CMYKColor
from reportlab.lib.textsplit import getCharWidths


def check_text_width(type_size, font, text):
    """
    Return the total width of a given type size in inches.

    type_size: (int) Type size, in points.
    font: (str) Font name.
    text: (str) The string to check.

    Returns a value in inches.
    """
    # This returns a list of sizes for each character.
    item_name_width = getCharWidths(text, font, type_size)
    # Sum the list for the total width.
    total_width = sum(item_name_width)
    # Convert points to inches.
    return total_width / 72.0


def __loop_through_contents(obj, color):
    """Loop through the contents of an object, if it has any."""
    try:
        for sub_obj in obj.contents:
            __loop_through_contents(sub_obj, color)
    # If the object does not have the attribute color, it's a Shape object,
    # not a Group object, and should therefore be colored.
    except AttributeError:
        obj.setProperties({"fillColor": color})


def convert_svg_to_color(object, color=CMYKColor(0, 0, 0, 1.0)):
    """Iterate through all the objects of an SVG and convert them to black CMYK."""
    __loop_through_contents(object, color)
