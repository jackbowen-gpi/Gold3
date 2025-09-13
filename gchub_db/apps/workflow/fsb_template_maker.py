#!/usr/bin/python
import os

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# Reset the shell's umask so it doesn't mess with NEWFILE_MODE.
os.umask(0)
# Default permissions mask for new files.
NEWFILE_MODE = 777


def generate_fsb_rectangle(rect_width, rect_height, pdf_path="fsb_rectangle_test.pdf"):
    """
    Generate the art rectangle for FSB item. This is where the art will
    be placed before being warped to the dielines.
    """
    # Setup the document.
    c = canvas.Canvas(pdf_path, pagesize=(rect_width * inch, rect_height * inch))
    c.rect(0.0 * inch, 0.0 * inch, rect_width * inch, rect_height * inch, stroke=0, fill=0)
    # Close and save the PDF
    c.showPage()
    c.save()
