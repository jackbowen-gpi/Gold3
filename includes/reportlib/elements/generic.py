"""A very basic element class to go with reportlib.documents.canvas classes."""

from reportlab.graphics.shapes import Drawing, Group, String
from reportlab.lib.units import inch
from svglib import svglib

from includes.reportlib.util import check_text_width, convert_svg_to_color


class InvalidPath(Exception):
    """Thrown when an invalid or mal-formed path is provided."""

    def __str__(self):
        return "An invalid file path has been provided."


class GenericElement(object):
    pass


class MultiLineTextElement(object):
    """
    This class will correctly set the element's 'width' attribute by looking
    at the longest line of text.
    """

    def __init__(self, lines, font="Helvetica", size=18):
        """Return a drawing obj. and x/y coordinates for given text lines"""
        self.drawing = Drawing()
        self.text_align = "left"  # Default text alignment
        # Used to determine how wide the entire block of text is. This represents
        # the width of the widest line.
        max_width = 0
        # Move cursor up before starting to type.
        inner_y = (size / 72.0) * (len(lines) - 1)
        # Go through each line and figure out how long they are.
        for line in lines:
            self.drawing.add(
                String(
                    0,
                    inner_y * inch,
                    line,
                    fontName=font,
                    fontSize=size,
                    textAnchor=self.text_align,
                    fillColor=(0, 0, 0, 1.0),
                )
            )
            # Calculate the width of the line.
            width = check_text_width(size, font, line)

            # If this is true, this line is the longest yet and therefore
            # becomes the text element's width.
            if width > max_width:
                max_width = width
            # Move the cursor up for the next line (if applicable).
            inner_y -= size / 72.0

        # Calculate these for collidable objects.
        self.width = max_width
        self.height = (size / 72.0) * len(lines)


class TextElement(object):
    """This class represents any single chunk of single line text on the box."""

    def __init__(self, bottom_left_x, bottom_left_y, label_text, font="Helvetica-Bold", size=12):
        """
        bottom_left_x: (float) X coordinate for object's bottom left point.
        bottom_left_y: (float) Y coordinate for object's bottom left point.
        text: (str) Text to be displayed on the element.
        font: (str) A valid registered font.
        size: (int) Size (in points) for the text.
        """
        self.drawing = Drawing()
        # Sometimes numbers are passed, but the only thing we can
        # use is a string.
        text = str(label_text)
        # Calculate width based on the text contents.
        self.width = check_text_width(size, font, text)
        # Calculate the height of this element based on font size.
        self.height = size / 100.0
        # Draw the text, ready for placement.
        self.drawing.add(String(0, 0, text, fontName=font, fontSize=size, fillColor=(0, 0, 0, 1.0)))


class SVGGraphicElement(object):
    """
    This class represents any single imported SVG (Scalable Vector Graphic)
    element.
    """

    def __init__(
        self,
        bottom_left_x,
        bottom_left_y,
        file_name,
        available_area_x,
        available_area_y,
    ):
        """
        bottom_left_x: (float) X coordinate for object's bottom left point.
        bottom_left_y: (float) Y coordinate for object's bottom left point.
        file: (str) File path to import.
        available_area_x: (int) Horiz. area available for graphic placement.
        available_area_Y: (int) Vert. area available for graphic placement.
        """
        self.drawing = Drawing()
        self.bottom_left_x = bottom_left_x
        self.alignment = "left"  # Default alignment
        # Import SVG graphic file.
        print(file_name)
        vector_graphic = svglib.svg2rlg(file_name)
        print(vector_graphic)
        if not vector_graphic:
            raise InvalidPath()

        convert_svg_to_color(vector_graphic)

        # Calculate the width of this element.
        self.width = vector_graphic.getProperties()["width"] / 72.0
        # Calculate the height of this element.
        self.height = vector_graphic.getProperties()["height"] / 72.0

        # Calculate horizontal scaling required to fit available area.
        if available_area_x:
            horiz_scaling = available_area_x / self.width

        # Calculate vertical scaling required to fit available area.
        if available_area_y:
            vert_scaling = available_area_y / self.height

        # Deal with scaling both directions, use the smaller of the two scalings.
        if available_area_x and available_area_y:
            if horiz_scaling < vert_scaling:
                scaling = horiz_scaling
            else:
                scaling = vert_scaling
        # Deal with only horizontal scaling.
        elif available_area_x and not available_area_y:
            scaling = horiz_scaling
        # Deal with only vertical scaling.
        elif available_area_y and not available_area_x:
            scaling = vert_scaling
        # Otherwise, don't scale at all.
        else:
            scaling = 1.0

        # Resave width and height to accomodate scaling.
        self.width *= scaling
        self.height *= scaling

        # If align right, need to move the bottom x bottom to the left
        # the distance of the width.
        # if self.alignment == 'right':
        #    self.bottom_left_x -= self.width

        if self.alignment == "center":
            self.bottom_left_x += (available_area_x / 2.0) - (self.width / 2.0)

        # Place the graphic in a group to perform scaling.
        graphic_group = Group(vector_graphic)
        graphic_group.scale(scaling, scaling)

        # Draw the graphic, ready for placement.
        self.drawing.add(graphic_group)
