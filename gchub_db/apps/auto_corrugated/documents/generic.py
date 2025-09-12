"""Generic corrugated documents."""

from fractions import Fraction
from reportlab.graphics import renderPDF
from reportlab.lib.units import inch

from gchub_db.apps.auto_corrugated.elements.common import MarginElement
from gchub_db.includes.reportlib.documents.canvas import GenericCanvas
from gchub_db.includes.reportlib.util import check_text_width

"""
This module contains high-level document classes for generating things such
as Foodservice containerboard artwork and label images.
"""


class ElementGroup(object):
    def __init__(self, group_num, *args, **kwargs):
        self.group_num = group_num
        self.group_x = None
        self.group_y = None
        self.group_height = None
        self.group_width = None
        self.element_list = []

    def determine_group_dimensions(self):
        """
        Determine the x/y and w/h of the group, as well as each element's
        relative position to the group. (delta_x & delta_y)
        """
        upper_right_x = None
        upper_right_y = None

        first_element = True
        # First, set overall group x,y,w,h
        for element in self.element_list:
            if first_element:
                # Set some variables to start -- for the first element.
                self.group_x = element.bottom_left_x
                self.group_y = element.bottom_left_y
                upper_right_x = element.bottom_left_x + element.width
                upper_right_y = element.bottom_left_y + element.height
                first_element = False
            else:
                if element.bottom_left_x < self.group_x:
                    self.group_x = element.bottom_left_x
                if element.bottom_left_y < self.group_y:
                    self.group_y = element.bottom_left_y
                if (element.bottom_left_x + element.width) > upper_right_x:
                    upper_right_x = element.bottom_left_x + element.width
                if (element.bottom_left_y + element.height) > upper_right_y:
                    upper_right_y = element.bottom_left_y + element.height

        self.height = upper_right_y - self.group_y
        self.width = upper_right_x - self.group_x

        # Secondly, set delta_x and delta_y for each element in relation to the group.
        for element in self.element_list:
            element.group_delta_x = element.bottom_left_x - self.group_x
            element.group_delta_y = element.bottom_left_y - self.group_y


