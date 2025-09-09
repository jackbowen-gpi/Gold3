#!/usr/bin/python
import os

from django.conf import settings
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Group
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

from gchub_db.apps.bev_billing.models import BevInvoice
from gchub_db.apps.workflow.models import Charge


def generate_pdf_invoice(invoice_id, invoice_pdf):
    """Generate an Invoice for the given invoice id.
    An invoice will only contain charges from one Job.
    """
    invoice = BevInvoice.objects.get(id=invoice_id)

    # Get invoiced charges, plates included.
    invoiced_charges = Charge.objects.filter(bev_invoice=invoice)

    # Let's just double check to make sure that all the charges are
    # for the same job...
    job_test = invoiced_charges[0].item.job
    for charge in invoiced_charges:
        if charge.item.job != job_test:
            print("SOMETHING BAD HAS HAPPENED! MULTIPLE JOBS ON ONE INVOICE!")
            break

    # Separate plate and art charges.
    plate_charges = []
    art_charges = []
    for charge in invoiced_charges:
        if charge.description.type == "Plates" or charge.description.type == "Films":
            plate_charges.append(charge)
        else:
            art_charges.append(charge)

    # Basic setup for PDF invoice.
    LINE_SPACING = 0.105

    # Setup the document.
    c = canvas.Canvas(invoice_pdf, pagesize=letter)

    # Draw GPI log on top left of invoice.
    # file_path = os.path.join(settings.MEDIA_ROOT, 'img/ip_logo.svg')
    file_path = os.path.join(settings.MEDIA_ROOT, "img/GPI_Black_logo.svg")
    graphic = svg2rlg(file_path)
    d = Drawing()
    graphic_group = Group(graphic)
    d.add(graphic_group)
    renderPDF.draw(d, c, 0.5 * inch, 10 * inch)

    # Setup all the headers for the invoice.
    c.setFont("Helvetica-Bold", 16)
    invoice_number = invoice.invoice_number
    c.drawString(5.35 * inch, 10.5 * inch, "INVOICE: %s" % invoice_number)
    c.setFont("Helvetica", 9)
    c.drawString(5.35 * inch, 10.20 * inch, "Clemson Graphic Communications Hub")
    c.drawString(5.35 * inch, 10.05 * inch, "155 Old Greenville Hwy, Suite 103")
    c.drawString(5.35 * inch, 9.9 * inch, "Clemson, SC, 29631")
    c.drawString(5.35 * inch, 9.75 * inch, "P: 864.633.6000  F: 864.653.5168")

    c.rect(0.45 * inch, 8.85 * inch, 7.75 * inch, 0.8 * inch, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(0.5 * inch, 9.5 * inch, "Invoice Date:")
    c.setFont("Helvetica", 9)
    c.drawString(1.35 * inch, 9.5 * inch, "%s" % invoice.qad_entry_date)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(0.5 * inch, 9.35 * inch, "Bill To:")
    c.setFont("Helvetica", 9)
    c.drawString(0.5 * inch, 9.20 * inch, "Evergreen Packaging, Inc.")
    if invoice.job.temp_printlocation:
        if "Kalamazoo" in invoice.job.temp_printlocation.plant.name:
            plant_address = "2315 Miller Rd, Kalamazoo, MI 49001-4140"
        elif "Plant City" in invoice.job.temp_printlocation.plant.name:
            plant_address = "2104 Henderson Way, Plant City, FL 33563-7902"
        elif "Turlock" in invoice.job.temp_printlocation.plant.name:
            plant_address = "500 W Main St., Turlock, CA 95380-3704"
        elif "Raleigh" in invoice.job.temp_printlocation.plant.name:
            plant_address = "2215 S Wilmington St., Raleigh, NC 27603-2541"
        elif "Olmsted Falls" in invoice.job.temp_printlocation.plant.name:
            plant_address = "920 Mapleway Dr., Olmsted Falls, Ohio 44138"
        elif "Clinton" in invoice.job.temp_printlocation.plant.name:
            plant_address = "1500 S. 14th St., Clinton, Iowa 52732"
        elif "Athens" in invoice.job.temp_printlocation.plant.name:
            plant_address = "PO Box 1547, Canton NC 28716"
        else:
            plant_address = ""
        c.drawString(0.5 * inch, 9.05 * inch, plant_address)

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(4.5 * inch, 9.5 * inch, "Customer:")
    c.drawRightString(4.5 * inch, 9.35 * inch, "Brand:")
    c.drawRightString(4.5 * inch, 9.20 * inch, "Customer PO:")
    c.drawRightString(4.5 * inch, 9.05 * inch, "Evergreen PO:")
    c.drawRightString(4.5 * inch, 8.90 * inch, "Purchase Requisition:")
    c.setFont("Helvetica", 9)
    c.drawString(4.55 * inch, 9.5 * inch, "%s" % invoice.job.customer_name)
    c.drawString(4.55 * inch, 9.35 * inch, "%s" % invoice.job.brand_name)
    c.drawString(4.55 * inch, 9.20 * inch, "%s" % invoice.job.customer_po_number)
    c.drawString(4.55 * inch, 9.05 * inch, "%s" % invoice.job.po_number)
    c.drawString(4.55 * inch, 8.90 * inch, "%s" % invoice.job.purchase_request_number)

    # Set X coordinates for columns on the invoice.
    COLUMN_ONE_X = 0.55
    COLUMN_TWO_X = 3.25
    COLUMN_THREE_X = 5.60
    COLUMN_FOUR_X = 7.40

    # Build the headers.
    c.line(0.5 * inch, 8.85 * inch, 8 * inch, 8.85 * inch)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(COLUMN_ONE_X * inch, 8.74 * inch, "Item")
    c.drawString(COLUMN_TWO_X * inch, 8.74 * inch, "Charges")
    c.drawString(COLUMN_THREE_X * inch, 8.74 * inch, "Totals")
    c.drawString(COLUMN_FOUR_X * inch, 8.74 * inch, "Amount")
    c.line(0.5 * inch, 8.7 * inch, 8 * inch, 8.7 * inch)

    # Vertical lines, left to right.
    c.line(
        (COLUMN_ONE_X - 0.05) * inch,
        8.85 * inch,
        (COLUMN_ONE_X - 0.05) * inch,
        0.55 * inch,
    )
    c.line(
        (COLUMN_TWO_X - 0.05) * inch,
        8.85 * inch,
        (COLUMN_TWO_X - 0.05) * inch,
        0.75 * inch,
    )
    c.line(
        (COLUMN_THREE_X - 0.05) * inch,
        8.85 * inch,
        (COLUMN_THREE_X - 0.05) * inch,
        0.75 * inch,
    )
    c.line(
        (COLUMN_FOUR_X - 0.05) * inch,
        8.85 * inch,
        (COLUMN_FOUR_X - 0.05) * inch,
        0.55 * inch,
    )
    c.line(8 * inch, 8.85 * inch, 8 * inch, 0.55 * inch)

    # Iterate through items for the job.
    # y_cursor Starting point for all line items to be written. Higher is up.
    y_cursor = 8.450
    line_item_number = 1
    total = 0
    # TODO: This is taking all the items in the job, we just want the ones
    # being invoiced. Not a problem in the code, just sloppy.
    for item in invoice.job.item_set.all():
        # Setup the starting line of the item to be that of the current
        # cursor position.
        item_start_y = y_cursor
        print("Drawing Item", item)
        print("Y Cursor", y_cursor)
        print("Item Start Y", item_start_y)
        item_name_written = False
        item_art_charges = 0
        item_plate_charges = 0
        trunc_description = item.description[:45]
        if trunc_description != item.description:
            trunc_description = trunc_description + "..."

        # Do art charges for each item.
        for charge in art_charges:
            if charge.item == item:
                c.setFont("Helvetica", 8)
                # vert_offset = y_cursor - LINE_SPACING
                # Write the item name if has not been written already.
                if not item_name_written:
                    c.drawString(
                        COLUMN_ONE_X * inch,
                        y_cursor * inch,
                        "%s" % charge.item.bev_nomenclature(),
                    )
                    c.drawString(
                        COLUMN_ONE_X * inch,
                        (y_cursor - LINE_SPACING) * inch,
                        trunc_description,
                    )
                    item_name_written = True
                    # item_start_y = y_cursor
                c.drawString(
                    COLUMN_TWO_X * inch,
                    y_cursor * inch,
                    "%d %s" % (line_item_number, charge.description),
                )
                c.drawRightString(
                    (COLUMN_THREE_X - 0.10) * inch,
                    y_cursor * inch,
                    "$%.2f" % float(charge.amount),
                )
                # Drop the y cursor for the next line write.
                y_cursor -= LINE_SPACING
                line_item_number += 1
                total += charge.amount
                item_art_charges += charge.amount

        # Draw total art charges
        if item_art_charges != 0:
            c.setFont("Helvetica-Bold", 8)
            # Draw at item start y (top line of item)
            c.drawRightString(
                (COLUMN_FOUR_X - 0.10) * inch, item_start_y * inch, "Item Art:"
            )
            c.drawRightString(
                7.95 * inch, item_start_y * inch, "$%.2f" % float(item_art_charges)
            )

        # Do plate charges for each item.
        for charge in plate_charges:
            if charge.item == item:
                c.setFont("Helvetica", 8)
                # vert_offset = y_cursor - LINE_SPACING
                # Write the item name if has not been written already.
                if not item_name_written:
                    c.drawString(
                        COLUMN_ONE_X * inch,
                        y_cursor * inch,
                        "%s" % charge.item.bev_nomenclature(),
                    )
                    c.drawString(
                        COLUMN_ONE_X * inch,
                        (y_cursor - LINE_SPACING) * inch,
                        trunc_description,
                    )
                    item_name_written = True
                    # item_start_y = y_cursor
                c.drawString(
                    COLUMN_TWO_X * inch,
                    y_cursor * inch,
                    "%d %s" % (line_item_number, charge.description),
                )
                c.drawRightString(
                    (COLUMN_THREE_X - 0.10) * inch,
                    y_cursor * inch,
                    "$%.2f" % float(charge.amount),
                )
                # Drop y_cursor for next line write.
                y_cursor -= LINE_SPACING
                line_item_number += 1
                total += charge.amount
                item_plate_charges += charge.amount

        # Draw total plate charges if they exist
        if item_plate_charges != 0:
            c.setFont("Helvetica-Bold", 8)
            # Draw at item start y - line spacing (second line of item)
            c.drawRightString(
                (COLUMN_FOUR_X - 0.10) * inch,
                (item_start_y - LINE_SPACING) * inch,
                "Item Plates:",
            )
            c.drawRightString(
                7.95 * inch,
                (item_start_y - LINE_SPACING) * inch,
                "$%.2f" % float(item_plate_charges),
            )

        # Calculate total item charges.
        item_charges = item_art_charges + item_plate_charges

        # Draw total item charges on the 3rd line of the item row.
        if item_charges != 0:
            c.setFont("Helvetica-Bold", 8)
            # Draw at item start y - 2x line spacing (third line of item)
            c.drawRightString(
                (COLUMN_FOUR_X - 0.10) * inch,
                (item_start_y - 2 * LINE_SPACING) * inch,
                "Total Item Charges:",
            )
            c.drawRightString(
                7.95 * inch,
                (item_start_y - 2 * LINE_SPACING) * inch,
                "$%.2f" % float(item_charges),
            )

            # Adjust in case of spacing issues.
            # If the y cursor is higher than the 3rd line, drop it down to the 3rd line.
            if y_cursor >= (item_start_y - 2.0 * LINE_SPACING):
                y_cursor = item_start_y - 2.0 * LINE_SPACING

            # Draw line underneath the item summary.
            c.line(
                0.5 * inch,
                (y_cursor - LINE_SPACING / 2.0) * inch,
                8.0 * inch,
                (y_cursor - LINE_SPACING / 2.0) * inch,
            )
            # Move y cursor down slightly to space for the next line item.
            y_cursor -= 1.8 * LINE_SPACING

    # Draw total box.
    c.line(0.5 * inch, 0.75 * inch, 8 * inch, 0.75 * inch)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(7.25 * inch, 0.6 * inch, "Total:")
    c.drawRightString(7.95 * inch, 0.6 * inch, "$%.2f" % float(total))
    c.line(0.5 * inch, 0.55 * inch, 8 * inch, 0.55 * inch)

    # Draw footer
    c.setFont("Helvetica", 8)
    c.drawCentredString(
        4.25 * inch,
        0.38 * inch,
        "Payment Terms: Net forty-five (45) days from date of invoice sent to the address below.",
    )
    # At request of Cindy Mueller 11/29/2010, change remit-to address for Plant City invoices.
    if "Plant City" in invoice.job.temp_printlocation.plant.name:
        c.drawCentredString(
            4.25 * inch,
            0.25 * inch,
            "Remit Payment to: Graphic Packaging International, PO Box 645689, Pittsburgh, PA 15264-5254",
        )
    elif "Turlock" in invoice.job.temp_printlocation.plant.name:
        c.drawCentredString(
            4.25 * inch,
            0.25 * inch,
            "Remit Payment to: Graphic Packaging International, PO Box 645689, Pittsburgh, PA 15264-5254",
        )
    elif "Clinton" in invoice.job.temp_printlocation.plant.name:
        c.drawCentredString(
            4.25 * inch,
            0.25 * inch,
            "Remit Payment to: Graphic Packaging International, PO Box 645689, Pittsburgh, PA 15264-5254",
        )
    else:
        c.drawCentredString(
            4.25 * inch,
            0.25 * inch,
            "Remit Payment to: Graphic Packaging International, PO Box 645689, Pittsburgh, PA 15264-5254",
        )

    # Close and save the PDF
    c.showPage()
    c.save()
