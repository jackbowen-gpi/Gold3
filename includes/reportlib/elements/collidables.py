"""
Generic objects that may be placed on a canvas, with collision detection
support.
"""

from includes.reportlib.elements.generic import (
    GenericElement,
    SVGGraphicElement,
    TextElement,
)


class CollidableElement(GenericElement):
    def __init__(self, name, bottom_left_x, bottom_left_y, width, height, **kwargs):
        """
        Instantiates a collidable element. Make sure to call this __init__
        method from sub-classes.

        draw_element: (bool) Toggle to draw object to canvas.
        name: (str) Description name of the object.
        bottom_left_x: (float) X coordinate for object's bottom left point.
        bottom_left_y: (float) Y coordinate for object's bottom left point.
        width: (float) Width of element (in inches).
        height: (float) Height of element (in inches).
        alignment: (str) Alignment of the element.
        text_align: (str) Aligntment of text in an object (start or end).
        padding: (float) Padding around the element (in inches).
        can_move_x: (bool) Can adjust element along X axis.
        can_move_y: (bool) Can adjust element along Y axis.
        can_scale: (bool) Can adjust element scaling to fit.
        min_scale: (float) Minimum allowable scaling on object before it's too small.
        max_move: (float) Maximum allowable distance an object can move.
        min_x_dim: (float) Min. horiz. dimension before object is too small.
        min_y_dim: (float) Min. vert. dimension before object is too small.
        move_options: (dict) Prioritized options for collision correction.
        attempted_moves: (dict) Moves attempted for collision correction.
        critical_element: (bool) Determines if failure to place element
            results in failure of box creation.
        group_id: (int) ID number given to grouped elements.
        group_delta_x: (float) Difference in bottomleft x of element to it's group.
        group_delta_y: (float) Difference in bottomleft y of element to it's group.
        """
        self.draw_element = kwargs.get("draw_element", True)
        self.name = name
        self.bottom_left_x = bottom_left_x
        self.bottom_left_y = bottom_left_y
        self.width = width
        self.height = height
        self.alignment = kwargs.get("alignment", "left")
        self.text_align = kwargs.get("text_align", "start")
        self.padding = kwargs.get("padding", 0.0)
        self.fix_x = kwargs.get("fix_x", True)
        self.fix_y = kwargs.get("fix_y", True)
        self.can_scale = kwargs.get("can_scale", True)
        self.min_scale = kwargs.get("min_scale", 0.55)
        self.max_move = kwargs.get("max_move", 4.0)
        self.min_x_dim = kwargs.get("min_x_dim", None)
        self.min_y_dim = kwargs.get("min_y_dim", None)
        self.move_options = kwargs.get("move_options", ["move", "scale"])
        self.attempted_moves = kwargs.get("attempted_moves", [])
        self.critical_element = kwargs.get("critical_element", False)
        self.group_id = kwargs.get("group_id", None)
        self.group_delta_x = kwargs.get("group_delta_x", None)
        self.group_delta_y = kwargs.get("group_delta_y", None)


class CollidableTextElement(TextElement, CollidableElement):
    def __init__(
        self,
        name,
        bottom_left_x,
        bottom_left_y,
        label_text,
        font="Helvetica-Bold",
        size=12,
        **kwargs,
    ):
        """
        bottom_left_x: (float) X coordinate for object's bottom left point.
        bottom_left_y: (float) Y coordinate for object's bottom left point.
        label_text: (str) Text to be displayed on the element.
        font: (str) A valid registered font.
        size: (int) Size (in points) for the text.
        """
        # Call the CollidableElement superclass's __init__ method. This sets
        # the coordinate attributes up. Note that we'll set the width and
        # height attributes later, None works for now.
        CollidableElement.__init__(
            self, name, bottom_left_x, bottom_left_y, None, None, **kwargs
        )
        # Call the CollidableTextElement's superclass's __init__ method, which
        # also calculates and sets the width and height attributes, along with
        # a self.drawing attribute.
        TextElement.__init__(
            self, bottom_left_x, bottom_left_y, label_text, font=font, size=size
        )
        # By the end of this, we've got all of the normal attributes, along
        # with self.drawing. This matches up with the other label classes
        # in this module.


class CollidableSVGGraphicElement(SVGGraphicElement, CollidableElement):
    def __init__(
        self,
        name,
        bottom_left_x,
        bottom_left_y,
        file_name,
        available_area_x,
        available_area_y,
        **kwargs,
    ):
        """
        bottom_left_x: (float) X coordinate for object's bottom left point.
        bottom_left_y: (float) Y coordinate for object's bottom left point.
        label_text: (str) Text to be displayed on the element.
        file_name: (str) Path to the SVG file.
        available_area_x: (int) Horiz. area available for graphic placement.
        available_area_Y: (int) Vert. area available for graphic placement.
        """
        CollidableElement.__init__(
            self, name, bottom_left_x, bottom_left_y, None, None, **kwargs
        )

        SVGGraphicElement.__init__(
            self,
            bottom_left_x,
            bottom_left_y,
            file_name,
            available_area_x,
            available_area_y,
        )
