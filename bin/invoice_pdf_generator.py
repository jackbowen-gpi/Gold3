#!/usr/bin/python
"""Generate PDF invoices from billing records for manual distribution."""

import bin_functions

bin_functions.setup_paths()
from datetime import date

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from gchub_db.apps.budget import billing_funcs
from gchub_db.apps.workflow.models import Job

# Set month and year to get invoiced charges from.
month_num = 10
year_num = 2009

# start_date = date(2008, 12, 21)
end_date = date(year_num, month_num, 21)
workflow = "Beverage"

# month_name = end_date.strftime('%B')

# Get invoiced charges, plates included.
invoiced_charges = billing_funcs.get_invoiced_data(
    year_num, month_num, workflow, plates=True
)["charges"]

# Build list of all unique job numbers in queryset.
jobs = []
for x in invoiced_charges:
    if x.item.job.id not in jobs:
        jobs.append(x.item.job.id)

print("Number of charges: %s" % invoiced_charges.count())
print("Number of jobs (POs to create): %s" % len(jobs))
print("======================================")

job_set = jobs

# Create a PDF invoices for each job.
for job_id in job_set:
    job = Job.objects.get(id=job_id)
    print("Generating PDF invoice for PO: %s" % job.po_number)

    # Setup the document.
    c = canvas.Canvas(
        "/Volumes/Beverage/Invoices_For_Email/Current_Invoices/%s.pdf" % job.po_number,
        pagesize=letter,
    )

    # Setup all the headers for the invoice.
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(0.8 * inch, 10.5 * inch, "PO:")
    c.drawRightString(0.8 * inch, 10.35 * inch, "Date:")
    c.setFont("Helvetica", 9)
    c.drawString(0.85 * inch, 10.5 * inch, "%s" % job.po_number)
    c.drawString(0.85 * inch, 10.35 * inch, "%s" % date.today())
    c.drawInlineImage(
        "../media/img/gch_logo.jpg", 2.5 * inch, 9.75 * inch, width=None, height=None
    )
    c.setFont("Helvetica-Bold", 9)
    c.rect(0.45 * inch, 9 * inch, 7.6 * inch, 0.65 * inch, stroke=1, fill=0)
    c.drawString(0.5 * inch, 9.5 * inch, "Bill To:")
    c.setFont("Helvetica", 9)
    c.drawString(0.5 * inch, 9.35 * inch, "Evergreen Packaging, Inc.")
    try:
        c.drawString(0.5 * inch, 9.20 * inch, "%s" % job.temp_printlocation.plant.name)
    except AttributeError:
        pass
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(4.5 * inch, 9.5 * inch, "Customer:")
    c.drawRightString(4.5 * inch, 9.35 * inch, "Brand:")
    c.drawRightString(4.5 * inch, 9.20 * inch, "Customer PO:")
    c.setFont("Helvetica", 9)
    c.drawString(4.55 * inch, 9.5 * inch, "%s" % job.customer_name)
    c.drawString(4.55 * inch, 9.35 * inch, "%s" % job.brand_name)
    c.drawString(4.55 * inch, 9.20 * inch, "%s" % job.customer_po_number)

    # Build the line item headers.
    c.line(0.5 * inch, 8.95 * inch, 8 * inch, 8.95 * inch)
    c.setFont("Helvetica-Bold", 9)
    # c.drawString(0.55*inch, 8.8*inch, "Item")
    c.drawString(0.8 * inch, 8.8 * inch, "Type")
    c.drawString(2.83 * inch, 8.8 * inch, "Description")
    c.drawRightString(7.95 * inch, 8.8 * inch, "Amount")
    c.line(0.5 * inch, 8.75 * inch, 8 * inch, 8.75 * inch)

    # Vertical lines, left to right.
    c.line(0.5 * inch, 8.95 * inch, 0.5 * inch, 0.95 * inch)
    c.line(0.75 * inch, 8.95 * inch, 0.75 * inch, 1.15 * inch)
    c.line(2.75 * inch, 8.95 * inch, 2.75 * inch, 1.15 * inch)
    c.line(7.35 * inch, 8.95 * inch, 7.35 * inch, 0.95 * inch)
    c.line(8 * inch, 8.95 * inch, 8 * inch, 0.95 * inch)

    # Iterate through charges for the job.
    vert_start = 8.6
    item = 1
    total = 0
    for charge in invoiced_charges:
        if charge.item.job == job:
            c.setFont("Helvetica", 9)
            vert_offset = vert_start - 0.135
            c.drawString(0.55 * inch, vert_start * inch, str(item))
            c.drawString(0.8 * inch, vert_start * inch, "%s" % charge.description)
            c.setFont("Helvetica", 8)
            c.drawString(
                2.8 * inch,
                vert_start * inch,
                "%s" % charge.item.bev_nomenclature()
                + " ("
                + charge.item.description
                + ")",
            )
            c.setFont("Helvetica", 9)
            c.drawRightString(
                7.95 * inch, vert_start * inch, "$%.2f" % float(charge.amount)
            )
            vert_start -= 0.16
            item += 1
            total += charge.amount

    # Draw total box.
    c.line(0.5 * inch, 1.15 * inch, 8 * inch, 1.15 * inch)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(6.85 * inch, 1 * inch, "Total:")
    c.drawRightString(7.95 * inch, 1 * inch, "$%.2f" % float(total))
    c.line(0.5 * inch, 0.95 * inch, 8 * inch, 0.95 * inch)

    # Draw footer
    c.setFont("Helvetica", 8)
    c.drawCentredString(
        4.25 * inch,
        0.25 * inch,
        "P: 864.633.6000  F: 864.653.5168    155 Old Greenville Hwy, Suite 103, "
        "Clemson, SC, 29631",
    )

    # Close and save the PDF
    c.showPage()
    c.save()
