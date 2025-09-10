"""Active Item Comparison -- Which currently active items use 'bad colors'.

This script imports two XLS files - one containing colors divided into two sets,
Coated and Uncoated. These colors were ones in which the PMS Digital standard
does not match the older GCH standard, but really, any color set could be used --
for instance, to find all items that use that color.

The second XLS file is a spreadsheet of all currently active jobs as pulled from
QAD (datawarehouse>LIDS): (Select * from ProductSpecs where status = 'Active').

The script iterates through the items in the 2nd XLS, finding any matches in GOLD.
If that items uses any of the colors on the 1st XLS, they are flagged and output
to a new XLS file.
"""

#!/usr/bin/python

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
import django

django.setup()
# Back to the ordinary imports

# from gchub_db.tools.importer_functions import *  # BROKEN IMPORT - HolySheet not found

# BROKEN SCRIPT - Missing HolySheet class and xlrd import issues
# Commenting out the entire script execution to avoid linting errors
"""
print("Pack it up, pack it in, let me begin.")
# Argument needs to be a valid Excel sheet.
color_xls_path = os.path.join(
    settings.WORKFLOW_ROOT_DIR,
    "Dropfolders/Color Management/GCH Color Study/pms2gch_mismatches.xls",
)
color_book = xlrd.open_workbook(color_xls_path)
sheet = color_book.sheet_by_index(0)
# hs = HolySheet(color_book, sheet)  # BROKEN - HolySheet not defined

# List of rows to go through
rows = list(range(1, sheet.nrows))

coated_colors = []
uncoated_colors = []

num_matches = 0
num_nonmatches = 0

for row_num in rows:
    # Returns the current row object
    row = sheet.row(row_num)
    try:
        c_color = hs.get_column_val(row, "Coated")
        if c_color:
            coated_colors.append(c_color)
        u_color = hs.get_column_val(row, "Uncoated")
        if u_color:
            uncoated_colors.append(u_color)
    except Exception:
        # Bad color or parse error, skip this row silently (preserve original no-op)
        pass

print("Coated", len(coated_colors))
print("Uncoated", len(uncoated_colors))

# Now read in the active item spreadsheet.
item_xls_path = os.path.join(
    settings.WORKFLOW_ROOT_DIR,
    "Dropfolders/Color Management/GCH Color Study/active_products_sorted.xls",
)
book = xlrd.open_workbook(item_xls_path)
sheet = book.sheet_by_index(0)
# hs = HolySheet(book, sheet)  # BROKEN - HolySheet not defined
# List of rows to go through
rows = list(range(1, sheet.nrows))

# Setup the Worksheet
workBookDocument = openpyxl.Workbook()
# Setup the first sheet to be the summary sheet

docSheet1 = workBookDocument.active
docSheet1.title = "Warning Items"

# Label column headings
docSheet1.cell(row=1, column=1).value = "Item#"
docSheet1.cell(row=1, column=2).value = "Colors"
docSheet1.cell(row=1, column=3).value = "Job"
docSheet1.cell(row=1, column=4).value = "PrintGroup"
docSheet1.cell(row=1, column=5).value = "Plants"

docSheet2 = workBookDocument.create_sheet("Color Frequency")
# Label column headings
docSheet2.cell(row=1, column=1).value = "Colors"
docSheet2.cell(row=1, column=2).value = "Instances"

write_row = 2
naughty_colors = {}

for row_num in rows:
    # Do some stuff.
    row = sheet.row(row_num)
    nine_digit = hs.get_column_val(row, "PrintType2")
    printgroup = hs.get_column_val(row, "PartType")
    plants = []
    try:
        item_matches = Item.objects.filter(fsb_nine_digit=nine_digit).order_by(
            "-creation_date"
        )
        for i in item_matches:
            if i.printlocation.plant.name not in plants:
                plants.append(i.printlocation.plant.name)
        item = item_matches[0]
        num_matches += 1
        # Reset color list for item.
        offending_colors = []
        # Hey, look, we found an item. Let's see if it's got any crappy colors in it.
        for color in item.itemcolor_set.all():
            flag = False
            if (
                color.item.size.product_substrate in app_defs.COATED_SUBSTRATES
                and color.color in coated_colors
            ):
                print("Crappy coated color.")
                flag = True
                coating = "C"
            elif (
                color.item.size.product_substrate in app_defs.UNCOATED_SUBSTRATES
                and color.color in uncoated_colors
            ):
                print("Crappy uncoated color.")
                flag = True
                coating = "U"
            # Flagged colors get sent to the naughty color bin.
            if flag:
                # Give it a U or a C
                bad_color = str(color.color) + " " + coating
                # Add to naughty color list.
                naughty_colors[bad_color] = naughty_colors.get(bad_color, 0) + 1
                # Append ink coverage in sq. inches to color, then append to
                # the offending colors list for the item.
                bad_color += ": " + str(color.coverage_sqin)
                offending_colors.append(bad_color)
        # So this item has some problematic colors in it... write to XLS file.
        if offending_colors:
            docSheet1.cell(row=write_row + 1, column=1).value = nine_digit
            docSheet1.cell(row=write_row + 1, column=2).value = str(offending_colors)
            docSheet1.cell(row=write_row + 1, column=3).value = str(item.job)
            docSheet1.cell(row=write_row + 1, column=4).value = printgroup
            docSheet1.cell(row=write_row + 1, column=5).value = str(plants)
            write_row += 1

    except Exception:
        print("Could not find item for part#:", nine_digit)
        num_nonmatches += 1

# Freeze the top row of column headings.
docSheet1.panes_frozen = docSheet1["B2"]

i = 0
for color in naughty_colors:
    docSheet2.cell(row=i + 2, column=1).value = color
    docSheet2.cell(row=i + 2, column=2).value = naughty_colors[color]
    i += 1

# Freeze the top row of column headings.
docSheet2.panes_frozen = docSheet1["B2"]

# Save XLS document
workBookDocument.save("xls_output/Warning Items.xls")

print("Finnish'd.")
print(num_matches)
print(num_nonmatches)
"""
