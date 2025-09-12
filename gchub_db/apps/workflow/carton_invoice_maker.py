#!/usr/bin/python
import os
from datetime import date

from django.conf import settings
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Group
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from svglib.svglib import svg2rlg

from gchub_db.apps.workflow.models import Charge, Item, Job

# Variables.
LINE_SPACING = 0.2

# Set X coordinates for columns on the invoice.
COLUMN_ONE_X = 0.5
COLUMN_TWO_X = 1.65
COLUMN_THREE_X = 6.6


def generate_carton_invoice(save_destination, job_id, item_list):
    """
    Generates PDF invoices for every item in the item_list. Each item gets it's
    own page. Items with too many charges for one page can span multiple pages.

    The item list contains database IDs for each item like this:
    ['26099621', '26099622', '26099623']
    """
    # Gather the listed items in the job.
    items = Item.objects.filter(id__in=item_list)
    job = Job.objects.get(id=job_id)

    # Setup the document.
    c = canvas.Canvas(save_destination, pagesize=letter)

    # Make a page for each item.
    for item in items:
        # Page counter. Used for labeling if the item spans multiple pages.
        page = 1

        # Draw the top of the page.
        draw_header(c)
        # Draw the middle with the job info.
        draw_job_info(c, job, item, page)

        # Iterate through charges for the item.
        y_cursor = 6.750  # Starting point for all line items to be written. Higher is up.
        c.setFont("Helvetica", 12)

        charges = Charge.objects.filter(item=item).order_by("creation_date")
        total = 0

        # Draw the charges. We'll track how much space we're using up.
        for charge in charges:
            # Save were the charge should start while we check how tall it ends
            # up being with comments.
            y_cursor_charge_start = y_cursor

            if charge.comments:  # Let's see if we have room for the comments.
                # Move the cursor down.
                y_cursor -= LINE_SPACING
                # Make a paragraph for the comment so we can wrap long text.
                styleSheet = getSampleStyleSheet()
                style = styleSheet["BodyText"]
                p = Paragraph("- " + charge.comments, style)
                INDNT_COLUMN_TWO_X = COLUMN_TWO_X + 0.25
                # Available width.
                avail_width = COLUMN_THREE_X - INDNT_COLUMN_TWO_X
                # Check height left. Invoice box ends a 0.75 inches from the bottom.
                avail_height = y_cursor - 0.75
                # Wrap the paragraph and see how tall it is.
                w, h = p.wrap(avail_width * inch, avail_height * inch)
                # Move the cursor down to make room for the wrapped paragraph.
                y_cursor -= h / inch
                # Check height left. Invoice box ends a 0.75 inches from the bottom.
                avail_height = y_cursor - 0.75
                if avail_height <= 0:  # Start a new page if comments won't fit.
                    # Move the y cursor back up to the start.
                    y_cursor = 6.750
                    page += 1
                    # New page
                    next_page(c, job, item, page)
                    # Now draw the charge.
                    # Date
                    c.drawString(
                        (COLUMN_ONE_X + 0.05) * inch,
                        y_cursor * inch,
                        "%s" % charge.creation_date.strftime("%m/%d/%Y"),
                    )
                    # Description
                    c.drawString(
                        (COLUMN_TWO_X + 0.05) * inch,
                        y_cursor * inch,
                        "%s" % charge.description,
                    )
                    # Price
                    c.drawRightString(7.95 * inch, y_cursor * inch, "${:,.2f}".format(charge.amount))
                    total += charge.amount
                    # Move the cursor down to make room for the wrapped paragraph.
                    y_cursor -= LINE_SPACING
                    y_cursor -= h / inch
                    # Comment
                    p.drawOn(c, INDNT_COLUMN_TWO_X * inch, y_cursor * inch)
                else:  # Draw the charge on this page since there's room.
                    # Date
                    c.drawString(
                        (COLUMN_ONE_X + 0.05) * inch,
                        y_cursor_charge_start * inch,
                        "%s" % charge.creation_date.strftime("%m/%d/%Y"),
                    )
                    # Description
                    c.drawString(
                        (COLUMN_TWO_X + 0.05) * inch,
                        y_cursor_charge_start * inch,
                        "%s" % charge.description,
                    )
                    # Price
                    c.drawRightString(
                        7.95 * inch,
                        y_cursor_charge_start * inch,
                        "${:,.2f}".format(charge.amount),
                    )
                    total += charge.amount
                    # Comment
                    p.drawOn(c, INDNT_COLUMN_TWO_X * inch, y_cursor * inch)
            else:  # No comments
                # Date
                c.drawString(
                    (COLUMN_ONE_X + 0.05) * inch,
                    y_cursor_charge_start * inch,
                    "%s" % charge.creation_date.strftime("%m/%d/%Y"),
                )
                # Description
                c.drawString(
                    (COLUMN_TWO_X + 0.05) * inch,
                    y_cursor_charge_start * inch,
                    "%s" % charge.description,
                )
                # Price
                c.drawRightString(
                    7.95 * inch,
                    y_cursor_charge_start * inch,
                    "${:,.2f}".format(charge.amount),
                )
                total += charge.amount

            # Check height left.
            avail_height = y_cursor - 0.75  # Invoice box ends a 0.75 inches from the bottom.
            avail_height -= LINE_SPACING * 3  # Minimum height for another comment.
            if avail_height <= 0:  # Start a new page if there's no room.
                # Move the y cursor back up.
                y_cursor = 6.750
                page += 1
                next_page(c, job, item, page)
            else:  # Plenty of room. Drop the y cursor for the next charge.
                y_cursor -= LINE_SPACING * 2

        # Draw total box.
        c.line(COLUMN_ONE_X * inch, 0.75 * inch, 8 * inch, 0.75 * inch)
        c.line(COLUMN_THREE_X * inch, 0.75 * inch, COLUMN_THREE_X * inch, 0.55 * inch)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString((COLUMN_THREE_X - 0.05) * inch, 0.6 * inch, "Total:")
        c.drawRightString(7.95 * inch, 0.6 * inch, "${:,.2f}".format(total))
        c.line(COLUMN_ONE_X * inch, 0.55 * inch, 8 * inch, 0.55 * inch)

        # Save this page and start a new one.
        c.showPage()

    # All items done. Close and save the PDF.
    c.save()


