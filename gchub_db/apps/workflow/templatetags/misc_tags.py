"""Didn't know where else to put these."""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def pantone_plus_mark(itemcolor):
    if itemcolor.definition:
        if itemcolor.definition.pantone_plus:
            return mark_safe("<strong>+</strong>")
        else:
            return ""
    else:
        return ""
