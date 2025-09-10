"""FSB box documents."""

import logging
import os
import re

from django.conf import settings
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from gchub_db.apps.auto_corrugated.elements.fsb_elements import (
    Code128Barcode_Kenton,
    CollidableSVGGraphicElement,
    CompanyLogoElement,
    CountLabelElement,
    FlapTextElement,
    ItemDescriptionElement,
    LabelAreaElement,
    MachineBarcodeBoxElement,
    SpecialtyLogoElement,
    StamperBoxElement,
)
from includes.reportlib.elements.collidables import CollidableTextElement
from gchub_db.includes import general_funcs
from gchub_db.includes.reportlib.util import check_text_width

from .generic import GenericBox, GenericLabel

# DISPLAY_GRAPHICS = True
CORRUGATED_MEDIA_DIR = os.path.join(settings.PRODUCTION_DIR, "autocorr_elements")
logger = logging.getLogger(__name__)

# Register special font if available. Use logging instead of printing so startup
# isn't noisy when the font isn't present in a dev environment.
font_path = os.path.join(CORRUGATED_MEDIA_DIR, "VAG Rounded BT.ttf")
try:
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("VAG Rounded BT", font_path))
    else:
        logger.debug("Font file not found at: %s", font_path)
except Exception:
    # Log the exception with stacktrace for diagnostics, but avoid printing to stdout.
    logger.exception("Could not load font at: %s", font_path)


