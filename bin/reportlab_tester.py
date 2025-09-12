#!/usr/bin/python
"""Generate a test PDF using ReportLab and SVG conversion helpers.

Creates a sample PDF file demonstrating barcode and SVG rendering.
"""

import os

import bin_functions

bin_functions.setup_paths()
from django.conf import settings
from reportlab.graphics import barcode, renderPDF
from reportlab.graphics.shapes import Drawing, Group
from reportlab.lib import pdfencrypt
from reportlab.lib.colors import CMYKColor
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from svglib import svglib


def __loop_through_contents(obj, color):
    """Loop through the contents of an object and apply a color.

    Recurses into Group-like objects and sets fillColor on shapes.
    """
    try:
        for sub_obj in obj.contents:
            __loop_through_contents(sub_obj, color)
    # If the object does not have the attribute color, it's a Shape object,
    # not a Group object, and should therefore be colored.
    except AttributeError:
        obj.setProperties({"fillColor": color})


def convert_svg_to_color(object, color=CMYKColor(0, 0, 0, 1.0)):
    """Iterate through all the objects of an SVG and convert them to black CMYK."""
    print("Begin SVG color conversion...")
    __loop_through_contents(object, color)


# Setup the document.
print("Generating PDF...")
# Add encryption to the PDF so that it cannot be printed.
enc = pdfencrypt.StandardEncryption(
    "", canPrint=0, canModify=0, canCopy=0, canAnnotate=0
)
c = canvas.Canvas("reportlab_testfile.pdf", encrypt=None)

# START DRAWING BARCODE
color = CMYKColor(0, 1, 0, 0)
# Setup all the headers for the invoice.
c.setFont("Helvetica-Bold", 16)
c.drawString(0.8 * inch, 10.5 * inch, "Reportlab Test File")
bcode_draw = barcode.createBarcodeDrawing(
    "Code128",
    barFillColor=color,
    width=4 * inch,
    height=1 * inch,
    quiet=False,
    barWidth=0.0085 * inch,
    value="12345678",
)

drawing = Drawing()
drawing.add(bcode_draw)
renderPDF.draw(drawing, c, 1 * inch, 1 * inch)

color_spot = CMYKColor(0, 0, 0, 0.40, spotName="Template")
c.setFillColor(color_spot)
c.rect(0.25 * inch, 0.25 * inch, 5.0 * inch, 5.0 * inch, fill=1)

# START DRAWING SVG ELEMENT.
drawing_graphic = Drawing()
# Import SVG graphic file.
CORRUGATED_MEDIA_DIR = os.path.join(settings.MEDIA_ROOT, "autocorr_elements")
vector_graphic = svglib.svg2rlg(os.path.join(CORRUGATED_MEDIA_DIR, "svgtest.svg"))


class InvalidPath(Exception):
    pass


if not vector_graphic:
    raise InvalidPath()

# Calculate the width of this element.
width = vector_graphic.getProperties()["width"] / 72.0
# Calculate the height of this element.
height = vector_graphic.getProperties()["height"] / 72.0
print("Graphic start width:", width)
print("Graphic start height:", height)

# vector_graphic.__setattr__('fillColor', '(0,1,0,0)')
# vector_graphic.contents[0].contents[0].contents[0].contents[0].setProperties({'fillColor': CMYKColor(0,0,0,1)})
convert_svg_to_color(vector_graphic)

# Place the graphic in a group to perform scaling.
graphic_group = Group(vector_graphic)

# Draw the graphic, ready for placement.
drawing_graphic.add(graphic_group)
renderPDF.draw(drawing_graphic, c, 1 * inch, 4 * inch)
# c.drawImage("test_tiffs/57941-1 X4-A012-003_354.tif", 1.0, 1.0)

# EPS ELEMENT
# drawing_graphic = Drawing()
# eps_graphic_path = os.path.join(CORRUGATED_MEDIA_DIR, 'ip_logo.eps')
# renderPS.draw(drawing_graphic, c, 1 * inch, 4 * inch)

# c.drawImage(eps_graphic_path, 1*inch, 4*inch)

# Close and save the PDF
c.showPage()

c.save()