def draw_header(c):
    """Draws everything above the job number and name."""
    # Draw GPI log top left
    file_path = os.path.join(settings.MEDIA_ROOT, "img/GPI_Black_logo.svg")
    graphic = svg2rlg(file_path)
    d = Drawing()
    graphic_group = Group(graphic)
    d.add(graphic_group)
    renderPDF.draw(d, c, 0.5 * inch, 10 * inch)

    # GCHub address to right
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(8 * inch, 10.5 * inch, "Graphic Communications Hub Invoice")
    c.setFont("Helvetica", 12)
    c.drawRightString(8 * inch, 10.25 * inch, "155 Old Greenville Hwy")
    c.drawRightString(8 * inch, 10.05 * inch, "Suite 103")
    c.drawRightString(8 * inch, 9.85 * inch, "Clemson, SC 29631")
    c.drawRightString(8 * inch, 9.65 * inch, "p: 864.633.6000")
    c.drawRightString(8 * inch, 9.45 * inch, "e: gchub.clemson@graphicpkg.com")

    # Line (x1,y1,x2,y2)
    c.line(0.5 * inch, 9.3 * inch, 8 * inch, 9.3 * inch)


def draw_job_info(c, job, item, page=None):
    """
    Draws the job info in the middle of the page and a blank invoice datail
    block at the bottom.
    """
    c.setFont("Helvetica-Bold", 14)
    c.drawString(0.5 * inch, 9 * inch, "%s-%s %s" % (str(job.id), str(item.num_in_job), job.name))

    # Left column
    c.setFont("Helvetica", 12)
    c.drawString(0.5 * inch, 8.7 * inch, "Date: %s" % (date.today().strftime("%m/%d/%Y")))
    c.drawString(0.5 * inch, 8.5 * inch, "GOLD Job Number: %s" % (str(job.id)))
    c.drawString(0.5 * inch, 8.3 * inch, "GOLD Job Name: %s" % (job.name))
    c.drawString(0.5 * inch, 8.1 * inch, "Graphic PO # : %s" % (item.graphic_po))
    c.drawString(0.5 * inch, 7.9 * inch, "Customer: %s" % (job.customer_name))
    c.drawString(0.5 * inch, 7.7 * inch, "Customer Contact: %s" % (job.customer_name))

    # Right column
    c.setFont("Helvetica", 12)
    c.drawString(5 * inch, 8.7 * inch, "GPI Sales: %s" % (job.salesperson))
    c.drawString(5 * inch, 8.5 * inch, "GPI CSR: %s" % (job.csr))
    c.drawString(5 * inch, 8.3 * inch, "SAP Payer: %s" % (job.customer_identifier))

    # Details
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(4.25 * inch, 7.3 * inch, "INVOICE DETAILS (Page %s)" % page)
    c.line(3.0 * inch, 7.25 * inch, 5.5 * inch, 7.25 * inch)

    # Build the headers.
    c.setFont("Helvetica-Bold", 14)
    c.drawString((COLUMN_ONE_X + 0.05) * inch, 7 * inch, "Date")
    c.drawString((COLUMN_TWO_X + 0.05) * inch, 7 * inch, "Description")
    c.drawString((COLUMN_THREE_X + 0.05) * inch, 7 * inch, "Price (USD)")
    c.line(COLUMN_ONE_X * inch, 6.95 * inch, 8 * inch, 6.95 * inch)

    # Vertical lines, left to right.
    c.line(COLUMN_ONE_X * inch, 6.95 * inch, COLUMN_ONE_X * inch, 0.55 * inch)
    c.line(COLUMN_TWO_X * inch, 6.95 * inch, COLUMN_TWO_X * inch, 0.75 * inch)
    c.line(COLUMN_THREE_X * inch, 6.95 * inch, COLUMN_THREE_X * inch, 0.75 * inch)
    c.line(8 * inch, 6.95 * inch, 8 * inch, 0.55 * inch)


def next_page(c, job, item, page=None):
    """Used when an item can't fit on one page and we need to span it to the next."""
    # Draw a "see next page" note at the bottom of the current page.
    c.line(COLUMN_ONE_X * inch, 0.75 * inch, 8 * inch, 0.75 * inch)
    c.drawRightString(7.95 * inch, 0.6 * inch, "Continued on next page...")
    c.line(COLUMN_ONE_X * inch, 0.55 * inch, 8 * inch, 0.55 * inch)

    # Save this page and start a new one.
    c.showPage()
    # Draw the top of the page.
    draw_header(c)
    # Draw the middle with the job info.
    draw_job_info(c, job, item, page)
    # Set the font back.
    c.setFont("Helvetica", 12)
