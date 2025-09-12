"""Links to item tasks with sanity checks included."""

import os
from random import shuffle

from django import template
from django.conf import settings

# from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def random_cute_img_url(blah):
    """
    Selects a random adorable image from the media/img/cute directory.
    Returns the URL to it.
    """
    cute_dir = os.path.join(settings.MEDIA_ROOT, "img", "cute")
    matches = next(os.walk(cute_dir))[2]

    excluded_files = [".DS_Store", ".svn"]
    contents = [match for match in matches if match not in excluded_files]
    shuffle(contents)
    return settings.MEDIA_URL + "img/cute/" + contents[0]