class GenericBox(GenericCanvas):
    def __init__(self, file_name, width, height, length, format, print_header, encrypt, plant):
        """
        Handles drawing the canvas and preparing other storage variables.

        file_name: (str) Path to the eventual finished PDF.
        width: (float) Width of the box (in inches)
        height: (float) Height of the box (in inches)
        length: (float) Length of the box (in inches)
        encrypt: (bool) Should PDF be encrypted?
        """
        self.DEBUG = False
        # This is the margin of the entire box. No elements to be placed on
        # panels within this far of the scores/cuts.
        self.MARGIN_WIDTH = 1.0
        self.side_flap_offset = 0
        # These move dimension lines left or right to make room for a glue flap.
        self.box_shift_left = 0
        self.box_shift_right = 0
        if plant == "Kenton":
            self.side_flap_offset = 1.0  # (1 and 3/8 inch) but we shortended it to 1 for spacing reasons
            # Has a glue flap on the right.
            self.box_shift_right = 1.375
        elif plant == "Pittston":
            self.side_flap_offset = 1.375
            # Has a glue flap on the left.
            self.box_shift_left = self.side_flap_offset
        elif plant == "Clarksville":
            self.side_flap_offset = 1.375
            # Has a glue flap on the left.
            self.box_shift_left = self.side_flap_offset
        elif plant == "Shelbyville":
            if format == "right":
                # Has a glue flap on the left. Yes it's opposite the format for this plant.
                self.side_flap_offset = 1.375
                self.box_shift_left = self.side_flap_offset
            else:
                # Has a glue flap on the right.
                self.side_flap_offset = 1.0
                self.box_shift_right = 1.375
        self.box_format = format
        self.box_width = width
        self.box_height = height
        self.box_length = length
        self.encrypt = encrypt

        self.plant = plant
        if self.plant == "Pittston":
            self.heightMod = 0.375
        elif self.plant == "Clarksville":
            self.heightMod = 0.375  # (0.4375 (7/16) - 0.0625 (1/16))
        elif self.plant == "Shelbyville":
            self.heightMod = 0.25
        else:
            self.heightMod = 0.4375

        #  Figure out where the long and short sides are.
        self.__determine_long_and_short_sides(width, height, length)

        # Calculate the actual reportlab Canvas size.
        CANVAS_MARGIN = 8.0
        self.canvas_width = 2.0 * self.box_width + 2.0 * self.box_length + CANVAS_MARGIN
        self.canvas_height = self.box_height + self.SHORT_SIDE + CANVAS_MARGIN

        # If there is a print header, add on an appropriate amount of
        # height above the template -- as proportion of width.
        if print_header:
            self.canvas_height += self.canvas_width / 7.6

        # Call the __init__ method from the GenericCanvas parent class.
        super(GenericBox, self).__init__(file_name, self.canvas_width, self.canvas_height, encrypt=self.encrypt)
        # Moves the origin out of the bleed to the beginning of the art board.
        self.canvas.translate(
            (CANVAS_MARGIN / 2.0 + self.side_flap_offset) * inch,
            (CANVAS_MARGIN / 2.0) * inch,
        )
        # Sets some easily accessed variables for each panel's origin point.
        self.__set_panel_origin_variables()
        # Get to it!
        self.__draw_box_basics()

    def __draw_box_basics(self):
        """
        This method contains the logic for drawing the basic common
        elements in a box (but not actually saving it to a file).
        """
        self.__draw_box_panel_outlines()
        self.__register_margins()
        self.__draw_box_dimension_lines()

    def __draw_element(self, canvas, element, rotated=False):
        """
        Within place_element(), this function draws the Drawing object
        on the Canvas.
        Handle bottom x/y and top x/y separately here. Actual x/y coordinates
        for drawing on the canvas are going to be different depending on
        alignment and rotation.
        """
        # At this point, the bottom_left_x is the physical location
        # of the object, which needs to be adjusted if the element is
        # aligned to the right.
        # This only applies to text boxes where the TEXT is aligned
        # to the end.
        if element.text_align == "end":
            drawing_bottom_left_x = element.bottom_left_x + element.width
        else:
            drawing_bottom_left_x = element.bottom_left_x

        drawing_bottom_left_y = element.bottom_left_y

        if rotated:
            drawing_bottom_left_x += element.width
            drawing_bottom_left_y += element.height

        # canvas.setStrokeColorCMYK(0, 0.5, 0, 0)
        # canvas.setFillColorCMYK(0, 0.5, 0, 0)

        if rotated:
            canvas.rotate(180)
            # Draws the element on the master canvas
            renderPDF.draw(
                element.drawing,
                canvas,
                -drawing_bottom_left_x * inch,
                -drawing_bottom_left_y * inch,
            )
            canvas.rotate(-180)
        else:
            # Draws the element on the master canvas
            renderPDF.draw(
                element.drawing,
                canvas,
                drawing_bottom_left_x * inch,
                drawing_bottom_left_y * inch,
            )

    def __detect_collisions(self, element, ignore_margins=False, **kwargs):
        """Determine if new object overlaps any existing objects."""
        # Declare variable from element object.
        bottom_left_x = element.bottom_left_x
        bottom_left_y = element.bottom_left_y

        fix_x = element.fix_x
        fix_y = element.fix_y

        top_right_x = bottom_left_x + element.width
        top_right_y = bottom_left_y + element.height
        # Define variables for returnng data about  the collision.
        # Direction that collision correction needs to occur in.
        direction = None
        # Object that was collided with.
        object = None
        # Distance to correct for. (Amount of overlap)
        distance = 0

        # Iterate through all registered objects, testing for collision.
        for obj in self.element_list:
            # If ignore_margins is True, don't look for collisions with those objects.
            if obj.name.lower().startswith("margin") and ignore_margins:
                pass
            else:
                # Setup variables for each existing obj.
                existing_obj_bottom_left_x = obj.bottom_left_x - obj.padding
                existing_obj_bottom_left_y = obj.bottom_left_y - obj.padding
                existing_obj_top_right_x = existing_obj_bottom_left_x + obj.width + (2.0 * obj.padding)
                existing_obj_top_right_y = existing_obj_bottom_left_y + obj.height + (2.0 * obj.padding)
                # Either bottom left point of test obj. is above and right of existing obj.
                # or top right point of test obj. is below and left of existing obj.
                # This means that the objects definitely don't overlap.
                if (bottom_left_y >= existing_obj_top_right_y or bottom_left_x >= existing_obj_top_right_x) or (
                    top_right_y <= existing_obj_bottom_left_y or top_right_x <= existing_obj_bottom_left_x
                ):
                    collision = False
                else:
                    # One of the y points is between the test y points, and the left x
                    # is left of the test right x, or the right x is right of the text
                    # left x.
                    if (
                        existing_obj_bottom_left_y < bottom_left_y < existing_obj_top_right_y
                        or existing_obj_bottom_left_y < top_right_y < existing_obj_top_right_y
                    ) and (bottom_left_x > existing_obj_top_right_x or top_right_x > existing_obj_bottom_left_x):
                        collision = True
                    # One of the x points is between the test x points, and the top y
                    # is above the test bottom y, or the bottom y is below the test
                    # top y.
                    if (
                        existing_obj_bottom_left_x < bottom_left_x < existing_obj_top_right_x
                        or existing_obj_bottom_left_x < top_right_x < existing_obj_top_right_x
                    ) and (bottom_left_y > existing_obj_top_right_y or top_right_y > existing_obj_bottom_left_y):
                        collision = True

                # Check for complete overlap.
                if (bottom_left_x <= existing_obj_bottom_left_x and bottom_left_y <= existing_obj_bottom_left_y) and (
                    top_right_x >= existing_obj_top_right_x and top_right_y >= existing_obj_top_right_y
                ):
                    if self.DEBUG:
                        print("@>>>WARNING: Complete coverage of new object over existing!")
                    element.draw_element = False

                # When a collision occurs, note direction and distance.
                if collision:
                    # Determine course of action to fix it.
                    # First, get midpoints.
                    existing_midpoint_x = ((existing_obj_top_right_x - existing_obj_bottom_left_x) / 2.0) + existing_obj_bottom_left_x
                    existing_midpoint_y = ((existing_obj_top_right_y - existing_obj_bottom_left_y) / 2.0) + existing_obj_bottom_left_y
                    comp_midpoint_x = ((top_right_x - bottom_left_x) / 2.0) + bottom_left_x
                    comp_midpoint_y = ((top_right_y - bottom_left_y) / 2.0) + bottom_left_y
                    # Compare midpoints. Positive means object is below/left.
                    # TODO: account for equal differently?
                    # New object is up or down. Register both direction and distance.
                    # Distance is the OVERLAP amount.
                    if existing_midpoint_y >= comp_midpoint_y:
                        direction_y = "DOWN"
                        distance_y = top_right_y - existing_obj_bottom_left_y
                    else:
                        direction_y = "UP"
                        distance_y = existing_obj_top_right_y - bottom_left_y
                    # New ojbect is left or right. Register both direction and distance.
                    if existing_midpoint_x > comp_midpoint_x:
                        direction_x = "LEFT"
                        distance_x = top_right_x - existing_obj_bottom_left_x
                    else:
                        direction_x = "RIGHT"
                        distance_x = existing_obj_top_right_x - bottom_left_x

                    # Make decision about which direction to move.
                    # Move element using the lesser of the two distances.
                    if distance_x < distance_y:
                        master_distance = distance_x
                        master_direction = direction_x
                    else:
                        master_distance = distance_y
                        master_direction = direction_y

                    """
                    This code determines the course of action to take
                    in terms of adjusting the object so that it no longer
                    collides. This should act as the sole decision-making
                    code, and allow adjust_for_collision to purely make
                    the adjustment
                    """
                    for move in element.move_options:
                        direction = None
                        distance = None
                        if move == "move":
                            moved = False
                            # Chooese lesser distance...
                            if master_direction not in element.attempted_moves:
                                direction = master_direction
                                distance = master_distance
                            # ...unless x or y is fixed.
                            if fix_y and direction_x not in element.attempted_moves:
                                direction = direction_x
                                distance = distance_x
                                moved = True
                            if fix_x and direction_y not in element.attempted_moves:
                                direction = direction_y
                                distance = distance_y
                                moved = True
                            if not moved and "scale" in element.move_options:
                                # scale
                                pass
                        elif move == "scale":
                            direction = "SCALE_" + master_direction
                            distance = master_distance
                        element.attempted_moves.append(direction)
                        if self.DEBUG:
                            print((element.attempted_moves))

                    # End at first collision detection.
                    object = obj.name

                status = {
                    "collision": collision,
                    "test_object": element.name,
                    "existing_object": object,
                    "direction": direction,
                    "distance": distance,
                }

                if collision:
                    # Return on first collision.
                    if self.DEBUG:
                        print(("@>>>", status))
                    return status
                    # Adjust for any collisions detected.
                    # adjustments = self.__adjust_for_collision(element, status)
                    # print adjustments

    def __adjust_for_collision(self, element, status):
        """Perform adjustments on element for collision."""
        draw_x = element.bottom_left_x
        draw_y = element.bottom_left_y
        direction = status["direction"]
        distance = status["distance"]

        padding = element.padding

        scaling = None
        # Move if allowed to move in the x direction.
        if direction == "RIGHT":
            draw_x += distance + padding
        elif direction == "LEFT":
            draw_x -= distance + padding
        # Move if allowed to move in the y direction.
        elif direction == "UP":
            draw_y += distance + padding
        elif direction == "DOWN":
            draw_y -= distance + padding
        # If XY is fixed, try to scale element.
        elif direction == "SCALE_DOWN":
            scaling = (element.height - padding - distance) / element.height
        elif direction == "SCALE_LEFT":
            scaling = (element.width - padding - distance) / element.width
        # If the object needs to move right or up, but is told it can only
        # do so by scaling, it MUST move in order to stop colliding.
        elif direction == "SCALE_RIGHT":
            draw_x += distance + padding
            scaling = (element.width - padding - distance) / element.width
        elif direction == "SCALE_UP":
            draw_y += distance + padding
            scaling = (element.height - padding - distance) / element.height

        # Apply adjustments to the starting X/Y coordinates.
        element.bottom_left_x = draw_x
        element.bottom_left_y = draw_y

        # Set scaling from adjustment calculations.
        if scaling:
            overall_scale_factor = (scaling * element.height) / element.initial_height
            if overall_scale_factor < element.min_scale:
                element.draw_element = False
                if self.DEBUG:
                    print(
                        (
                            "@>>>WARNING: Scaling exceeded:",
                            overall_scale_factor,
                            "will not place element!",
                        )
                    )
            else:
                orig_width = element.width
                if self.DEBUG:
                    print(("@>>>Scaling:", str(scaling)))
                element.drawing.scale(scaling, scaling)
                element.height *= scaling
                element.width *= scaling
                # If an object scales and it is aligned right,
                # This will adjust the start X point so that it will still
                # be aligned to the right.
                if element.alignment == "right":
                    # Apply adjustments to the starting X/Y coordinates.
                    element.bottom_left_x += orig_width - element.width

        adjustments = {
            "draw_x": draw_x,
            "draw_y": draw_y,
            "scaling": scaling,
        }

        return adjustments

    # this is a draw element functions that we can call from any child classes that will call the parent one
    # We cannot hit the protected parent function from the children so we use this wrapper instead
    def draw_element(self, canvas, element, rotated):
        self.__draw_element(self.canvas, element, rotated)
        # After collision adjustments, register the object.
        self.element_list.append(element)

    def place_element(
        self,
        element,
        draw=True,
        rotated=False,
        ignore_margins=False,
        can_delete=False,
        SHOW_OBJECT_BOUNDS=False,
        **kwargs,
    ):
        """
        Registers an element in element_list, which is our basis for
        collision detection.
        """
        # For align-right and rotated objects, adjust the bottom_x or bottom_y
        # coordinates. The location that reportlab needs to actually DRAW
        # the object is handled in __draw_element.
        if self.DEBUG:
            SHOW_OBJECT_BOUNDS = True
        if self.DEBUG:
            print(("PLACING ELEMENT:", element.name))
        if element.alignment == "right":
            element.bottom_left_x -= element.width

        if rotated:
            element.bottom_left_x -= element.width
            element.bottom_left_y -= element.height

        # Store initial dimensions to allow checking for min_scale.
        element.initial_height = element.height
        element.initial_width = element.width

        # Set number of times to try to correct the element before
        # giving up and not drawing it.
        adjustments = None
        max_iterations = 4
        for iter in range(0, max_iterations):
            # Collision Detection here.
            collision_check = self.__detect_collisions(element, ignore_margins, **kwargs)

            # Adjust for collisions if there are any.
            if collision_check:
                if iter + 1 == max_iterations:
                    if self.DEBUG:
                        print(
                            (
                                "@>>>MAX ATTEMPTS REACHED: CANNOT ADJUST! ELEMENT WILL NOT BE DRAWN:",
                                element.name,
                            )
                        )
                    element.draw_element = False
                    break
                else:
                    # return the adjustments for later use in scaling groups of elements to the smallest
                    adjustments = self.__adjust_for_collision(element, collision_check)
                    # The element wont be drawn anyway so keep going to make sure we get all adjustments
                    # Stop here if the element is no longer to be drawn.
                    # if not element.draw_element:
                    #    break
                    # else:
                    #    if self.DEBUG:
                    #        print "ADJ. #:", iter + 1, adjustments
            else:
                break

        # Check to see if the element, after adjustments, is smaller
        # than allowed. If so, disable drawing.
        if (element.min_y_dim and element.height < element.min_y_dim) or (element.min_x_dim and element.width < element.min_x_dim):
            if can_delete:
                element.draw_element = False
                if self.DEBUG:
                    print(
                        (
                            "@>>>WARNING: Element is too small. Removing.(min_y, h, min_x, w)",
                            element.min_y_dim,
                            element.height,
                            element.min_x_dim,
                            element.width,
                        )
                    )
            else:
                if self.DEBUG:
                    print("@>>>WARNING: Element too small, set to not delete, placing anyway.")
        # Handle margins separetly from other objects.
        if element.name.lower().startswith("margin"):
            # After collision adjustments, register the object.
            self.element_list.append(element)
            # Debugging -- draw element bounds.
            if SHOW_OBJECT_BOUNDS:
                self.draw_object_bounds(element)
        else:
            # Draw element onto the canvas.
            if element.draw_element:
                self.__draw_element(self.canvas, element, rotated)
                # After collision adjustments, register the object.
                self.element_list.append(element)
                # Debugging -- draw element bounds.
                if SHOW_OBJECT_BOUNDS:
                    self.draw_object_bounds(element)
            else:
                if self.DEBUG:
                    print("NOT DRAWING ELEMENT.")
                if element.critical_element and self.DEBUG:
                    print("AHHHH! CRITICAL!!!")
        if self.DEBUG:
            print("@==============================================@")
        return adjustments

    def __register_margins(self):
        """Registers the margins as collidable objects."""
        # Left vertical
        left_vertical = MarginElement(
            "MarginLeft",
            0,
            0,
            self.MARGIN_WIDTH,
            (self.box_height - self.heightMod) + (self.FLAP_HEIGHT * 2),
        )
        self.place_element(left_vertical, draw=False, ignore_margins=True)

        # Bottom Horiz.
        bottom_horizontal = MarginElement(
            "MarginBottom",
            0,
            0,
            (self.A_PANEL_SIDE + self.B_PANEL_SIDE + self.C_PANEL_SIDE + self.D_PANEL_SIDE),
            self.MARGIN_WIDTH,
        )
        self.place_element(bottom_horizontal, draw=False, ignore_margins=True)

        # Top Horiz.
        top_horizontal = MarginElement(
            "MarginTop",
            0,
            (self.box_height - self.heightMod) + (self.FLAP_HEIGHT * 2) - self.MARGIN_WIDTH,
            (self.A_PANEL_SIDE + self.B_PANEL_SIDE + self.C_PANEL_SIDE + self.D_PANEL_SIDE),
            self.MARGIN_WIDTH,
        )
        self.place_element(top_horizontal, draw=False, ignore_margins=True)

        # Right Vert
        right_vertical = MarginElement(
            "MarginRight",
            (self.A_PANEL_SIDE + self.B_PANEL_SIDE + self.C_PANEL_SIDE + self.D_PANEL_SIDE - self.MARGIN_WIDTH),
            0,
            self.MARGIN_WIDTH,
            (self.box_height - self.heightMod) + (self.FLAP_HEIGHT * 2),
        )
        self.place_element(right_vertical, draw=False, ignore_margins=True)

        # Bottom Flap/Main Panel Horiz
        bottom_flap = MarginElement(
            "MarginBottomFormed",
            0,
            self.Y_PANEL_A - self.MARGIN_WIDTH,
            (self.A_PANEL_SIDE + self.B_PANEL_SIDE + self.C_PANEL_SIDE + self.D_PANEL_SIDE),
            2.0 * self.MARGIN_WIDTH,
        )
        self.place_element(bottom_flap, draw=False, ignore_margins=True)

        # Top Flap/Main Panel Horiz
        top_flap = MarginElement(
            "MarginTopFormed",
            0,
            self.Y_PANEL_A + (self.box_height - self.heightMod) - self.MARGIN_WIDTH,
            (self.A_PANEL_SIDE + self.B_PANEL_SIDE + self.C_PANEL_SIDE + self.D_PANEL_SIDE),
            2.0 * self.MARGIN_WIDTH,
        )
        self.place_element(top_flap, draw=False, ignore_margins=True)

        # A/B Vert.
        a_b_vert = MarginElement(
            "MarginABFold",
            self.X_PANEL_B - self.MARGIN_WIDTH,
            0,
            2.0 * self.MARGIN_WIDTH,
            (self.FLAP_HEIGHT * 2) + (self.box_height - self.heightMod),
        )
        self.place_element(a_b_vert, draw=False, ignore_margins=True)

        # B/C Vert.
        b_c_vert = MarginElement(
            "MarginBCFold",
            self.X_PANEL_C - self.MARGIN_WIDTH,
            0,
            2.0 * self.MARGIN_WIDTH,
            (self.FLAP_HEIGHT * 2) + (self.box_height - self.heightMod),
        )
        self.place_element(b_c_vert, draw=False, ignore_margins=True)

        # C/D Vert.
        c_d_vert = MarginElement(
            "MarginCDFold",
            self.X_PANEL_D - self.MARGIN_WIDTH,
            0,
            2.0 * self.MARGIN_WIDTH,
            (self.FLAP_HEIGHT * 2) + (self.box_height - self.heightMod),
        )
        self.place_element(c_d_vert, draw=False, ignore_margins=True)

    def __draw_box_panel_outlines(self):
        """Draws each of the box panels' outlines."""
        # move over the whole image to make room for the
        # For convenience.
        c = self.canvas
        # Sets the color of the panel outlines.
        c.setStrokeColorCMYK(100, 0, 0, 0)

        # Sets the width of the stroke
        c.setLineWidth(2)

        # Main face of box: Panel A with flaps
        c.rect(
            self.X_PANEL_A * inch,
            self.Y_PANEL_A * inch,
            self.A_PANEL_SIDE * inch,
            (self.box_height - self.heightMod) * inch,
            stroke=1,
            fill=0,
        )
        c.rect(
            self.X_PANEL_A * inch,
            0,
            self.A_PANEL_SIDE * inch,
            self.FLAP_HEIGHT * inch,
            stroke=1,
            fill=0,
        )
        c.rect(
            self.X_PANEL_A * inch,
            (self.Y_PANEL_A + (self.box_height - self.heightMod)) * inch,
            self.A_PANEL_SIDE * inch,
            self.FLAP_HEIGHT * inch,
            stroke=1,
            fill=0,
        )

        # Panel B with flaps
        c.rect(
            self.X_PANEL_B * inch,
            self.Y_PANEL_A * inch,
            self.B_PANEL_SIDE * inch,
            (self.box_height - self.heightMod) * inch,
            stroke=1,
            fill=0,
        )
        c.rect(
            self.X_PANEL_B * inch,
            0,
            self.B_PANEL_SIDE * inch,
            self.FLAP_HEIGHT * inch,
            stroke=1,
            fill=0,
        )
        c.rect(
            self.X_PANEL_B * inch,
            (self.Y_PANEL_A + (self.box_height - self.heightMod)) * inch,
            self.B_PANEL_SIDE * inch,
            self.FLAP_HEIGHT * inch,
            stroke=1,
            fill=0,
        )

        # Flap on the right.
        if self.box_shift_right > 0:
            # Box flap top slant.
            self.__draw_dimension_line(
                "left",
                self.X_PANEL_D + self.D_PANEL_SIDE,
                self.FLAP_HEIGHT,
                self.X_PANEL_D + self.D_PANEL_SIDE + self.side_flap_offset,
                self.FLAP_HEIGHT + 1,
                [1, 0, 0, 0],
                False,
                False,
                0,
            )
            # Box flap bottom slant.
            self.__draw_dimension_line(
                "left",
                self.X_PANEL_D + self.D_PANEL_SIDE,
                self.FLAP_HEIGHT + (self.box_height - self.heightMod),
                self.X_PANEL_D + self.D_PANEL_SIDE + self.side_flap_offset,
                self.FLAP_HEIGHT + (self.box_height - self.heightMod) - 1,
                [1, 0, 0, 0],
                False,
                False,
                0,
            )
            # Box flap height.
            self.__draw_dimension_line(
                "left",
                self.X_PANEL_D + self.D_PANEL_SIDE + self.side_flap_offset,
                self.FLAP_HEIGHT + 1,
                self.X_PANEL_D + self.D_PANEL_SIDE + self.side_flap_offset,
                self.FLAP_HEIGHT + (self.box_height - self.heightMod) - 1,
                [1, 0, 0, 0],
                False,
                False,
                0,
            )
        # Flap on the left.
        else:
            # Box flap top slant.
            self.__draw_dimension_line(
                "left",
                self.X_PANEL_A,
                self.FLAP_HEIGHT,
                self.X_PANEL_A - self.side_flap_offset,
                self.FLAP_HEIGHT + 1,
                [1, 0, 0, 0],
                False,
                False,
                0,
            )
            # Box flap bottom slant.
            self.__draw_dimension_line(
                "left",
                self.X_PANEL_A,
                self.FLAP_HEIGHT + (self.box_height - self.heightMod),
                self.X_PANEL_A - self.side_flap_offset,
                self.FLAP_HEIGHT + (self.box_height - self.heightMod) - 1,
                [1, 0, 0, 0],
                False,
                False,
                0,
            )
            # Box flap height.
            self.__draw_dimension_line(
                "left",
                self.X_PANEL_A - self.side_flap_offset,
                self.FLAP_HEIGHT + 1,
                self.X_PANEL_A - self.side_flap_offset,
                self.FLAP_HEIGHT + (self.box_height - self.heightMod) - 1,
                [1, 0, 0, 0],
                False,
                False,
                0,
            )

        # Panel C with flaps
        c.rect(
            self.X_PANEL_C * inch,
            self.Y_PANEL_A * inch,
            self.C_PANEL_SIDE * inch,
            (self.box_height - self.heightMod) * inch,
            stroke=1,
            fill=0,
        )
        c.rect(
            self.X_PANEL_C * inch,
            0,
            self.C_PANEL_SIDE * inch,
            self.FLAP_HEIGHT * inch,
            stroke=1,
            fill=0,
        )
        c.rect(
            self.X_PANEL_C * inch,
            (self.Y_PANEL_A + (self.box_height - self.heightMod)) * inch,
            self.C_PANEL_SIDE * inch,
            self.FLAP_HEIGHT * inch,
            stroke=1,
            fill=0,
        )

        # Panel D with flaps
        c.rect(
            self.X_PANEL_D * inch,
            self.Y_PANEL_A * inch,
            self.D_PANEL_SIDE * inch,
            (self.box_height - self.heightMod) * inch,
            stroke=1,
            fill=0,
        )
        c.rect(
            self.X_PANEL_D * inch,
            0,
            self.D_PANEL_SIDE * inch,
            self.FLAP_HEIGHT * inch,
            stroke=1,
            fill=0,
        )
        c.rect(
            self.X_PANEL_D * inch,
            (self.Y_PANEL_A + (self.box_height - self.heightMod)) * inch,
            self.D_PANEL_SIDE * inch,
            self.FLAP_HEIGHT * inch,
            stroke=1,
            fill=0,
        )

    def __set_panel_origin_variables(self):
        """
        Sets the 'origin point' variables for each panel on the box. These
        are easily referenced when placing elements in relation to the
        corner of each panel.
        """
        # The first panel starts at the origin, which is X = 0.0 + a flap offset if it is kenton(1.5)
        # or another plant (0).
        self.X_PANEL_A = 0.0
        # All panels will share this Y coordinate.
        self.Y_PANEL_A = self.FLAP_HEIGHT

        self.X_PANEL_B = self.X_PANEL_A + self.A_PANEL_SIDE
        self.X_PANEL_C = self.X_PANEL_A + self.A_PANEL_SIDE + self.B_PANEL_SIDE
        self.X_PANEL_D = self.X_PANEL_A + self.A_PANEL_SIDE + self.B_PANEL_SIDE + self.C_PANEL_SIDE

    def __determine_long_and_short_sides(self, width, height, length):
        """
        Most boxes are not geometrical 'boxes' in a sense that there are
        typically differences in the length of each pair of panels. This
        function determines what the shorter and longer dimensions for
        the panel, as it is laid out in a 2D board.

        Also, boxes can be left and right handed. This determines whether
        the short or the long panel is the first panel drawn in order from
        left to right on the 2D cutout board.

        UPDATE: The whole long side/short side concept is a hold over from
        before we started using the CAD dimensions. Under CAD dimensions the
        width will always be the short side. At some point we might go through
        and replace all references to SHORT_SIDE with width. For now we'll
        just make SHORT_SIDE equal width across the board since SHORT_SIDE gets
        referenced so much.
        """
        boxModA = 0.125
        boxModB = 0.1875
        boxModC = 0.1875
        boxModD = 0.125
        if self.plant == "Pittston":
            boxModA = 0.1875
            boxModB = 0.1875
            boxModC = 0.1875
            boxModD = 0.0625
        if self.plant == "Clarksville":
            boxModA = 0.125
            boxModB = 0.1875
            boxModC = 0.1875
            boxModD = 0.0625
        if self.plant == "Shelbyville":
            boxModA = 0.125
            boxModB = 0.1875
            boxModC = 0.1875
            boxModD = 0.0

        self.SHORT_SIDE = width
        if self.box_format.lower() == "left":
            self.A_PANEL_SIDE = (length - 0.375) + boxModA
            self.B_PANEL_SIDE = (width - 0.375) + boxModB
            self.C_PANEL_SIDE = (length - 0.375) + boxModC
            self.D_PANEL_SIDE = (width - 0.375) + boxModD
        else:
            self.A_PANEL_SIDE = (width - 0.375) + boxModA
            self.B_PANEL_SIDE = (length - 0.375) + boxModB
            self.C_PANEL_SIDE = (width - 0.375) + boxModC
            self.D_PANEL_SIDE = (length - 0.375) + boxModD

        if self.plant == "Shelbyville":
            if self.box_format.lower() == "left":
                self.A_PANEL_SIDE = (length - 0.3125) + boxModA
                self.B_PANEL_SIDE = (width - 0.3125) + boxModB
                self.C_PANEL_SIDE = (length - 0.3125) + boxModC
                self.D_PANEL_SIDE = (width - 0.3125) + boxModD
            else:
                self.A_PANEL_SIDE = (width - 0.3125) + boxModA
                self.B_PANEL_SIDE = (length - 0.3125) + boxModB
                self.C_PANEL_SIDE = (width - 0.3125) + boxModC
                self.D_PANEL_SIDE = (length - 0.3125) + boxModD

        """
        Figure out the top flap and bottom flap heights. Normally the flap
        height would just be half of the width/short side. However, because the
        equipment used to manufacture corrugated works in 1/16th increments we
        have to make sure that half the width won't result in 32nds of an inch.
        For example, a width of 10 and 2/16ths is fine because it splits to 5
        and 1/16th. However, 10 and 3/16ths is a problem because it splits to 5
        and 5 and 3/32nds. Is such cases we should reduce the width by 1/16th
        before we split it to derive the flap height. This solution is what
        plate-making uses.
        """
        # Get the inner dimension for the width.
        if self.plant == "Shelbyville":
            inner_width = width - 0.3125
        else:
            inner_width = width - 0.375
        # If the width isn't a whole number we need to check the fraction.
        if not float(inner_width).is_integer():  #
            # Find out if the numerator in 16ths.
            decimal = inner_width - int(inner_width)
            numerator = decimal * 16
            # If the numerator (in 16ths) is odd:
            if numerator % 2 != 0:
                # Increase the width by 1/16th before you split it to get the
                # flap height.
                flap_height = (inner_width + 0.0625) / 2
                if self.plant == "Shelbyville":
                    flap_height -= 0.0625
            else:
                # If the numerator is already even we need to divide it by two
                # and then add 1/16th for seam allowence.
                if self.plant == "Shelbyville":
                    flap_height = inner_width / 2
                else:
                    flap_height = (inner_width / 2) + 0.0625
        else:
            flap_height = inner_width / 2
        self.FLAP_HEIGHT = flap_height

    def __draw_dimension_line(
        self,
        orientation,
        x1,
        y1,
        x2,
        y2,
        cmykArr,
        dimensionType,
        altDimensionColor=False,
        tick_length=0.75,
    ):
        """
        Very generic dimension line drawer.
        Orientation (text): Left, right, top, bottom. Side on which the dimension
                            line should be drawn in relation to the object.
        x1 (int): X1 coordinate of line to dimension.
        y1 (int): Y1 coordinate of line to dimension.
        x2 (int): X2 coordinate of line to dimension.
        y2 (int): Y2 coordinate of line to dimension.
        cmykArr: Stroke color (in CMYK) for the dimension lines.
        dimensionType (text): Draw the dimension number on the dimension line if
                            a type is provided. Choices are 'Decimal' and
                            'Decimal_and_Fraction' for now. Passing False won't
                            draw the dimension number.
        altDimensionColor (bool): If true, draws the dimension number in the
                                alt color for contrast.
        tick_length (int): Length of tick marks for the dimension line.
        """
        c = self.canvas
        # Set stroke color for dimension lines.
        c.setStrokeColorCMYK(cmykArr[0], cmykArr[1], cmykArr[2], cmykArr[3])

        # Set offset of the dimension line.
        dim_line_offset = tick_length / 2.0

        if orientation == "left":
            draw_x1 = x1 - dim_line_offset
            draw_y1 = y1
            draw_x2 = x2 - dim_line_offset
            draw_y2 = y2
        elif orientation == "right":
            draw_x1 = x1 + dim_line_offset
            draw_y1 = y1
            draw_x2 = x2 + dim_line_offset
            draw_y2 = y2
        elif orientation == "top":
            draw_x1 = x1
            draw_y1 = y1 + dim_line_offset
            draw_x2 = x2
            draw_y2 = y2 + dim_line_offset
        elif orientation == "bottom":
            draw_x1 = x1
            draw_y1 = y1 - dim_line_offset
            draw_x2 = x2
            draw_y2 = y2 - dim_line_offset

        # Calculate dimension.
        if orientation in ("left", "right"):
            # Vertical line, subtract Y values.
            dim_number = y2 - y1
        else:
            # Horizontal line, subtract X values.
            dim_number = x2 - x1

        # Draw dimension line.
        c.line(draw_x1 * inch, draw_y1 * inch, draw_x2 * inch, draw_y2 * inch)

        # Draw ticks and arrows.
        # Use this to get the arrows to be at a slight angle.
        angle_offset = dim_line_offset / 1.5
        if orientation in ("left", "right"):
            # Ticks.
            c.line(
                (draw_x1 - dim_line_offset) * inch,
                draw_y1 * inch,
                (draw_x1 + dim_line_offset) * inch,
                draw_y1 * inch,
            )
            c.line(
                (draw_x2 - dim_line_offset) * inch,
                draw_y2 * inch,
                (draw_x2 + dim_line_offset) * inch,
                draw_y2 * inch,
            )
            # Arrows
            # Bottom
            c.line(
                draw_x1 * inch,
                draw_y1 * inch,
                (draw_x1 + angle_offset) * inch,
                (draw_y1 + dim_line_offset) * inch,
            )
            c.line(
                draw_x1 * inch,
                draw_y1 * inch,
                (draw_x1 - angle_offset) * inch,
                (draw_y1 + dim_line_offset) * inch,
            )
            # Top
            c.line(
                draw_x2 * inch,
                draw_y2 * inch,
                (draw_x2 - angle_offset) * inch,
                (draw_y2 - dim_line_offset) * inch,
            )
            c.line(
                draw_x2 * inch,
                draw_y2 * inch,
                (draw_x2 + angle_offset) * inch,
                (draw_y2 - dim_line_offset) * inch,
            )
        else:
            # Ticks.
            c.line(
                draw_x1 * inch,
                (draw_y1 - dim_line_offset) * inch,
                draw_x1 * inch,
                (draw_y1 + dim_line_offset) * inch,
            )
            c.line(
                draw_x2 * inch,
                (draw_y2 - dim_line_offset) * inch,
                draw_x2 * inch,
                (draw_y2 + dim_line_offset) * inch,
            )
            # Arrows
            # Left
            c.line(
                draw_x1 * inch,
                draw_y1 * inch,
                (draw_x1 + dim_line_offset) * inch,
                (draw_y1 + angle_offset) * inch,
            )
            c.line(
                draw_x1 * inch,
                draw_y1 * inch,
                (draw_x1 + dim_line_offset) * inch,
                (draw_y1 - angle_offset) * inch,
            )
            # Right
            c.line(
                draw_x2 * inch,
                draw_y2 * inch,
                (draw_x2 - dim_line_offset) * inch,
                (draw_y2 + angle_offset) * inch,
            )
            c.line(
                draw_x2 * inch,
                draw_y2 * inch,
                (draw_x2 - dim_line_offset) * inch,
                (draw_y2 - angle_offset) * inch,
            )

        if not dimensionType:  # Instructed to not draw the dimension number. Bail out.
            return

        # Dimension number as a string. For display.
        dim_number_str = str(dim_number)
        # Dimension number as a fraction string. For display.
        dim_frac = Fraction(dim_number)
        numer = dim_frac.numerator
        denom = dim_frac.denominator
        if (numer % denom) == 0:
            # Dimension number is a whole number. No fraction to display.
            dim_frac_str = None
        else:
            dim_frac_str = str("%d %d/%d" % (numer // denom, numer % denom, denom))

        # Display the dimention number as instructed.
        if dimensionType == "Fraction":
            if dim_frac_str:
                dim_number_str = dim_frac_str
        elif dimensionType == "Decimal_and_Fraction":
            if dim_frac_str:
                dim_number_str += " (" + dim_frac_str + ")"

        # Draw dimension number.
        font_size = 48
        c.setFont("Helvetica", font_size)

        # Use this to offset the text slightly to accommodate it's size and center it.
        text_height_offest = (font_size / 100.0) / 2.0
        text_width_offset = check_text_width(font_size, "Helvetica", dim_number_str)

        text_width_offset = text_width_offset / 2.0

        if altDimensionColor:
            c.setFillColorCMYK(0, 0.60, 0.55, 0)
        else:
            c.setFillColorCMYK(0.65, 0.60, 0.55, 0)

        if orientation in ("left", "right"):
            c.rotate(90)
            mid_draw_y = dim_number / 2.0
            prerotated_x = draw_x1
            prerotated_y = draw_y1 + mid_draw_y - text_width_offset
            rotated_x = prerotated_y
            rotated_y = -prerotated_x
            c.drawString(rotated_x * inch, rotated_y * inch, dim_number_str)
            c.rotate(-90)
        else:
            # Top/Bottom (works best for bottom right now)
            mid_draw_x = dim_number / 2.0
            c.drawString(
                (draw_x1 + mid_draw_x - text_width_offset) * inch,
                (draw_y1 - 2.0 * text_height_offest) * inch,
                dim_number_str,
            )

    def __draw_box_dimension_lines(self):
        """
        Dimension lines around box. Need to show width of each panel, and height
        of box and top panels.
        """
        CMYKArr = [0.5, 0, 0.5, 0]

        # Panel A width.
        self.__draw_dimension_line("bottom", self.X_PANEL_A, 0.0, self.X_PANEL_B, 0.0, CMYKArr, "Decimal")
        # Panel B width.
        self.__draw_dimension_line(
            "bottom",
            self.X_PANEL_B,
            0.0,
            self.X_PANEL_C,
            0.0,
            CMYKArr,
            "Decimal_and_Fraction",
        )
        # Panel A and B width combined.
        self.__draw_dimension_line(
            "bottom",
            self.X_PANEL_A,
            -0.75,
            self.X_PANEL_C,
            -0.75,
            CMYKArr,
            "Decimal_and_Fraction",
            True,
        )
        # Panel C width.
        self.__draw_dimension_line(
            "bottom",
            self.X_PANEL_C,
            0.0,
            self.X_PANEL_D,
            0.0,
            CMYKArr,
            "Decimal_and_Fraction",
        )
        # Panel D width.
        self.__draw_dimension_line(
            "bottom",
            self.X_PANEL_D,
            0.0,
            (self.X_PANEL_D + self.D_PANEL_SIDE),
            0.0,
            CMYKArr,
            "Decimal",
        )
        # Panel C and D width combined.
        self.__draw_dimension_line(
            "bottom",
            self.X_PANEL_C,
            -0.75,
            (self.X_PANEL_D + self.D_PANEL_SIDE),
            -0.75,
            CMYKArr,
            "Decimal_and_Fraction",
            True,
        )
        # Total box width.
        self.__draw_dimension_line(
            "bottom",
            self.X_PANEL_A,
            -1.5,
            (self.X_PANEL_D + self.D_PANEL_SIDE),
            -1.5,
            CMYKArr,
            "Decimal",
        )

        # Box panel height.
        self.__draw_dimension_line(
            "left",
            self.X_PANEL_A - self.box_shift_left,
            self.Y_PANEL_A,
            self.X_PANEL_A - self.box_shift_left,
            (self.FLAP_HEIGHT + (self.box_height - self.heightMod)),
            CMYKArr,
            "Decimal",
        )
        # Bottom flap 'height'.
        self.__draw_dimension_line(
            "left",
            self.X_PANEL_A - self.box_shift_left,
            0.0,
            self.X_PANEL_A - self.box_shift_left,
            self.FLAP_HEIGHT,
            CMYKArr,
            "Decimal",
        )
        # Top flap 'height'.
        self.__draw_dimension_line(
            "left",
            self.X_PANEL_A - self.box_shift_left,
            (self.Y_PANEL_A + (self.box_height - self.heightMod)),
            self.X_PANEL_A - self.box_shift_left,
            ((self.FLAP_HEIGHT * 2) + (self.box_height - self.heightMod)),
            CMYKArr,
            "Decimal",
        )
        # Total box height.
        self.__draw_dimension_line(
            "left",
            (self.X_PANEL_A - 0.75 - self.box_shift_left),
            0.0,
            (self.X_PANEL_A - 0.75 - self.box_shift_left),
            ((self.FLAP_HEIGHT * 2) + (self.box_height - self.heightMod)),
            CMYKArr,
            "Decimal",
            True,
        )

        # Bottom flap 'height' right side.
        self.__draw_dimension_line(
            "right",
            (self.X_PANEL_D + self.D_PANEL_SIDE + self.box_shift_right + 0.25),
            0.0,
            (self.X_PANEL_D + self.D_PANEL_SIDE + self.box_shift_right + 0.25),
            self.FLAP_HEIGHT,
            CMYKArr,
            "Decimal",
        )
        # Bottom flap 'height' plus box panel 'height' right side.
        self.__draw_dimension_line(
            "right",
            (self.X_PANEL_D + self.D_PANEL_SIDE + self.box_shift_right + 1.00),
            0.0,
            (self.X_PANEL_D + self.D_PANEL_SIDE + self.box_shift_right + 1.00),
            (self.FLAP_HEIGHT + (self.box_height - self.heightMod)),
            CMYKArr,
            "Decimal",
            True,
        )
        # Total box height right side.
        self.__draw_dimension_line(
            "right",
            (self.X_PANEL_D + self.D_PANEL_SIDE + self.box_shift_right + 1.75),
            0.0,
            (self.X_PANEL_D + self.D_PANEL_SIDE + self.box_shift_right + 1.75),
            ((self.FLAP_HEIGHT * 2) + (self.box_height - self.heightMod)),
            CMYKArr,
            "Decimal",
        )

    def draw_label_dimension_line(self, height):
        """
        Draw a dimension line showing the distance between the bottom of the
        label area and the bottom of the panel. Since that varies by plant we
        need to specify the height each time.
        """
        CMYKArr = [0.5, 0, 0.5, 0]

        self.__draw_dimension_line(
            "left",
            (self.X_PANEL_B - 6),
            self.Y_PANEL_A,
            (self.X_PANEL_B - 6),
            (self.Y_PANEL_A + height),
            CMYKArr,
            "Decimal",
        )

    def draw_object_bounds(self, element):
        """Debugging tool for drawing object bounds on objects."""
        if not element.name.lower().startswith("margin"):
            self.canvas.setStrokeColorCMYK(0.5, 0, 1.0, 0)
        else:
            self.canvas.setStrokeColorCMYK(0, 1.0, 0, 0)
        self.canvas.rect(
            element.bottom_left_x * inch,
            element.bottom_left_y * inch,
            element.width * inch,
            element.height * inch,
            stroke=1,
            fill=0,
        )

    def create_slugs(self):
        """
        Draw all elements as slugs on a page. Sort elements by size, add crop
        marks, etc... Slugging is required for some platemakers in order to
        save on costly plate material. Two elements in close proximity to
        each other should be given identical 'group_id' numbers so that they
        will be grouped into the same slug.
        Slugging will begin with the origin in the bottom left, sort the slugs
        by group, arranging them by width and placing them on the given
        sheet size bottom to top, then creating a new column to the right of
        the previous column.
        """
        # Setup variables for slugging.
        # Beginning cursor coordinates.
        X_CURSOR = 1.0
        X_CURSOR_RETURN = X_CURSOR
        Y_CURSOR = 1.0
        Y_CURSOR_RETURN = Y_CURSOR
        PAGE_BORDER = 1.0
        # Limits of film dimensions,
        SHEET_HEIGHT = 14.0
        SHEET_WIDTH = 48.0

        # self.canvas = Canvas(self.file_name, pagesize=(PAGE_WIDTH_LIMIT * inch, PAGE_HEIGHT_LIMIT * inch))
        self.canvas.setPageSize((SHEET_WIDTH * inch, SHEET_HEIGHT * inch))

        # Set page limits based on sheet size minus border.
        PAGE_HEIGHT_LIMIT = SHEET_HEIGHT - PAGE_BORDER
        PAGE_WIDTH_LIMIT = SHEET_WIDTH - PAGE_BORDER

        # Toggle for first element in column -- used to determine column widths.
        FIRST_ELEMENT_IN_COLUMN = True
        # Length of the center marks for each slug.
        CENTER_MARK_LENGTH = 0.375
        # Distance from the outer bounds of the element for each slug.
        CENTER_MARK_DISTANCE = 0.5
        # Spacing between two slugs.
        SLUG_SPACING = 0.25
        # Length of each part of corner mark.
        CORNER_MARK_LENGTH = 0.375
        # Sum of extra width/height of each slug. Used for spacing purposes.
        EXTRA_DIMENSIONS = 2 * (CENTER_MARK_LENGTH + CENTER_MARK_DISTANCE)
        # Column width -- used to determine where the next column should start
        # drawing.
        COLUMN_WIDTH = 0.0

        # Set up lists to sort elements into groups. Group = Slug
        master_element_groups = []
        elements_with_group_id = []
        elements_without_group_id = []
        group_id_numbers = []
        # Sort elements into 2 separate lists: those with group and those without.
        for element in self.element_list:
            if not element.name.lower().startswith("margin"):
                if element.group_id:
                    elements_with_group_id.append(element)
                    # Make a list of group numbers.
                    if element.group_id not in group_id_numbers:
                        group_id_numbers.append(element.group_id)
                else:
                    elements_without_group_id.append(element)
            else:
                # Margin element, no need for slugs.
                pass

        # Build groups for those with with a group id.
        for group_num in group_id_numbers:
            group = ElementGroup(group_num)
            for elem in elements_with_group_id:
                if elem.group_id == group_num:
                    group.element_list.append(elem)
            group.determine_group_dimensions()
            master_element_groups.append(group)
            if self.DEBUG:
                print(
                    (
                        "Group",
                        group.group_num,
                        ":",
                        group.group_x,
                        group.group_y,
                        group.width,
                        group.height,
                    )
                )

        # Build groups of 1 for all the loner elements.
        for elem in elements_without_group_id:
            group = ElementGroup(None)
            group.element_list.append(elem)
            group.determine_group_dimensions()
            master_element_groups.append(group)
            if self.DEBUG:
                print(
                    (
                        "Group",
                        group.group_num,
                        ":",
                        group.group_x,
                        group.group_y,
                        group.width,
                        group.height,
                    )
                )

        # Sort the groups by width before laying out the slugs.
        sorted_elements = sorted(master_element_groups, key=lambda x: x.width, reverse=True)

        for grp in sorted_elements:
            # Determine slug dimensions with added marks (extra dimensions)
            slug_width = grp.width + EXTRA_DIMENSIONS
            slug_height = grp.height + EXTRA_DIMENSIONS

            # Go ahead and adjust the cursor if the upcoming slug is going
            # to exceed the current column height.
            if (Y_CURSOR + slug_height) > PAGE_HEIGHT_LIMIT:
                X_CURSOR += COLUMN_WIDTH
                Y_CURSOR = Y_CURSOR_RETURN
                FIRST_ELEMENT_IN_COLUMN = True

            # Create a new page if the next column of slugs will exceed the
            # allowable page width.
            if (X_CURSOR + slug_width) > PAGE_WIDTH_LIMIT:
                X_CURSOR = X_CURSOR_RETURN
                Y_CURSOR = Y_CURSOR_RETURN
                FIRST_ELEMENT_IN_COLUMN = True
                self.canvas.showPage()

            for element in grp.element_list:
                # Draw each element in the group's list.
                # Draw element at cursor position.
                element.bottom_left_x = X_CURSOR + element.group_delta_x + EXTRA_DIMENSIONS / 2.0
                element.bottom_left_y = Y_CURSOR + element.group_delta_y + EXTRA_DIMENSIONS / 2.0
                self.__draw_element(self.canvas, element)

            # Draw center and corner marks for each slug.
            self.canvas.setStrokeColorCMYK(0, 0, 0, 1.0)

            # Left center mark.
            self.canvas.line(
                (X_CURSOR) * inch,
                (Y_CURSOR + slug_height / 2.0) * inch,
                (X_CURSOR + CENTER_MARK_LENGTH) * inch,
                (Y_CURSOR + slug_height / 2.0) * inch,
            )
            # Right center mark.
            self.canvas.line(
                (X_CURSOR + slug_width) * inch,
                (Y_CURSOR + slug_height / 2.0) * inch,
                (X_CURSOR + slug_width - CENTER_MARK_LENGTH) * inch,
                (Y_CURSOR + slug_height / 2.0) * inch,
            )
            # Bottom center mark.
            self.canvas.line(
                (X_CURSOR + (slug_width / 2.0)) * inch,
                (Y_CURSOR) * inch,
                (X_CURSOR + (slug_width / 2.0)) * inch,
                (Y_CURSOR + CENTER_MARK_LENGTH) * inch,
            )
            # Top center mark.
            self.canvas.line(
                (X_CURSOR + (slug_width / 2.0)) * inch,
                (Y_CURSOR + slug_height) * inch,
                (X_CURSOR + (slug_width / 2.0)) * inch,
                (Y_CURSOR + slug_height - CENTER_MARK_LENGTH) * inch,
            )

            # Bottom-left corner mark.
            self.canvas.line(
                (X_CURSOR) * inch,
                (Y_CURSOR) * inch,
                (X_CURSOR + CORNER_MARK_LENGTH) * inch,
                (Y_CURSOR) * inch,
            )
            self.canvas.line(
                (X_CURSOR) * inch,
                (Y_CURSOR) * inch,
                (X_CURSOR) * inch,
                (Y_CURSOR + CORNER_MARK_LENGTH) * inch,
            )
            # Top-left corner mark.
            self.canvas.line(
                (X_CURSOR) * inch,
                (Y_CURSOR + slug_height) * inch,
                (X_CURSOR + CORNER_MARK_LENGTH) * inch,
                (Y_CURSOR + slug_height) * inch,
            )
            self.canvas.line(
                (X_CURSOR) * inch,
                (Y_CURSOR + slug_height) * inch,
                (X_CURSOR) * inch,
                (Y_CURSOR + slug_height - CORNER_MARK_LENGTH) * inch,
            )
            # Bottom-right corner mark.
            self.canvas.line(
                (X_CURSOR + slug_width) * inch,
                (Y_CURSOR) * inch,
                (X_CURSOR + slug_width - CORNER_MARK_LENGTH) * inch,
                (Y_CURSOR) * inch,
            )
            self.canvas.line(
                (X_CURSOR + slug_width) * inch,
                (Y_CURSOR) * inch,
                (X_CURSOR + slug_width) * inch,
                (Y_CURSOR + CORNER_MARK_LENGTH) * inch,
            )
            # Top-right corner mark.
            self.canvas.line(
                (X_CURSOR + slug_width) * inch,
                (Y_CURSOR + slug_height) * inch,
                (X_CURSOR + slug_width - CORNER_MARK_LENGTH) * inch,
                (Y_CURSOR + slug_height) * inch,
            )
            self.canvas.line(
                (X_CURSOR + slug_width) * inch,
                (Y_CURSOR + slug_height) * inch,
                (X_CURSOR + slug_width) * inch,
                (Y_CURSOR + slug_height - CORNER_MARK_LENGTH) * inch,
            )

            """
            If this is the first element in the column (and therefore the
            widest), set up the column_width variable for changing the
            x_cursor once the column is full.
            """
            if FIRST_ELEMENT_IN_COLUMN:
                COLUMN_WIDTH = slug_width + SLUG_SPACING
                FIRST_ELEMENT_IN_COLUMN = False
            Y_CURSOR += slug_height + SLUG_SPACING
            # Once page height limit is reached, setup the next column.
            if Y_CURSOR > PAGE_HEIGHT_LIMIT:
                X_CURSOR += COLUMN_WIDTH
                Y_CURSOR = Y_CURSOR_RETURN
                FIRST_ELEMENT_IN_COLUMN = True

    def save_to_pdf(self):
        """Saves the box to a PDF file."""
        self.canvas.save()


class GenericLabel(GenericCanvas):
    def __init__(self, file_name):
        """
        Handles drawing the canvas and preparing other storage variables.

        file_name: (str) Path to the eventual finished PDF.
        """
        self.DEBUG = False

        # Calculate the actual reportlab Canvas size.
        self.canvas_width = 13.0
        self.canvas_height = 5.125

        # Call the __init__ method from the GenericCanvas parent class.
        super(GenericLabel, self).__init__(file_name, self.canvas_width, self.canvas_height)
        # Moves the origin out of the bleed to the beginning of the art board.
        self.canvas.translate(0.5 * inch, 0.5 * inch)

    def place_element(self, element):
        """
        Simplified place element method. No collision detection needed like
        the box element needs.
        """
        renderPDF.draw(element.drawing, self.canvas, 0.0, 0.0)

    def save_to_pdf(self):
        """Saves the label to a PDF file."""
        self.canvas.save()
