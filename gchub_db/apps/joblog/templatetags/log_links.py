"""Links to log files with sanity checks included."""

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

from gchub_db.includes import fs_api

register = template.Library()


@register.filter
def log_proof_link(log, link_text=""):
    """
    Generates the necessary HTML to render a PDF proof link. If the
    proof can't be found, make the link show an error message.
    """
    try:
        if log.item.job.workflow.name == "Beverage":
            # Beverage links low res proofs.
            fs_api.get_item_proof(log.item.job.id, log.item.num_in_job, "l", log.id)
        else:
            fs_api.get_item_proof(log.item.job.id, log.item.num_in_job, quality=None, proof_log_id=log.id)

        return mark_safe(
            """
          <a href='%s'>
            <img src='%simg/icons/page_white_acrobat.png' style='vertical-align:text-bottom' alt='Previous Proof' />
            %s
          </a>"""
            % (
                reverse(
                    "get_item_past_proof",
                    args=[log.item.job.id, log.item.num_in_job, log.id],
                ),
                settings.MEDIA_URL,
                link_text,
            )
        )
    except Exception:
        return mark_safe(
            """
          <a onclick=\"alert('An error occured while resolving the proof PDF link.')\">
            <img src='%simg/icons/page_white_acrobat_dimmed.png' style='vertical-align:text-bottom' alt='No Proof' />
            %s
          </a>"""
            % (settings.MEDIA_URL, link_text)
        )
