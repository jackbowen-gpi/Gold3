"""Links to item tasks with sanity checks included."""

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

from gchub_db.includes import fs_api

register = template.Library()


@register.filter
def hasgroup(user, groupName):
    return user.groups.filter(name=groupName).exists()


def _safe_link(html_template, *args):
    """Helper to format and mark safe HTML templates."""
    return mark_safe(html_template % args)


@register.filter
def item_stepped_proof_link(item, link_text="Stepped Proof"):
    """Render a stepped proof link or an informative fallback."""
    if item.current_revision():
        return _safe_link(
            """
              <a onclick=\"alert('Stepped Proof is not available if revisions are pending.')\">
                <img src='%simg/icons/hourglass.png' style='vertical-align:text-bottom' alt='Awaiting Revision' />
                %s
              </a>""",
            settings.MEDIA_URL,
            link_text,
        )

    try:
        if item.job.workflow.name == "Beverage":
            fs_api.get_item_proof(item.job.id, item.num_in_job, "h")

        return _safe_link(
            """
              <a href='%s'>
                <img src='%simg/icons/page_white_acrobat.png' style='vertical-align:text-bottom' alt='SteppedProof' />
                %s
              </a>""",
            reverse("get_stepped_item_proof", args=[item.job.id, item.num_in_job]),
            settings.MEDIA_URL,
            link_text,
        )
    except Exception:
        return _safe_link(
            """
              <a onclick=\"alert('An error occured while resolving the stepped proof PDF link.')\">
                <img src='%simg/icons/page_white_acrobat_dimmed.png' style='vertical-align:text-bottom' alt='No Proof' />
                %s
              </a>""",
            settings.MEDIA_URL,
            link_text,
        )


@register.filter
def item_proof_link(item, link_text="Proof"):
    if item.current_revision():
        return _safe_link(
            """
              <a onclick=\"alert('Proof is not available if revisions are pending.')\">
                <img src='%simg/icons/hourglass.png' style='vertical-align:text-bottom' alt='Awaiting Revision' />
                %s
              </a>""",
            settings.MEDIA_URL,
            link_text,
        )

    try:
        if item.job.workflow.name == "Beverage":
            fs_api.get_item_proof(item.job.id, item.num_in_job, "l")
        else:
            fs_api.get_item_proof(item.job.id, item.num_in_job)

        return _safe_link(
            """
              <a href='%s'>
                <img src='%simg/icons/page_white_acrobat.png' style='vertical-align:text-bottom' alt='Proof' />
                %s
              </a>""",
            reverse("get_item_proof", args=[item.job.id, item.num_in_job]),
            settings.MEDIA_URL,
            link_text,
        )
    except Exception:
        return _safe_link(
            """
              <a onclick=\"alert('An error occured while resolving the proof PDF link.')\">
                <img src='%simg/icons/page_white_acrobat_dimmed.png' style='vertical-align:text-bottom' alt='No Proof' />
                %s
              </a>""",
            settings.MEDIA_URL,
            link_text,
        )


@register.filter
def item_finalfile_link(item, link_text="Production File"):
    try:
        fs_api.get_item_finalfile(item.job.id, item.num_in_job)
        return _safe_link(
            """
          <a href='%s'>
            <img src='%simg/icons/page_white_acrobat.png' style='vertical-align:text-bottom' alt='FinalFile' />
            %s
          </a>""",
            reverse("get_item_finalfile", args=[item.job.id, item.num_in_job]),
            settings.MEDIA_URL,
            link_text,
        )
    except Exception:
        return _safe_link(
            """
          <a onclick=\"alert('An error occured while resolving the Final File PDF link.')\">
            <img src='%simg/icons/page_white_acrobat_dimmed.png' style='vertical-align:text-bottom' alt='No FinalFile' />
            %s
          </a>""",
            settings.MEDIA_URL,
            link_text,
        )


