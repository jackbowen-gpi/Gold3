#!/usr/bin/python
"""Foodservice Corrugated generator module."""

import os
import sys
import time

# Setup the Django environment
sys.path.append("../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
# Back to the ordinary imports
from gchub_db.apps.auto_corrugated.documents.fsb_box import FSBLabel

x = time.time()

# Numbers
nine_digit_num = 322345015
fourteen_digit_num = 12345678901234

text_line_1 = "SMR-12 Example Case"
text_line_2 = "12 ounce hot cup"

box1 = FSBLabel("label_example.pdf", nine_digit_num, fourteen_digit_num, text_line_1, text_line_2)

box1.save_to_pdf()

print("Time:", time.time() - x)
# box1.save_to_jpg('blah.jpg', max_width='200px')
