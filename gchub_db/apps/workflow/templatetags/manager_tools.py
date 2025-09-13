"""Used to hide and show certain manager specific elements."""

from django import template

register = template.Library()


@register.filter
def show_manager_tools(job):
    return job.todo_list_html(show_manager_tools=True, fileout=False)


@register.filter
def show_manager_tools_fileout(job):
    return job.todo_list_html(show_manager_tools=True, fileout=True)
