#!/usr/bin/python
"""Foodservice Corrugated generator module."""

import os
import sys
import time

# Setup the Django environment
sys.path.append("../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
# Back to the ordinary imports
from gchub_db.apps.auto_corrugated.documents.fsb_box import FSBBox

x = time.time()

# Dimensions
length = 14.0
width = 12.0
height = 16.375

# Numbers
six_digit_num = 915165
nine_digit_num = 322345015
fourteen_digit_num = 12345678901234

plant = "Kenton"
box_format = "left"

case_count = "1000"
sleeve_count = "100"
text_line_1 = "SMR-12 Example Case"
text_line_2 = "12 ounce hot cup"
item_name = "LHRN-16"

item_description_english = "CLEAR PLASTIC LID - FLAT SLOTTED"
item_description_spanish = "Tapas de plastico transparente - plana ranurada"
item_description_french = None
lid_information_english = "Use lid LCRS-22, LCSRCR-22 or LCSRSM-20"
lid_information_spanish = "Spanish lid description."
lid_information_french = None

# These are independent of each other.
sfi_container = True
sfi_contents = True

print_header = True
board_spec = "32 ECT"
case_color = "90 Black"

box1 = FSBBox(
    "box_example.pdf",
    height,
    width,
    length,
    box_format,
    six_digit_num,
    nine_digit_num,
    fourteen_digit_num,
    text_line_1,
    text_line_2,
    plant,
    case_count,
    sleeve_count,
    item_name,
    item_description_english,
    item_description_spanish,
    item_description_french,
    lid_information_english,
    lid_information_spanish,
    lid_information_french,
    sfi_container,
    sfi_contents,
    print_header,
    board_spec,
    case_color,
    True,
    watermark=False,
)

box1.save_to_pdf()

print("Time:", time.time() - x)
# box1.save_to_jpg('blah.jpg', max_width='200px')