class FSBBox(GenericBox):
    """The FSBBox is a standard Foodservice Corrugated box layout."""

    def __init__(
        self,
        file_name,
        height,
        width,
        length,
        format,
        six_digit_num,
        replaced_6digit,
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
        pdf_type,
        sfi_container,
        sfi_contents,
        print_header,
        board_spec,
        case_color,
        make_slugs,
        artist,
        plate_number,
        label_id,
        method,
        job_id=None,
        watermark=False,
    ):
        """Handles drawing the canvas and preparing other storage variables.

        file_name: (str) Path to the eventual finished PDF.
        width: (float) Width of the box (in inches)
        height: (float) Height of the box (in inches)
        length: (float) Length of the box (in inches)
        text_line_1: (str) String to appear in the LabelAreaElement.
        text_line_2: (str) String to appear in the LabelAreaElement.
        plant: (str) String value for the plant name.
        case_count: (int) Case count for cups.
        sleeve_count: (int) Sleeve count for cups.
        item_name: (str) The name of the item in the box.
        item_description_english: (str) Description of item - English
        item_description_spanish: (str) Description of item - Spanish
        item_description_french: (str) Description of item - French
        lid_information_english: (str) Lid information - English
        lid_information_spanish: (str) Lid information - Spanish
        lid_information_french: (str) Lid information - French
        sfi_container: (bool) Needs SFI cert stamp for container.
        sfi_contents: (bool) Needs SFI cert stamp for contents of container.
        print_header: (bool) Add print header info or not.
        board_spec: (str) Board material - printer header only.
        case_color: (str) Ink color to print box - printer header only.
        watermark: (bool) Place 'watermark' on artwork if True.
        make_slugs: (bool) Create slugs pages for platemaking if True.
        job_id: (int) GOLD job id number.
        replaced_6digit: (int) Six-digit # of replaced part.
        box_id: (int) ID of the generated box to get info from GOLD
        method: (Str) Either automationEngine of reportlab to decide how we generate the barcode.
        """
        if watermark:
            encrypt = True
        else:
            encrypt = False
        # Call GenericBox's __init__() method.
        super(FSBBox, self).__init__(
            file_name, width, height, length, format, print_header, encrypt, plant
        )
        # Transfer variables that are specific to FSBBox objects.
        self.file_name = file_name
        self.format = format
        self.six_digit_num = six_digit_num
        self.replaced_6digit = replaced_6digit
        self.nine_digit_num = nine_digit_num
        self.fourteen_digit_num = fourteen_digit_num
        self.text_line_1 = text_line_1
        self.text_line_2 = text_line_2
        self.plant = plant
        self.case_count = case_count
        self.sleeve_count = sleeve_count
        self.item_name = item_name
        self.item_description_english = item_description_english
        self.item_description_spanish = item_description_spanish
        self.item_description_french = item_description_french
        self.lid_information_english = lid_information_english
        self.lid_information_spanish = lid_information_spanish
        self.lid_information_french = lid_information_french
        self.sfi_container = sfi_container
        self.sfi_contents = sfi_contents
        self.print_header = print_header
        self.board_spec = board_spec
        self.case_color = case_color
        self.make_slugs = make_slugs
        self.watermark = watermark
        self.job_id = job_id
        self.artist = artist
        self.plate_number = plate_number
        self.pdf_type = pdf_type
        self.label_id = label_id
        self.method = method

        if self.plant == "Pittston":
            self.heightMod = 0.375
        elif self.plant == "Clarksville":
            self.heightMod = 0.4375
        else:
            self.heightMod = 0.4375

        # Place watermark down first underneath other elements.
        if watermark:
            self.__draw_watermark()
        # Start drawing the FSBBox-specific elements on page 1.
        self.__draw_fsb_elements()
        # Print header is the box on top of the page containing much of the
        # information used to create the box artwork (dimensions, codes, etc...)
        if self.print_header:
            self.__draw_fsb_print_header()
        # Visalia wants a dimension line for their label area.
        if self.plant.lower() == "visalia":
            # Visalia's is 2 inches up from the bottom of the panel.
            self.draw_label_dimension_line(2)
        # Close drawing on the first page.
        self.canvas.showPage()
        # Create slugs if True.
        if self.make_slugs:
            print("This has been removed for now")
            # self.create_slugs()

    def __draw_case_sleeve_counts(self):
        """Draw the Case/Sleeve count labels on each of the panels."""
        # Case count, goes on the first line of the multi-line text box.
        case_text = "%s/CASE/CAJA/CAISSE" % self.case_count
        # Sleeve count is the second line.
        sleeve_text = "%s/SLEEVE/MANGA/MANCHE" % self.sleeve_count
        # Combine these to pass to the MultiLineElement constructor.
        text_lines = [case_text, sleeve_text]
        # This is on a separate line because it will need to be larger.
        text_lines_usa = ["MADE IN THE U.S.A."]

        # Case/Sleeve count on panel A.
        if self.plant == "Kenton":  # Kenton doesn't want this panel.
            pass
        else:
            panel_a_label = CountLabelElement(
                "CaseCountA",
                self.X_PANEL_A + self.MARGIN_WIDTH,
                self.Y_PANEL_A + 0.7 + self.MARGIN_WIDTH,
                text_lines,
                can_move_x=False,
                can_move_y=False,
            )
            self.place_element(panel_a_label, ignore_margins=True)

            """
            Marketing wanted the "Made in USA" line to be a different size so
            we're placing that line separately. We're also moving the other
            lines up by .7 to make room for it as you can see above. There might
            be a better way to do this but I am not a clever man.
            """
            panel_a_label_usa = CountLabelElement(
                "CaseCountA_USA",
                self.X_PANEL_A + self.MARGIN_WIDTH,
                self.Y_PANEL_A + self.MARGIN_WIDTH,
                text_lines_usa,
                size=42,
                can_move_x=False,
                can_move_y=False,
            )
            self.place_element(panel_a_label_usa, ignore_margins=True)

        # Case/Sleeve count on panel C.
        panel_c_label = CountLabelElement(
            "CaseCountC",
            self.X_PANEL_C + self.MARGIN_WIDTH,
            self.Y_PANEL_A + 0.7 + self.MARGIN_WIDTH,
            text_lines,
            can_move_x=False,
            can_move_y=False,
        )
        self.place_element(panel_c_label, ignore_margins=True)

        # USA line placed at a larger size on panel C.
        panel_c_label_usa = CountLabelElement(
            "CaseCountC_USA",
            self.X_PANEL_C + self.MARGIN_WIDTH,
            self.Y_PANEL_A + self.MARGIN_WIDTH,
            text_lines_usa,
            size=42,
            can_move_x=False,
            can_move_y=False,
        )
        self.place_element(panel_c_label_usa, ignore_margins=True)

        # Depending on whether the box is left or right handed, the panel D
        # label is placed differently.
        if self.format.lower() == "left":
            # Left handed box.
            panel_d_top_label = CountLabelElement(
                "CaseCountD",
                self.X_PANEL_C + self.C_PANEL_SIDE - self.MARGIN_WIDTH,
                (self.box_height - self.heightMod)
                - 0.7
                + (self.FLAP_HEIGHT * 2)
                - self.MARGIN_WIDTH,
                text_lines,
                can_move_x=False,
                can_move_y=False,
            )
            # Make sure to perform rotation.
            self.place_element(panel_d_top_label, ignore_margins=True, rotated=True)

            # USA line placed at a larger size on panel D top
            panel_d_top_label_usa = CountLabelElement(
                "CaseCountD_USA",
                self.X_PANEL_C + self.C_PANEL_SIDE - self.MARGIN_WIDTH,
                (self.box_height - self.heightMod)
                + (self.FLAP_HEIGHT * 2)
                - self.MARGIN_WIDTH,
                text_lines_usa,
                can_move_x=False,
                can_move_y=False,
                size=42,
            )
            # Make sure to perform rotation.
            self.place_element(panel_d_top_label_usa, ignore_margins=True, rotated=True)

        else:
            # Right handed box.
            panel_d_top_label = CountLabelElement(
                "CaseCountD",
                self.X_PANEL_D + self.D_PANEL_SIDE - self.MARGIN_WIDTH,
                (self.box_height - self.heightMod)
                - 0.7
                + (self.FLAP_HEIGHT * 2)
                - self.MARGIN_WIDTH,
                text_lines,
                can_move_x=False,
                can_move_y=False,
            )
            # Make sure to perform rotation.
            self.place_element(panel_d_top_label, ignore_margins=True, rotated=True)

            # USA line placed at a larger size on panel D top
            panel_d_top_label_usa = CountLabelElement(
                "CaseCountD_USA",
                self.X_PANEL_D + self.D_PANEL_SIDE - self.MARGIN_WIDTH,
                (self.box_height - self.heightMod)
                + (self.FLAP_HEIGHT * 2)
                - self.MARGIN_WIDTH,
                text_lines_usa,
                can_move_x=False,
                can_move_y=False,
                size=42,
            )
            # Make sure to perform rotation.
            self.place_element(panel_d_top_label_usa, ignore_margins=True, rotated=True)

        # Case/Sleeve count on panel B.
        panel_b_label = CountLabelElement(
            "CaseCountB",
            self.X_PANEL_B + self.B_PANEL_SIDE - self.MARGIN_WIDTH,
            self.Y_PANEL_A + 0.7 + self.MARGIN_WIDTH,
            text_lines,
            text_align="end",
            can_move_x=False,
            alignment="right",
            can_move_y=False,
        )
        self.place_element(panel_b_label, ignore_margins=True)

        # USA line placed at a larger size on panel B.
        panel_b_label_usa = CountLabelElement(
            "CaseCountB_USA",
            self.X_PANEL_B + self.B_PANEL_SIDE - self.MARGIN_WIDTH,
            self.Y_PANEL_A + self.MARGIN_WIDTH,
            text_lines_usa,
            text_align="end",
            can_move_x=False,
            alignment="right",
            can_move_y=False,
            size=42,
        )
        self.place_element(panel_b_label_usa, ignore_margins=True)

        # Case/Sleeve count on panel D.
        panel_d_label = CountLabelElement(
            "CaseCountD",
            self.X_PANEL_D + self.D_PANEL_SIDE - self.MARGIN_WIDTH,
            self.Y_PANEL_A + 0.7 + self.MARGIN_WIDTH,
            text_lines,
            text_align="end",
            can_move_x=False,
            alignment="right",
            can_move_y=False,
        )
        self.place_element(panel_d_label, ignore_margins=True)

        # USA line placed at a larger size on panel D.
        panel_d_label_usa = CountLabelElement(
            "CaseCountD_USA",
            self.X_PANEL_D + self.D_PANEL_SIDE - self.MARGIN_WIDTH,
            self.Y_PANEL_A + self.MARGIN_WIDTH,
            text_lines_usa,
            text_align="end",
            can_move_x=False,
            alignment="right",
            can_move_y=False,
            size=42,
        )
        self.place_element(panel_d_label_usa, ignore_margins=True)

    def __draw_label_area(self):
        """Draw the label area and accompanying barcodes."""
        label_area_bottom_left_x = self.X_PANEL_B - 6.025
        label_area_bottom_left_y = self.Y_PANEL_A - 0.025
        self.elem_label_area = LabelAreaElement(
            "LabelArea",
            label_area_bottom_left_x,
            label_area_bottom_left_y,
            self.nine_digit_num,
            self.fourteen_digit_num,
            self.text_line_1,
            self.text_line_2,
            self.plant,
            self.case_count,
            self.pdf_type,
            self.label_id,
            self.method,
            group_id=6,
        )
        self.place_element(self.elem_label_area, ignore_margins=True)

        # add Order# and Date on the D flap of the box for kenton
        if self.plant == "Clarksville":
            bottomLeftFlap_location = self.A_PANEL_SIDE + (self.B_PANEL_SIDE / 2) + 1.5
            c = self.canvas
            # Sets the color of the panel outlines. Original values were (0, 0, 0, 0.75) for both
            c.setStrokeColorCMYK(0.65, 0.60, 0.55, 0)
            c.setFillColorCMYK(0.65, 0.60, 0.55, 0)
            c.setFont("Helvetica-Bold", 40)
            c.drawRightString(
                bottomLeftFlap_location * inch,
                (self.FLAP_HEIGHT / 2.0 - 1.5) * inch,
                "MFG ORD #",
            )

    def __draw_stamper_box(self):
        """Draws the stamper box above the label area."""
        if self.format.lower() == "left":
            self.stamper = StamperBoxElement(
                "StamperBox",
                self.X_PANEL_B - 6.0,
                self.elem_label_area.bottom_left_y + self.elem_label_area.height + 0.25,
                5.45,
                0.95,
                group_id=6,
            )
        else:
            self.stamper = StamperBoxElement(
                "StamperBox",
                self.X_PANEL_B + 0.55,
                self.elem_label_area.bottom_left_y + self.elem_label_area.height + 0.25,
                5.45,
                0.95,
                group_id=6,
            )
        self.place_element(self.stamper, ignore_margins=True)

    def __draw_machine_barcode_box(self):
        """Draws the machine bar code box to the left of the label area. Only for
        Kenton with box format left.
        """
        if self.format.lower() == "left" and self.plant.lower() == "kenton":
            self.box = MachineBarcodeBoxElement(
                "MachineBarcodeBox",
                self.X_PANEL_B - 9,
                self.elem_label_area.bottom_left_y + self.elem_label_area.height - 1,
                2,
                1,
                group_id=6,
            )
            self.place_element(self.box, ignore_margins=True)
        else:
            print("Skipping machine bar code box due to plant or box format.")

    def __draw_barcode_six_digit_barcode(self):
        if self.format.lower() == "left":
            six_digit_barcode_x_location = (
                self.X_PANEL_B + (self.B_PANEL_SIDE / 2) - 1.0
            )
        else:
            six_digit_barcode_x_location = (
                self.X_PANEL_C + (self.C_PANEL_SIDE / 2) - 1.0
            )

        # Draw the barcode for Kenton.
        barcode_y_location = self.FLAP_HEIGHT / 2.0 - 0.69
        barcode = Code128Barcode_Kenton(
            "Six_Digit_Code",
            six_digit_barcode_x_location,
            barcode_y_location,
            self.six_digit_num,
            self.label_id,
            self.method,
        )
        self.place_element(barcode, can_delete=False, ignore_margins=True)

    def __draw_flap_text(self):
        """Draw the common text on the flaps."""
        # Misc. text and codes.
        if self.format.lower() == "left":
            six_digit_x_location = self.X_PANEL_C + self.MARGIN_WIDTH
            six_digit_barcode_x_location = (
                self.X_PANEL_B + (self.B_PANEL_SIDE / 2) - 1.0
            )
            topflap_1_location = self.X_PANEL_A + self.MARGIN_WIDTH
            topflap_2_location = self.X_PANEL_C + self.MARGIN_WIDTH
            bottomflap_location = self.X_PANEL_D - self.MARGIN_WIDTH
        else:
            six_digit_x_location = self.X_PANEL_D + self.MARGIN_WIDTH
            six_digit_barcode_x_location = (
                self.X_PANEL_C + (self.C_PANEL_SIDE / 2) - 1.0
            )
            topflap_1_location = self.X_PANEL_B + self.MARGIN_WIDTH
            topflap_2_location = self.X_PANEL_D + self.MARGIN_WIDTH
            bottomflap_location = self.X_PANEL_D + self.B_PANEL_SIDE - self.MARGIN_WIDTH

        # Draw the six digit number.
        self.six_digit_text = CollidableTextElement(
            "SixDigitNumBottom",
            six_digit_x_location,
            0.25 * self.SHORT_SIDE,
            self.six_digit_num,
            size=65,
            group_id=5,
        )
        self.place_element(self.six_digit_text, ignore_margins=True)

        # Draw the 6-digit-barcode
        barcode_y_location = self.FLAP_HEIGHT / 2 - 0.8
        barcode = Code128Barcode_Kenton(
            "Six_Digit_Code",
            six_digit_barcode_x_location,
            barcode_y_location,
            self.six_digit_num,
            self.label_id,
            self.method,
        )
        self.place_element(barcode, can_delete=False)

        # Draw item name on the bottom of the box.
        item_name_bottom = CollidableTextElement(
            "Item_Name_Bottom",
            six_digit_x_location,
            self.six_digit_text.bottom_left_y - 0.5,
            self.item_name,
            size=26,
            group_id=5,
        )
        self.place_element(item_name_bottom)

        this_side_text_size = 26
        text_lines_up = [
            "This side up",
            "Este lado para arriba",
            "Ce cote vers le haut",
        ]

        this_side_text_height = len(text_lines_up) * (this_side_text_size / 72.0)
        this_side_up_y = (
            (self.box_height - self.heightMod)
            + (self.FLAP_HEIGHT * 2)
            - this_side_text_height
            - self.MARGIN_WIDTH
        )

        # Draw the first 'This side up' label on the top flap.
        this_side_up_1_text = FlapTextElement(
            "ThisSideUpTop", topflap_1_location, this_side_up_y, text_lines_up
        )
        self.place_element(this_side_up_1_text)

        # Draw the second 'This side up' label on the top flap.
        this_side_up_2_text = FlapTextElement(
            "ThisSideUpTop2", topflap_2_location, this_side_up_y, text_lines_up
        )
        self.place_element(this_side_up_2_text)

        # Draw the second 'This side up' label on the top flap.
        text_lines_down = [
            "This side down",
            "Este lado para bajo",
            "Ce cote vers le bas",
        ]

        this_side_text_height = len(text_lines_down) * (this_side_text_size / 72.0)
        this_side_down_y = self.MARGIN_WIDTH + this_side_text_height

        this_side_down_text = FlapTextElement(
            "ThisSideUpDown", bottomflap_location, this_side_down_y, text_lines_down
        )
        self.place_element(this_side_down_text, rotated=True)

    def __draw_item_name(self, short_mode=False):
        """Create Drawing object for the item name."""
        # KWARGS!
        can_move_x = False
        can_move_y = False

        # Adjust the font size to fit the shorter panel.
        type_size = 131.0

        # Reduce the size of the text by 10 points at a time until it fits
        # comfortably into the space alloted
        size_OK = False
        total_width = check_text_width(type_size, "VAG Rounded BT", self.item_name)

        # Start at font size suggested above, adjust as needed until limit is reached.
        while not size_OK and type_size > 90.0:
            if total_width < (self.SHORT_SIDE - 4.0):
                size_OK = True
                # print total_width
            else:
                type_size -= 8.0
                total_width = check_text_width(
                    type_size, "VAG Rounded BT", self.item_name
                )

        # In short mode the item name's vertical size must be limited.
        if short_mode:
            text_height = type_size / 100.0
            if text_height > self.box_height * 0.1:
                print(("Item name height: %s" % text_height))
                print("Shortening item name.")
                type_size = (self.box_height * 0.09) * 100

        # Convert text height to inches.
        text_height = type_size / 100.0
        total_width = check_text_width(type_size, "VAG Rounded BT", self.item_name)

        # Draw item name on first panel (A)
        try:  # If there's a specialty logo there go under it.
            item_name_a_y = self.specialty_logo_a.bottom_left_y - text_height - 0.25
        except Exception:  # Otherwise go under the GPI logo.
            if short_mode:  # For short boxes go directly under the GPI logo.
                item_name_a_y = self.ip_logo_a.bottom_left_y - text_height - 0.5
            else:  # For bigger boxes leave a gap.
                item_name_a_y = (
                    (self.box_height - self.heightMod) * 0.65 + self.SHORT_SIDE / 2.0
                ) - (text_height / 2.0)
        self.item_name_a = CollidableTextElement(
            "ItemNameA",
            self.X_PANEL_A + self.MARGIN_WIDTH,
            item_name_a_y,
            self.item_name,
            font="VAG Rounded BT",
            size=type_size,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            group_id=1,
        )
        self.place_element(self.item_name_a)

        # Draw item name on second panel (B)
        try:  # If there's a specialty logo there go under it.
            item_name_b_y = self.specialty_logo_b.bottom_left_y - text_height - 0.25
        except Exception:  # Otherwise go under the GPI logo.
            if short_mode:  # For short boxes go directly under the GPI logo.
                item_name_b_y = self.ip_logo_a.bottom_left_y - text_height - 0.5
            else:  # For bigger boxes leave a gap.
                item_name_b_y = (
                    (self.box_height - self.heightMod) * 0.65 + self.SHORT_SIDE / 2.0
                ) - (text_height / 2.0)
        item_name_b_x = self.X_PANEL_C - self.MARGIN_WIDTH - total_width
        self.item_name_b = CollidableTextElement(
            "ItemNamB",
            item_name_b_x,
            item_name_b_y,
            self.item_name,
            font="VAG Rounded BT",
            size=type_size,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            group_id=2,
        )
        self.place_element(self.item_name_b)

        # Draw item name on third panel (C)
        try:  # If there's a specialty logo there go under it.
            item_name_c_y = self.specialty_logo_c.bottom_left_y - text_height - 0.25
        except Exception:  # Otherwise go under the GPI logo.
            if short_mode:  # For short boxes go directly under the GPI logo.
                item_name_c_y = self.ip_logo_a.bottom_left_y - text_height - 0.5
            else:  # For bigger boxes leave a gap.
                item_name_c_y = (
                    (self.box_height - self.heightMod) * 0.65 + self.SHORT_SIDE / 2.0
                ) - (text_height / 2.0)
        item_name_c_x = self.X_PANEL_C + self.MARGIN_WIDTH
        self.item_name_c = CollidableTextElement(
            "ItemNameC",
            item_name_c_x,
            item_name_c_y,
            self.item_name,
            font="VAG Rounded BT",
            size=type_size,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            group_id=3,
        )
        self.place_element(self.item_name_c)

        # Draw item name on fourth panel (D)
        try:  # If there's a specialty logo there go under it.
            item_name_d_y = self.specialty_logo_d.bottom_left_y - text_height - 0.25
        except Exception:  # Otherwise go under the GPI logo.
            if short_mode:  # For short boxes go directly under the GPI logo.
                item_name_d_y = self.ip_logo_a.bottom_left_y - text_height - 0.5
            else:  # For bigger boxes leave a gap.
                item_name_d_y = (
                    (self.box_height - self.heightMod) * 0.65 + self.SHORT_SIDE / 2.0
                ) - (text_height / 2.0)
        item_name_d_x = (
            self.X_PANEL_D + self.D_PANEL_SIDE - self.MARGIN_WIDTH - total_width
        )

        self.item_name_d = CollidableTextElement(
            "ItemNameD",
            item_name_d_x,
            item_name_d_y,
            self.item_name,
            font="VAG Rounded BT",
            size=type_size,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            group_id=4,
        )
        self.place_element(self.item_name_d)

        # Draw item name on top flap of the box, upside down.
        # Dependency on box format for x placement.
        if self.box_format.lower() == "left":
            item_name_top_x = self.X_PANEL_D - self.MARGIN_WIDTH
        else:
            item_name_top_x = self.X_PANEL_D + self.B_PANEL_SIDE - self.MARGIN_WIDTH

        # Set up y position for top logo, accounting for rotation.
        item_name_top_y = (
            (self.box_height - self.heightMod)
            + self.FLAP_HEIGHT
            + self.MARGIN_WIDTH
            + text_height
        )

        # Draw item name on top.
        self.item_name_top = CollidableTextElement(
            "ItemNameTop",
            item_name_top_x,
            item_name_top_y,
            self.item_name,
            font="VAG Rounded BT",
            size=type_size,
            can_move_x=can_move_x,
        )
        self.place_element(self.item_name_top, rotated=True)

    def __draw_item_description(self):
        """Draw item descriptions & lid information under the item names.
        Three different languages.
        """
        # Setup kwargs for this set of elements.
        can_move_x = False
        can_move_y = False

        # Set font size and convert height to inches.
        type_size = 17.5
        text_height = type_size / 72.0
        print(("Type size: %s" % type_size))
        print(("Text height: %s" % text_height))
        # Build list of text lines.
        text_lines = []
        if self.item_description_english:
            text_lines.append(self.item_description_english)
        if self.item_description_spanish:
            text_lines.append(self.item_description_spanish)
        if self.item_description_french:
            text_lines.append(self.item_description_french)
        if self.lid_information_english:
            text_lines.append(self.lid_information_english)
        if self.lid_information_spanish:
            text_lines.append(self.lid_information_spanish)
        if self.lid_information_french:
            text_lines.append(self.lid_information_french)

        if self.item_name_a.draw_element:
            # Draw descriptions for panel A
            item_description_a_x = self.X_PANEL_A + self.MARGIN_WIDTH
            item_description_y = self.item_name_a.bottom_left_y - 0.25
            item_description_y -= text_height * len(text_lines)
            item_description_a = ItemDescriptionElement(
                "ItemDescriptionA",
                item_description_a_x,
                item_description_y,
                text_lines,
                can_move_x=can_move_x,
                can_move_y=can_move_y,
                group_id=1,
            )
            self.place_element(item_description_a)

        if self.item_name_b.draw_element:
            # Draw descriptions for panel B
            item_description_b_x = self.X_PANEL_C - self.MARGIN_WIDTH
            item_description_y = self.item_name_b.bottom_left_y - 0.25
            item_description_y -= text_height * len(text_lines)
            item_description_b = ItemDescriptionElement(
                "ItemDescriptionB",
                item_description_b_x,
                item_description_y,
                text_lines,
                text_align="end",
                can_move_x=can_move_x,
                can_move_y=can_move_y,
                alignment="right",
                group_id=2,
            )
            self.place_element(item_description_b)

        if self.item_name_c.draw_element:
            # Draw descriptions for panel C
            item_description_c_x = self.X_PANEL_C + self.MARGIN_WIDTH
            item_description_y = self.item_name_c.bottom_left_y - 0.25
            item_description_y -= text_height * len(text_lines)
            item_description_c = ItemDescriptionElement(
                "ItemDescriptionC",
                item_description_c_x,
                item_description_y,
                text_lines,
                can_move_x=can_move_x,
                can_move_y=can_move_y,
                group_id=3,
            )
            self.place_element(item_description_c)

        if self.item_name_d.draw_element:
            # Draw descriptions for panel D
            item_description_d_x = (
                self.X_PANEL_D + self.D_PANEL_SIDE - self.MARGIN_WIDTH
            )
            item_description_y = self.item_name_d.bottom_left_y - 0.25
            item_description_y -= text_height * len(text_lines)
            item_description_d = ItemDescriptionElement(
                "ItemDescriptionD",
                item_description_d_x,
                item_description_y,
                text_lines,
                text_align="end",
                can_move_x=can_move_x,
                can_move_y=can_move_y,
                alignment="right",
                group_id=4,
            )
            self.place_element(item_description_d)

    def __draw_company_logo(self, short_mode=False):
        """Draw the Graphic Packaging logo on the box, top of each panel."""
        # Setup kwargs for this set of elements.
        # min_scale = 0.5
        can_move_x = False
        can_move_y = False
        # min_x_dim = 3.0
        # min_y_dim = 3.0

        # Path to SVG file for the logo.
        # ip_logo_file_name = os.path.join(CORRUGATED_MEDIA_DIR, 'ip_logo.svg')
        ip_logo_file_name = os.path.join(CORRUGATED_MEDIA_DIR, "GPI_Black.svg")

        # This is good information for creating different logo sizes for the different boxes.
        print(("format: " + self.box_format.lower()))
        print(("a side: " + str(self.A_PANEL_SIDE)))
        print(("b side: " + str(self.B_PANEL_SIDE)))

        # Determine available area of the graphic. This, along with the width
        # of the graphic, will determine scaling.
        if self.A_PANEL_SIDE < 14:
            available_area_AC_side_x = self.A_PANEL_SIDE * 0.8 - 2 * self.MARGIN_WIDTH
        else:
            available_area_AC_side_x = self.A_PANEL_SIDE * 0.9 - 2 * self.MARGIN_WIDTH
        if self.SHORT_SIDE < 7.0:
            available_area_BD_side_x = self.B_PANEL_SIDE * 0.8 - 2 * self.MARGIN_WIDTH
        else:
            available_area_BD_side_x = self.B_PANEL_SIDE * 0.9 - 2 * self.MARGIN_WIDTH

        # Calculate y position for initial placement.
        # This will get moved down the height of the logo later.
        ip_logo_y = (
            self.Y_PANEL_A + (self.box_height - self.heightMod) - self.MARGIN_WIDTH
        )

        # In short mode the IP logo can't take up more than 1/6th of the
        # vertical space.
        if short_mode:
            available_area_y = (self.box_height - self.heightMod) * (0.167)
        else:
            available_area_y = None

        if (ip_logo_y - 2.5) < (self.stamper.bottom_left_x + self.stamper.height):
            available_area_A_side_label = (
                self.A_PANEL_SIDE - 6.0 - 2 * self.MARGIN_WIDTH
            )
            if available_area_A_side_label < available_area_AC_side_x:
                available_area_AC_side_x = available_area_A_side_label * 0.85

        # Begin graphic creation and placement.
        # Create and place logo for panel A.
        ip_logo_x = self.X_PANEL_A + self.MARGIN_WIDTH
        self.ip_logo_a = CompanyLogoElement(
            "IPLogoA",
            ip_logo_x,
            ip_logo_y,
            ip_logo_file_name,
            available_area_x=available_area_AC_side_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            padding=0.125,
            group_id=10,
        )
        self.place_element(self.ip_logo_a)

        # Create and place logo for panel B.
        if short_mode:  # GPI logo needs to swap sides in short mode.
            # We'll start moving it to the correct panel but we can't finish
            # until the logo's width is set later.
            ip_logo_x = self.X_PANEL_C - self.MARGIN_WIDTH
        else:
            ip_logo_x = self.X_PANEL_B + self.MARGIN_WIDTH
        self.ip_logo_b = CompanyLogoElement(
            "IPLogoB",
            ip_logo_x,
            ip_logo_y,
            ip_logo_file_name,
            available_area_x=available_area_BD_side_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            group_id=11,
        )
        if short_mode:
            # Finish moving it to the B panel now that we know it's width.
            self.ip_logo_b.bottom_left_x -= self.ip_logo_b.width
        self.place_element(self.ip_logo_b)

        # Create and place logo for panel C.
        ip_logo_x = self.X_PANEL_C + self.MARGIN_WIDTH
        self.ip_logo_c = CompanyLogoElement(
            "IPLogoC",
            ip_logo_x,
            ip_logo_y,
            ip_logo_file_name,
            available_area_x=available_area_AC_side_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            padding=0.125,
            group_id=12,
        )
        self.place_element(self.ip_logo_c)

        # Create and place logo for panel D.
        if short_mode:  # GPI logo needs to swap sides in short mode.
            # We'll start moving it to the correct panel but we can't finish
            # until the logo's width is set later.
            ip_logo_x = self.X_PANEL_D + self.B_PANEL_SIDE - self.MARGIN_WIDTH
        else:
            ip_logo_x = self.X_PANEL_D + self.MARGIN_WIDTH
        self.ip_logo_d = CompanyLogoElement(
            "IPLogoD",
            ip_logo_x,
            ip_logo_y,
            ip_logo_file_name,
            available_area_x=available_area_BD_side_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            group_id=13,
        )
        if short_mode:
            # Finish moving it to the D panel now that we know it's width.
            self.ip_logo_d.bottom_left_x -= self.ip_logo_d.width
        self.place_element(self.ip_logo_d)

        # Calculate available area and starting points.
        if self.box_format.lower() == "left":
            ip_logo_top_bottom_x = self.X_PANEL_A + 2.0 * self.MARGIN_WIDTH
            available_area_x = self.A_PANEL_SIDE - (4.0 * self.MARGIN_WIDTH)
        else:
            ip_logo_top_bottom_x = self.X_PANEL_B + self.MARGIN_WIDTH
            available_area_x = self.B_PANEL_SIDE - (4.0 * self.MARGIN_WIDTH)

        available_area_y = self.FLAP_HEIGHT - (2.0 * self.MARGIN_WIDTH)
        # Calculate y positon of top panel logo.
        ip_logo_top_y = (
            (self.FLAP_HEIGHT) + self.MARGIN_WIDTH + (self.box_height - self.heightMod)
        )
        # Create and place logo for top flap -- this one is different!

        # Here us some statements that will let us control the sizes of the Top panel logos.
        topModifier = 0.8
        if self.box_format.lower() == "right":
            if self.B_PANEL_SIDE > 12:
                topModifier = 0.8
            else:
                topModifier = 0.8
        else:
            if self.A_PANEL_SIDE > 12:
                topModifier = 0.9
            else:
                topModifier = 0.8

        ip_logo_top = CollidableSVGGraphicElement(
            "IPLogoTop",
            ip_logo_top_bottom_x,
            ip_logo_top_y,
            ip_logo_file_name,
            available_area_x=available_area_x * topModifier,
            available_area_y=available_area_y * topModifier,
            alignment="center",
            can_move_x=False,
            can_move_y=True,
        )
        self.place_element(ip_logo_top)

    def __draw_item_graphic(self, short_mode=False):
        """Draw the graphic of the item on each main panel.."""
        # Setup kwargs for this set of elements.
        min_scale = 0.5
        can_move_x = False
        can_move_y = False
        min_x_dim = 1.0
        min_y_dim = 1.0

        # Determine available area of the graphic. This, along with the width
        # of the graphic, will determine scaling.
        # *** This gets silly small for short sides under 6 or 8 inches.
        available_area_x = (self.SHORT_SIDE - 2 * self.MARGIN_WIDTH) / 3
        if available_area_x < 3:
            available_area_x = 3

        # Determine the y position for placement.
        item_graphic_y = self.item_name_a.bottom_left_y - 0.7

        if short_mode:
            # In short mode let to graphic grow all the way to the top of the panel.
            available_area_y = (
                self.Y_PANEL_A + (self.box_height - self.heightMod) - item_graphic_y
            )
        else:
            # Set the upper limit of the graphic to be the lowest of the
            # GPI logos.
            if self.ip_logo_c.bottom_left_y < self.ip_logo_b.bottom_left_y:
                # new gpi logo is bigger so we have to move the cup images down 3%
                top_limit = self.ip_logo_c.bottom_left_y
            else:
                top_limit = self.ip_logo_b.bottom_left_y
            top_limit -= 0.5
            available_area_y = top_limit - item_graphic_y - 0.25

        graphic_file = os.path.join(
            CORRUGATED_MEDIA_DIR, self.item_name.lower() + ".svg"
        )

        adjustmentArr = []
        elementArr = []
        if not short_mode:  # No room on panels A and B in short mode.
            # Create and place logo for panel A.
            item_graphic_x = self.X_PANEL_B - self.MARGIN_WIDTH
            item_graphic_a = CollidableSVGGraphicElement(
                "ItemGraphicA",
                item_graphic_x,
                item_graphic_y,
                graphic_file,
                available_area_x=available_area_x,
                available_area_y=available_area_y,
                alignment="right",
                can_move_x=can_move_x,
                can_move_y=can_move_y,
                min_scale=min_scale,
                min_x_dim=min_x_dim,
                min_y_dim=min_y_dim,
                group_id=10,
            )
            # here we set the element draw to false so it tries and returns the adjustments that need to be made
            # we also add the element to an array for later to apply the smaller adjustments and draw the element again
            item_graphic_a.draw_element = False
            adjustments = self.place_element(item_graphic_a, can_delete=True)
            adjustmentArr.append(adjustments)
            elementArr.append(item_graphic_a)

            # Create and place logo for panel B.
            item_graphic_x = self.X_PANEL_B + self.MARGIN_WIDTH
            item_graphic_b = CollidableSVGGraphicElement(
                "ItemGraphicB",
                item_graphic_x,
                item_graphic_y,
                graphic_file,
                available_area_x=available_area_x,
                available_area_y=available_area_y,
                alignment="left",
                can_move_x=can_move_x,
                can_move_y=can_move_y,
                min_scale=min_scale,
                min_x_dim=min_x_dim,
                min_y_dim=min_y_dim,
                group_id=11,
            )
            # here we set the element draw to false so it tries and returns the adjustments that need to be made
            # we also add the element to an array for later to apply the smaller adjustments and draw the element again
            item_graphic_b.draw_element = False
            adjustments = self.place_element(item_graphic_b, can_delete=True)
            adjustmentArr.append(adjustments)
            elementArr.append(item_graphic_b)
        # Create and place logo for panel C.
        item_graphic_x = self.X_PANEL_D - self.MARGIN_WIDTH
        item_graphic_c = CollidableSVGGraphicElement(
            "ItemGraphicC",
            item_graphic_x,
            item_graphic_y,
            graphic_file,
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            alignment="right",
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            min_scale=min_scale,
            min_x_dim=min_x_dim,
            min_y_dim=min_y_dim,
            group_id=12,
        )
        #        item_graphic_c.bottom_left_y -= item_graphic_c.height
        # here we set the element draw to false so it tries and returns the adjustments that need to be made
        # we also add the element to an array for later to apply the smaller adjustments and draw the element again
        item_graphic_c.draw_element = False
        adjustments = self.place_element(item_graphic_c, can_delete=True)
        adjustmentArr.append(adjustments)
        elementArr.append(item_graphic_c)

        # Create and place logo for panel D.
        item_graphic_x = self.X_PANEL_D + self.MARGIN_WIDTH
        item_graphic_d = CollidableSVGGraphicElement(
            "ItemGraphicD",
            item_graphic_x,
            item_graphic_y,
            graphic_file,
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            alignment="left",
            can_move_x=can_move_x,
            can_move_y=can_move_y,
            min_scale=min_scale,
            min_x_dim=min_x_dim,
            min_y_dim=min_y_dim,
            group_id=13,
        )

        #        item_graphic_d.bottom_left_y -= item_graphic_d.height
        # here we set the element draw to false so it tries and returns the adjustments that need to be made
        # we also add the element to an array for later to apply the smaller adjustments and draw the element again
        item_graphic_d.draw_element = False
        adjustments = self.place_element(item_graphic_d, can_delete=True)
        adjustmentArr.append(adjustments)
        elementArr.append(item_graphic_d)
        # This takes the array of adjustments and finds the smallest scaling factor
        currentSmallestItem = None
        for adjustment in adjustmentArr:
            if adjustment:
                if currentSmallestItem:
                    if adjustment["scaling"] < currentSmallestItem["scaling"]:
                        currentSmallestItem = adjustment
                else:
                    currentSmallestItem = adjustment
        # This applies the smaller scaling factor to all of the item elements and then draws them
        for x in range(len(adjustmentArr)):
            if currentSmallestItem:
                if not adjustmentArr[x]:
                    elementArr[x].height *= currentSmallestItem["scaling"]
                    elementArr[x].width *= currentSmallestItem["scaling"]
                    elementArr[x].drawing.scale(
                        currentSmallestItem["scaling"], currentSmallestItem["scaling"]
                    )
                    elementArr[x].bottom_left_y = currentSmallestItem["draw_y"]
            #                 elif adjustmentArr[x]['scaling'] > currentSmallestItem['scaling']:
            #                     elementArr[x].height *= (elementArr[x].height*(1 + (1 - adjustmentArr[x]['scaling'])))*currentSmallestItem['scaling']
            #                     elementArr[x].width *= (elementArr[x].width*(1 + (1 - adjustmentArr[x]['scaling'])))*currentSmallestItem['scaling']
            #                     elementArr[x].drawing.scale(currentSmallestItem['scaling'], currentSmallestItem['scaling'])
            #                     elementArr[x].bottom_left_y = currentSmallestItem['draw_y']
            elementArr[x].draw_element = True
            self.draw_element(self.canvas, elementArr[x], rotated=False)

    def __draw_sfi_graphic_container(self):
        """Draw the graphic if the BOX meets SFI certification,"""
        # Determine available area of the graphic. This, along with the width
        # of the graphic, will determine scaling.
        available_area_x = None
        available_area_y = None

        sfi_logo_location = "sfi_logo_right.svg"
        if self.plant == "Clarksville" or self.plant == "Pittston":
            sfi_logo_location = self.plant + "_sfi_logo_right.svg"

        # Create and place SFI graphic.
        sfi_graphic_x = self.X_PANEL_D + self.MARGIN_WIDTH
        sfi_graphic_y = self.Y_PANEL_A + self.MARGIN_WIDTH
        sfi_graphic = CollidableSVGGraphicElement(
            "SFIContainerLogo",
            sfi_graphic_x,
            sfi_graphic_y,
            os.path.join(CORRUGATED_MEDIA_DIR, sfi_logo_location),
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            group_id=7,
        )
        self.place_element(sfi_graphic)

    def __draw_ect_graphic_container(self):
        # Dimensions of the ECT/SFI logos for shellbyville and visalia
        shell_image_x = 8.29
        shell_image_y = 3.07
        vis_image_x = 8.27
        vis_image_y = 2.23
        ken_image_x = 8.29
        ken_image_y = 3.07
        clar_image_x = 8.29
        clar_image_y = 3.07
        pitt_image_x = 8.29
        pitt_image_y = 3.07
        """
        Draw the graphic if the BOX meets ect certification,
        """
        # Determine available area of the graphic. This, along with the width
        # of the graphic, will determine scaling.
        available_area_x = None
        available_area_y = None

        # kenton plant gets the SFI Logo like normal, Shelbyville and Visallia now
        # get a new logo on a different flap
        sfi_graphic_x = None
        sfi_graphic_y = None
        file_name = ""
        type = "ECT"

        # there are two sizes that have different logos for shel and vis, this will
        # search the board spec for the correct pattern (32 or 44)
        pattern51 = re.compile("[5][1]")
        pattern48 = re.compile("[4][8]")
        pattern44 = re.compile("[4][4]")
        pattern40 = re.compile("[4][0]")
        pattern32 = re.compile("[3][2]")
        pattern29 = re.compile("[2][9]")
        file_name += self.plant + "_" + type + "_"
        if pattern51.search(self.board_spec):
            file_name += "51"
            if self.plant == "Clarksville":
                sfi_graphic_y = (self.FLAP_HEIGHT - clar_image_y) / 2
            else:
                return
        elif pattern48.search(self.board_spec):
            file_name += "48"
            if self.plant == "Clarksville":
                sfi_graphic_y = (self.FLAP_HEIGHT - clar_image_y) / 2
            else:
                return
        elif pattern40.search(self.board_spec):
            file_name += "40"
            if self.plant == "Clarksville":
                sfi_graphic_y = (self.FLAP_HEIGHT - clar_image_y) / 2
            elif self.plant == "Pittston":
                sfi_graphic_y = (self.FLAP_HEIGHT - pitt_image_y) / 2
            else:
                return
        elif pattern44.search(self.board_spec):
            file_name += "44"
            if self.plant == "Shelbyville":
                sfi_graphic_y = (self.FLAP_HEIGHT - shell_image_y) / 2
            elif self.plant == "Visalia":
                sfi_graphic_y = (self.FLAP_HEIGHT - pitt_image_y) / 2
            elif self.plant == "Kenton":
                sfi_graphic_y = (self.FLAP_HEIGHT - ken_image_y) / 2
            elif self.plant == "Pittston":
                sfi_graphic_y = (self.FLAP_HEIGHT - pitt_image_y) / 2
            elif self.plant == "Clarksville":
                sfi_graphic_y = (self.FLAP_HEIGHT - clar_image_y) / 2
            else:
                return
        elif pattern32.search(self.board_spec):
            file_name += "32"
            if self.plant == "Shelbyville":
                sfi_graphic_y = (self.FLAP_HEIGHT - shell_image_y) / 2
            elif self.plant == "Visalia":
                sfi_graphic_y = (self.FLAP_HEIGHT - vis_image_y) / 2
            elif self.plant == "Kenton":
                sfi_graphic_y = (self.FLAP_HEIGHT - ken_image_y) / 2
            elif self.plant == "Pittston":
                sfi_graphic_y = (self.FLAP_HEIGHT - pitt_image_y) / 2
            elif self.plant == "Clarksville":
                sfi_graphic_y = (self.FLAP_HEIGHT - clar_image_y) / 2
            else:
                return
        elif pattern29.search(self.board_spec):
            file_name += "29"
            if self.plant == "Kenton":
                sfi_graphic_y = (self.FLAP_HEIGHT - ken_image_y) / 2
            else:
                return
        else:
            file_name = type + "_ERROR"
            sfi_graphic_y = self.FLAP_HEIGHT / 2.0 - 0.7

        if self.format.lower() == "left":
            if self.plant == "Shelbyville":
                sfi_graphic_x = self.X_PANEL_A + (self.A_PANEL_SIDE - shell_image_x) / 2
            elif self.plant == "Clarksville":
                sfi_graphic_x = self.X_PANEL_A + (self.A_PANEL_SIDE - clar_image_x) / 2
            elif self.plant == "Pittston":
                sfi_graphic_x = self.X_PANEL_A + (self.A_PANEL_SIDE - pitt_image_x) / 2
            elif self.plant == "Visalia":
                sfi_graphic_x = self.X_PANEL_A + (self.A_PANEL_SIDE - vis_image_x) / 2
            elif self.plant == "Kenton":
                sfi_graphic_x = self.X_PANEL_A + (self.A_PANEL_SIDE - ken_image_x) / 2
            else:
                return
        else:
            if self.plant == "Shelbyville":
                sfi_graphic_x = self.X_PANEL_B + (self.B_PANEL_SIDE - shell_image_x) / 2
            elif self.plant == "Clarksville":
                sfi_graphic_x = self.X_PANEL_B + (self.B_PANEL_SIDE - clar_image_x) / 2
            elif self.plant == "Pittston":
                sfi_graphic_x = self.X_PANEL_B + (self.B_PANEL_SIDE - pitt_image_x) / 2
            elif self.plant == "Visalia":
                sfi_graphic_x = self.X_PANEL_B + (self.A_PANEL_SIDE - vis_image_x) / 2
            else:
                return
        file_name += ".svg"
        # Create and place SFI graphic and ignore margins so that it places
        # within the bounds of the flap but at the correct logo size
        sfi_graphic = CollidableSVGGraphicElement(
            "SFIContainerLogo",
            sfi_graphic_x,
            sfi_graphic_y,
            os.path.join(CORRUGATED_MEDIA_DIR, file_name),
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            group_id=7,
        )
        self.place_element(sfi_graphic, ignore_margins=True)

    def __draw_sfi_graphic_contents(self):
        """Draw the graphic if the CONTENTS of the box meet SFI certification,"""
        # Determine available area of the graphic. This, along with the width
        # of the graphic, will determine scaling.
        # (Note: These variables are not currently used but may be needed for future scaling logic)

        # Create and place SFI graphic.
        # (Currently commented out as the graphic creation is not being used)
        # sfi_graphic = CollidableSVGGraphicElement(
        #     "SFIContentLogo",
        #     sfi_graphic_x,
        #     sfi_graphic_y,
        #     os.path.join(CORRUGATED_MEDIA_DIR, sfi_logo_location),
        #     available_area_x=available_area_x,
        #     available_area_y=available_area_y,
        #     alignment="right",
        #     group_id=7,
        # )
        # self.place_element(sfi_graphic)

    def __draw_specialty_logo(self, type=False, short_mode=False):
        """Draw specialty logos on the box, near the middle of each panel as
        needed. Specialty logos include Ecotainer Logos, Hold&Go Logos, and
        Hold&Cold logos.
        """
        # Setup kwargs for this set of elements.
        can_move_x = False
        can_move_y = False

        # Path to SVG file for the logo.
        if type == "ecotainer":
            specialty_logo_file_name = os.path.join(
                CORRUGATED_MEDIA_DIR, "ecotainer.svg"
            )
        elif type == "holdngo":
            specialty_logo_file_name = os.path.join(CORRUGATED_MEDIA_DIR, "holdngo.svg")
        else:
            # Can't go any further without a logo file. Bail out.
            return False

        # Determine available area of the graphic. This, along with the width
        # of the graphic, will determine scaling.
        available_area_x = (self.SHORT_SIDE * 0.5) - self.MARGIN_WIDTH
        print(("Available area: %s" % available_area_x))

        # Calculate y position for initial placement.
        if short_mode:  # Place directly under the GPI logo for short boxes.
            if self.A_PANEL_SIDE == self.SHORT_SIDE:  # Pick the lower GPI logo.
                specialty_logo_Y = self.ip_logo_a.bottom_left_y - 0.25
            else:
                specialty_logo_Y = self.ip_logo_b.bottom_left_y - 0.25
            # In short mode the logo can't take up more than 1/6th of the
            # vertical space.
            available_area_y = (self.box_height - self.heightMod) * (0.167)
        else:  # Leave a gap for longer boxes.
            specialty_logo_Y = self.Y_PANEL_A + (
                (self.box_height - self.heightMod) * 0.75
            )
            available_area_y = None

        # Begin graphic creation and placement.
        # Create and place logo for panel A.
        specialty_logo_X = 0 + self.MARGIN_WIDTH
        self.specialty_logo_a = SpecialtyLogoElement(
            "SpecialtyLogoA",
            specialty_logo_X,
            specialty_logo_Y,
            specialty_logo_file_name,
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
        )
        self.place_element(self.specialty_logo_a)

        # Create and place logo for panel B.
        specialty_logo_X = self.X_PANEL_C - available_area_x - self.MARGIN_WIDTH
        self.specialty_logo_b = SpecialtyLogoElement(
            "SpecialtyLogoB",
            specialty_logo_X,
            specialty_logo_Y,
            specialty_logo_file_name,
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
        )
        self.place_element(self.specialty_logo_b)

        # Create and place logo for panel C.
        specialty_logo_X = self.X_PANEL_C + self.MARGIN_WIDTH
        self.specialty_logo_c = SpecialtyLogoElement(
            "SpecialtyLogoC",
            specialty_logo_X,
            specialty_logo_Y,
            specialty_logo_file_name,
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
        )
        self.place_element(self.specialty_logo_c)

        # Create and place logo for panel D.
        specialty_logo_X = (
            self.X_PANEL_D + self.B_PANEL_SIDE - self.MARGIN_WIDTH - available_area_x
        )
        self.specialty_logo_d = SpecialtyLogoElement(
            "SpecialtyLogoD",
            specialty_logo_X,
            specialty_logo_Y,
            specialty_logo_file_name,
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
        )
        self.place_element(self.specialty_logo_d)

        # Draw logo on top flap of the box, upside down.
        # X placement is different on left and right box formats.
        if self.box_format.lower() == "left":
            specialty_logo_X = self.X_PANEL_C + self.MARGIN_WIDTH + available_area_x
        else:
            specialty_logo_X = self.X_PANEL_D + self.MARGIN_WIDTH + available_area_x

        specialty_logo_Y = (
            self.Y_PANEL_A + (self.box_height - self.heightMod) + self.MARGIN_WIDTH
        )
        self.specialty_logo_top = SpecialtyLogoElement(
            "SpecialtyLogoTop",
            specialty_logo_X,
            specialty_logo_Y,
            specialty_logo_file_name,
            available_area_x=available_area_x,
            available_area_y=available_area_y,
            can_move_x=can_move_x,
            can_move_y=can_move_y,
        )
        self.specialty_logo_top.bottom_left_y = (
            specialty_logo_Y + self.specialty_logo_top.height
        )
        self.place_element(self.specialty_logo_top, rotated=True)

    def __draw_fsb_elements(self):
        """Draws and places all of the elements on the FSBBox.
        Currently, the draw order determines the drawing priority. Elements
        drawn last are more likely to move/be deleted in event of collisions.
        """
        # Draw the label area (contains barcodes and identifying text).
        self.__draw_label_area()
        # Draw the stamper box.
        self.__draw_stamper_box()
        # Draw the machine bar code box.
        self.__draw_machine_barcode_box()
        # Draw six_digit barcode
        self.__draw_barcode_six_digit_barcode()
        # Draw the ect graphics for shelbyville and visalia regardless of selected artwork
        self.__draw_ect_graphic_container()

        """"
        We will draw some box elements differently depending on which is
        smaller: the height of the box or the width of the short side (the
        short side is the skinniest panel on the box.) If the box_height is
        smaller than the short side's width we'll draw things in "short mode"
        which means elements will be sized based on their vertical height since
        that's the space we have less of.
        """
        if self.box_height <= self.SHORT_SIDE:
            short_mode = True
        else:
            short_mode = False

        if self.pdf_type is None:
            self.pdf_type = 0
        if self.pdf_type == 0 or self.pdf_type == 1:
            # Draw the GPI logo on to box, top of each main panel.
            self.__draw_company_logo(short_mode)
            # Draw any ectainer, hold&go, etc. logos.
            print(("Size: %s" % self.item_name))
            # Check if any specialty logos need to be placed.
            try:
                # Hold&Gos start with "SD" or have "D" as the 3rd letter in their size.
                if (self.item_name[0] == "S" and self.item_name[1] == "D") or (
                    self.item_name[0] == "L" and self.item_name[2] == "D"
                ):
                    print("Hold&Go size. Placing Hold&Go logo.")
                    self.__draw_specialty_logo("holdngo", short_mode)
                # Ecotainers will have an "E" as the 4th or 5th letter in their size.
                elif self.item_name[3] == "E" or self.item_name[4] == "E":
                    print("Ecotainer size. Placing Ecotainer logo.")
                    self.__draw_specialty_logo("ecotainer", short_mode)
                else:
                    print("Not an Ecotainer or Hold&Go size.")
            except Exception:
                print("Error placing Ecotainer or Hold&Go. Passing.")
                pass
            # Draw the item (contents of box) name.
            self.__draw_item_name(short_mode)
            # Draw the item descriptions under the item names.
            self.__draw_item_description()
            # Draw SFI logos if needed.
            if self.sfi_container:
                self.__draw_sfi_graphic_container()
            if self.sfi_contents:
                self.__draw_sfi_graphic_contents()
            # Draw case and sleeve counts.
            self.__draw_case_sleeve_counts()
            # Handle drawing the text on the flaps.
            self.__draw_flap_text()
            # Draw the item graphic on each main panel.
            self.__draw_item_graphic(short_mode)

        print("Finished Drawing...")

    def __draw_fsb_print_header(self):
        """Draw the print header across the top of the page."""
        if self.pdf_type is None:
            self.pdf_type = 0
        c = self.canvas
        # Sets the color of the panel outlines. Original values were (0, 0, 0, 0.75) for both
        c.setStrokeColorCMYK(0.65, 0.60, 0.55, 0)
        c.setFillColorCMYK(0.65, 0.60, 0.55, 0)

        # Print card header outline.
        header_x1 = self.X_PANEL_A
        header_y1 = 0.5 + self.SHORT_SIDE + self.box_height
        header_x2 = (
            self.A_PANEL_SIDE
            + self.B_PANEL_SIDE
            + self.C_PANEL_SIDE
            + self.D_PANEL_SIDE
        )
        header_y2 = self.canvas_height - self.box_height - self.SHORT_SIDE - 8.0

        c.rect(
            header_x1 * inch,
            header_y1 * inch,
            header_x2 * inch,
            header_y2 * inch,
            stroke=1,
            fill=0,
        )

        font_size = header_y2 / 5.5 * 36
        column_a_x = header_x2 / 4.0
        column_b_x = column_a_x + (header_x2 / 2.0)
        c.setFont("Helvetica-Bold", font_size)
        TEXT_SPACING = (font_size * 1.25) / 72.0
        TEXT_START = header_y1 + header_y2 - TEXT_SPACING
        header_text = "GPI Corrugate Packaging Specifications"
        if self.job_id:
            header_text += ": GOLD# %s" % str(self.job_id)
        else:
            header_text += ": GOLD# ??????"
        c.drawString((header_x1 + column_a_x) * inch, TEXT_START * inch, header_text)

        c.drawRightString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - TEXT_SPACING) * inch,
            "Customer Identification:",
        )
        c.drawRightString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 2.0 * TEXT_SPACING) * inch,
            "Packaging Identification:",
        )
        c.drawRightString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 3.0 * TEXT_SPACING) * inch,
            "Inner Dim. (L x W x H):",
        )
        c.drawRightString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 4.0 * TEXT_SPACING) * inch,
            "Outer Dim. (L x W x H):",
        )
        c.drawRightString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 5.0 * TEXT_SPACING) * inch,
            "Case Quantity:",
        )
        c.drawRightString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 6.0 * TEXT_SPACING) * inch,
            "Board Specification:",
        )
        # Commented this line so that, we don't have add this to the PDF later.
        # if self.artist:
        c.drawRightString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 7.0 * TEXT_SPACING) * inch,
            "Artist:",
        )

        c.drawRightString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - TEXT_SPACING) * inch,
            "Case Color:",
        )
        if self.plate_number:
            c.drawRightString(
                (header_x1 + column_b_x + 9.5) * inch,
                (TEXT_START - TEXT_SPACING) * inch,
                "Plate #:",
            )
        c.drawRightString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 2.0 * TEXT_SPACING) * inch,
            "Print Color:",
        )
        c.drawRightString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 3.0 * TEXT_SPACING) * inch,
            "Date:",
        )
        c.drawRightString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 4.0 * TEXT_SPACING) * inch,
            "Manufacturing Plant:",
        )
        c.drawRightString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 5.0 * TEXT_SPACING) * inch,
            "Part Number:",
        )
        if self.replaced_6digit:
            c.drawRightString(
                (header_x1 + column_b_x + 9.5) * inch,
                (TEXT_START - 5.0 * TEXT_SPACING) * inch,
                "Replaces:",
            )
        c.drawRightString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 6.0 * TEXT_SPACING) * inch,
            "Box Format:",
        )

        c.drawRightString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 7.0 * TEXT_SPACING) * inch,
            "Nine Digit Number:",
        )

        column_a_x += font_size / 144.0
        column_b_x += font_size / 144.0
        c.setFont("Helvetica", font_size)
        c.drawString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - TEXT_SPACING) * inch,
            "Graphic Packaging Foodservice",
        )
        c.drawString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 2.0 * TEXT_SPACING) * inch,
            self.item_name,
        )
        if self.plant == "Shelbyville":
            c.drawString(
                (header_x1 + column_a_x) * inch,
                (TEXT_START - 3.0 * TEXT_SPACING) * inch,
                "%s x %s x %s inches"
                % (
                    str(self.box_length - 0.3125),
                    str(self.box_width - 0.3125),
                    str(self.box_height - 0.625),
                ),
            )
        else:
            c.drawString(
                (header_x1 + column_a_x) * inch,
                (TEXT_START - 3.0 * TEXT_SPACING) * inch,
                "%s x %s x %s inches"
                % (
                    str(self.box_length - 0.375),
                    str(self.box_width - 0.375),
                    str(self.box_height - 0.75),
                ),
            )
        c.drawString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 4.0 * TEXT_SPACING) * inch,
            "%s x %s x %s inches"
            % (str(self.box_length), str(self.box_width), str(self.box_height)),
        )
        c.drawString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 5.0 * TEXT_SPACING) * inch,
            "%s/case, %s/sleeve" % (str(self.case_count), str(self.sleeve_count)),
        )
        c.drawString(
            (header_x1 + column_a_x) * inch,
            (TEXT_START - 6.0 * TEXT_SPACING) * inch,
            self.board_spec,
        )
        if self.artist:
            c.drawString(
                (header_x1 + column_a_x) * inch,
                (TEXT_START - 7.0 * TEXT_SPACING) * inch,
                "%s %s" % (str(self.artist.first_name), str(self.artist.last_name)),
            )
        # Added this else statement to give the Artist working on the job an easy way just to
        # start adding text per their request
        else:
            c.drawString(
                (header_x1 + column_a_x) * inch,
                (TEXT_START - 7.0 * TEXT_SPACING) * inch,
                "??????",
            )

        c.drawString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - TEXT_SPACING) * inch,
            self.case_color,
        )
        if self.plate_number:
            c.drawString(
                (header_x1 + column_b_x + 9.3) * inch,
                (TEXT_START - TEXT_SPACING) * inch,
                str(self.plate_number),
            )
        c.drawString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 2.0 * TEXT_SPACING) * inch,
            "90 Black",
        )
        c.drawString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 3.0 * TEXT_SPACING) * inch,
            str(general_funcs._utcnow_naive().strftime("%m-%d-%Y")),
        )
        c.drawString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 4.0 * TEXT_SPACING) * inch,
            self.plant,
        )
        c.drawString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 5.0 * TEXT_SPACING) * inch,
            str(self.six_digit_num),
        )
        if self.replaced_6digit:
            c.drawString(
                (header_x1 + column_b_x + 9.3) * inch,
                (TEXT_START - 5.0 * TEXT_SPACING) * inch,
                str(self.replaced_6digit),
            )
        c.drawString(
            (header_x1 + column_b_x) * inch,
            (TEXT_START - 6.0 * TEXT_SPACING) * inch,
            self.format,
        )
        if self.pdf_type == 0 or self.pdf_type == 2:
            c.drawString(
                (header_x1 + column_b_x) * inch,
                (TEXT_START - 7.0 * TEXT_SPACING) * inch,
                str(self.nine_digit_num),
            )
        else:
            c.drawString(
                (header_x1 + column_b_x) * inch,
                (TEXT_START - 7.0 * TEXT_SPACING) * inch,
                "Blank",
            )

        # Impression slug designation, Order#, and Date on the D flap of the box for Kenton
        if self.plant == "Kenton":
            bottomLeftFlap_location = (
                self.A_PANEL_SIDE
                + self.B_PANEL_SIDE
                + self.C_PANEL_SIDE
                + (self.D_PANEL_SIDE / 2)
                + 1
            )
            c = self.canvas
            # Sets the color of the panel outlines. Original values were (0, 0, 0, 0.75) for both
            c.setStrokeColorCMYK(0.65, 0.60, 0.55, 0)
            c.setFillColorCMYK(0.65, 0.60, 0.55, 0)
            ## Impression slug designation.
            c.setFont("Helvetica-Bold", 40)
            c.drawRightString(
                (bottomLeftFlap_location + 0.9) * inch,
                (self.FLAP_HEIGHT / 2.0 + 0.5) * inch,
                "Impression",
            )
            c.drawRightString(
                bottomLeftFlap_location * inch,
                (self.FLAP_HEIGHT / 2.0 - 0) * inch,
                "Slug",
            )
            c.drawRightString(
                (bottomLeftFlap_location + 0.01) * inch,
                (self.FLAP_HEIGHT / 2.0 - 0.5) * inch,
                "Here",
            )
            # Date and Order #
            c.setFont("Helvetica-Bold", 30)
            c.drawRightString(
                bottomLeftFlap_location * inch,
                (self.FLAP_HEIGHT / 2.0 - 1.5) * inch,
                "Order #: ",
            )
            c.drawRightString(
                bottomLeftFlap_location * inch,
                (self.FLAP_HEIGHT / 2.0 - 2) * inch,
                "Date: ",
            )

        # Impression slug designation.
        imp_slug_plants = ["Clarksville", "Visalia"]
        if self.plant in imp_slug_plants:
            bottomLeftFlap_location = (
                self.A_PANEL_SIDE
                + self.B_PANEL_SIDE
                + self.C_PANEL_SIDE
                + (self.D_PANEL_SIDE / 2)
                + 1
            )
            c = self.canvas
            # Sets the color of the panel outlines. Original values were (0, 0, 0, 0.75) for both
            c.setStrokeColorCMYK(0.65, 0.60, 0.55, 0)
            c.setFillColorCMYK(0.65, 0.60, 0.55, 0)
            c.setFont("Helvetica-Bold", 40)
            c.drawRightString(
                (bottomLeftFlap_location + 0.9) * inch,
                (self.FLAP_HEIGHT / 2.0 + 0.5) * inch,
                "Impression",
            )
            c.drawRightString(
                bottomLeftFlap_location * inch,
                (self.FLAP_HEIGHT / 2.0 - 0) * inch,
                "Slug",
            )
            c.drawRightString(
                (bottomLeftFlap_location + 0.01) * inch,
                (self.FLAP_HEIGHT / 2.0 - 0.5) * inch,
                "Here",
            )

    def __draw_watermark(self):
        """Draws watermark over artwork. This is for pre-approval PDF artwork.
        Discourages use of art before it is approved and paid for.
        """
        c = self.canvas
        # Set watermark parameters.
        font_size = 1000
        font_style = "Helvetica-Oblique"
        watermark_text = "FOR APPROVAL"
        c.setFillColorCMYK(0, 0.1, 0, 0)
        # Check watermark width and adjust start points to canvas size.
        text_width = check_text_width(font_size, font_style, watermark_text)
        # Adjust font size if the text width exceeds canvas.
        while text_width > self.canvas_width - 4.0:
            font_size = font_size - 50
            text_width = check_text_width(font_size, font_style, watermark_text)
            # print "Reducing watermark font size to", font_size
        start_x = (self.canvas_width - text_width) / 2.0
        start_y = self.canvas_height / 2.0 - 2.0
        #  Set font and draw watermark.
        c.setFont(font_style, font_size)
        c.drawString(start_x * inch, start_y * inch, watermark_text)