@register.filter
def item_approval_link(item, link_text="Approval"):
    try:
        fs_api.get_item_approval_pdf(item.job.id, item.num_in_job)
        return _safe_link(
            """
          <a href='%s'>
            <img src='%simg/icons/picture_edit.png' style='vertical-align:text-bottom' alt='Approval' />
            %s
          </a>""",
            reverse("get_item_approval_scan", args=[item.job.id, item.num_in_job]),
            settings.MEDIA_URL,
            link_text,
        )
    except Exception:
        return _safe_link(
            """
          <a onclick=\"alert('An error occured while resolving the approval PDF link.')\">
            <img src='%simg/icons/picture_edit_dimmed.png' style='vertical-align:text-bottom' alt='No Approval' />
            %s
          </a>""",
            settings.MEDIA_URL,
            link_text,
        )


@register.filter
def item_preview_art_link(item, link_text="Preview Art"):
    try:
        fs_api.get_item_preview_art(item.job.id, item.num_in_job)
        return _safe_link(
            """
          <a href='%s'>
            <img src='%simg/icons/picture_save.png' style='vertical-align:text-bottom' alt='Preview' />
            %s
          </a>""",
            reverse("get_item_preview_art", args=[item.job.id, item.num_in_job]),
            settings.MEDIA_URL,
            link_text,
        )
    except fs_api.NoResultsFound:
        # Check if this is development mode with file system access disabled
        if not getattr(settings, "FS_ACCESS_ENABLED", True):
            alert_message = "Preview art is not available in development mode."
        else:
            alert_message = "No preview artwork available for this item."

        return _safe_link(
            """
          <a onclick=\"alert('%s')\">
            <img src='%simg/icons/picture_save_dimmed.png' style='vertical-align:text-bottom' alt='No Preview' />
            %s
          </a>""",
            alert_message,
            settings.MEDIA_URL,
            link_text,
        )
    except Exception:
        return _safe_link(
            """
          <a onclick=\"alert('An error occurred while resolving the preview art link.')\">
            <img src='%simg/icons/picture_save_dimmed.png' style='vertical-align:text-bottom' alt='No Preview' />
            %s
          </a>""",
            settings.MEDIA_URL,
            link_text,
        )


@register.filter
def item_print_seps_link(item, link_text="Printable Separations"):
    try:
        fs_api.get_item_print_seps(item.job.id, item.num_in_job)
        return _safe_link(
            """
          <a href='%s'>
            <img src='%simg/icons/page_white_acrobat.png' style='vertical-align:text-bottom' alt='Separations' />
            %s
          </a>""",
            reverse("get_item_print_seps", args=[item.job.id, item.num_in_job]),
            settings.MEDIA_URL,
            link_text,
        )
    except fs_api.NoResultsFound:
        # Check if this is development mode with file system access disabled
        if not getattr(settings, "FS_ACCESS_ENABLED", True):
            alert_message = "Printable separations are not available in development mode."
        else:
            alert_message = "No printable separations are available for this item."

        return _safe_link(
            """
          <a onclick=\"alert('%s')\">
            <img src='%simg/icons/page_white_acrobat_dimmed.png' style='vertical-align:text-bottom' alt='No Separations' />
            %s
          </a>""",
            alert_message,
            settings.MEDIA_URL,
            link_text,
        )
    except Exception:
        return _safe_link(
            """
          <a onclick=\"alert('An error occurred while resolving the printable separations link.')\">
            <img src='%simg/icons/page_white_acrobat_dimmed.png' style='vertical-align:text-bottom' alt='No Separations' />
            %s
          </a>""",
            settings.MEDIA_URL,
            link_text,
        )


@register.filter
def item_download_zip_tiffs_link(item, link_text="Download all tiffs in ZIP format"):
    try:
        if fs_api.list_item_tiffs(item.job.id, item.num_in_job):
            return _safe_link(
                """
              <a href='%s'>
                <img src='%simg/icons/compress.png' style='vertical-align:text-bottom' alt='TIFFs' />
                %s
              </a>""",
                reverse("get_zipfile_tiff", args=[item.id]),
                settings.MEDIA_URL,
                link_text,
            )
    except Exception:
        pass

    return _safe_link(
        """
      <a onclick=\"alert('An error occured while resolving the tiff download link.')\">
        <img src='%simg/icons/compress_dimmed.png' style='vertical-align:text-bottom' alt='No TIFFs' />
        %s
      </a>""",
        settings.MEDIA_URL,
        link_text,
    )
