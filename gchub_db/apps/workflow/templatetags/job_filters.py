"""Misc. job filters."""

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

from gchub_db.includes import fs_api

register = template.Library()


@register.filter
def job_thumbnail(job, width=155):
    """
    Returns one of the generated thumbnails of the desired size. If you
    request a size that does not exist, the filter fails silently.
    NOTE: This filter does not generate thumbnails, it merely looks for
    the ones that have already been generated.
    """
    # print "WIDTH", width
    try:
        # Fine the item that was most recently thumbnailed and use that.
        thumbnailed_item = job.item_set.filter(time_last_thumbnailed__isnull=False).order_by("-time_last_thumbnailed")[0]
        # print "ITEM", thumbnailed_item
    except IndexError:
        # Fail silently if none have been thumbnailed.
        # return "NO THUMBS"
        return ""

    try:
        thumbnail_file = fs_api.get_thumbnail_item_finalfile(job.id, thumbnailed_item.num_in_job, width=int(width))
        # print "THUMB", thumbnail_file
    except fs_api.NoResultsFound:
        # This should generally not happen, as the DB says that the thumbnail
        # was generated correctly, but the file would have been deleted or
        # never created.
        thumbnail_file = False
    except fs_api.InvalidPath:
        # This usually means the drives aren't mounted.
        thumbnail_file = False

    if thumbnail_file:
        # Return the image tag with an appropriate link.
        # print "REVERSING"
        img_url = reverse("item_thumbnail_sized", args=[thumbnailed_item.id, int(width)])
        # print "URL", img_url
        return mark_safe("<img src='%s' />" % img_url)
    else:
        # No thumbnail file was found for this supposedly thumbnailed item.
        # return "BROKEN THUMB"
        return ""
