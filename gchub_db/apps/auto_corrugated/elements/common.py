"""Common elements that may be useful for other generators."""

from includes.reportlib.elements.collidables import CollidableElement


class MarginElement(CollidableElement):
    """Represents a margin for the panels. This is typically not drawn."""

    def __init__(self, name, bottom_left_x, bottom_left_y, width, height):
        super(MarginElement, self).__init__(name, bottom_left_x, bottom_left_y, width, height, draw_element=False)
