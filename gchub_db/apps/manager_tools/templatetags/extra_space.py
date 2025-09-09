from django import template

register = template.Library()

# Just wanted to add some extra space around forward slashes in some text in the template so the text would flow better.


@register.filter
def extra_space(value):
    return value.replace("/", " / ")