class FSBLabel(GenericLabel):
    """Standard Foodservice label object. Labels are placed on the corner of
    a corrugated box. The standard FSBBox has a pre-printed label. This label
    would be placed on top of that with updated/different information.
    """

    def __init__(
        self,
        file_name,
        nine_digit_num,
        fourteen_digit_num,
        text_line_1,
        text_line_2,
        pdf_type,
        label_id,
    ):
        """Handles drawing the canvas and preparing other storage variables.

        file_name: (str) Path to the eventual finished PDF.
        nine_digit_num: (int) Barcode number 1.
        fourteen_digit_num: (int) Barcode number 2.
        text_line_1: (str) String to appear in the LabelAreaElement.
        text_line_2: (str) String to appear in the LabelAreaElement.
        """
        # Call GenericBox's __init__() method.
        super(FSBLabel, self).__init__(file_name)

        # Transfer variables that are specific to FSBBox objects.
        self.file_name = file_name
        self.nine_digit_num = nine_digit_num
        self.fourteen_digit_num = fourteen_digit_num
        self.text_line_1 = text_line_1
        self.text_line_2 = text_line_2
        self.pdf_type = pdf_type
        self.label_id = label_id

        # Only one object we need to draw here.
        self.__draw_label_area()

        # Close drawing on the first page.
        self.canvas.showPage()

    def __draw_label_area(self):
        """Draw the label area and accompanying barcodes. Label area falls on
        the corner of the box, and is equally distributed on two panels.
        """
        label_area_bottom_left_x = 0.0
        label_area_bottom_left_y = 0.0

        # Right now we will make all methods autoeng so that is tried to make new barcodes every time that are
        # production ready as only artists use this to regenerate barcodes.
        method = "automationEngine"

        # Labels won't have a case count. Don't do that part, then.
        try:
            case_count = self.case_count
        except AttributeError:
            case_count = None

        self.elem_label_area = LabelAreaElement(
            "LabelArea",
            label_area_bottom_left_x,
            label_area_bottom_left_y,
            self.nine_digit_num,
            self.fourteen_digit_num,
            self.text_line_1,
            self.text_line_2,
            None,
            case_count,
            self.pdf_type,
            self.label_id,
            method,
            group_id=1,
        )
        self.place_element(self.elem_label_area)
