from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from gchub_db.apps.qc.models import QCResponseDoc
from gchub_db.apps.workflow.models import Item, Job
from gchub_db.includes.gold_json import JSMessage


@csrf_exempt
def qc_manager(request, job_id):
    """Manage shipping address associated with job."""
    job = get_object_or_404(Job, id=int(job_id))

    pagevars = {
        "job": job,
    }
    return render(request, "qc_manager/qc_overview.html", context=pagevars)


@csrf_exempt
def select_and_create(request, job_id):
    """Select the items for which this QC applies."""

    pagevars = {
        "job_id": job_id,
    }
    return render(request, "qc_manager/select_and_create.html", context=pagevars)


def ajax_create_qc(request, job_id):
    """Sends the request to create a QC."""

    if not request.user.is_authenticated:
        return HttpResponse(
            JSMessage(
                "Your GOLD session is goofed up. Please log out and log back in.",
                is_error=True,
            )
        )

    items = []
    for key, item_id in request.POST.items():
        try:
            item = get_object_or_404(Item, id=int(item_id))
            items.append(item)
        except ValueError:
            # This happens on Safari, the extra comma cause funkage.
            pass

    if not items:
        return HttpResponse(JSMessage("Select at least one item to review.", is_error=True))

    qcr = QCResponseDoc.objects.start_qc_for_items(items, request.user)

    return HttpResponse(JSMessage(reverse("qc_edit_qc", args=[qcr.id])))


def ajax_create_qc2(request, job_id):
    """Sends the request to create a QC."""

    if not request.user.is_authenticated:
        return HttpResponse(
            JSMessage(
                "Your GOLD session is goofed up. Please log out and log back in.",
                is_error=True,
            )
        )

    items = []
    for key, item_id in request.POST.items():
        try:
            item = get_object_or_404(Item, id=int(item_id))
            items.append(item)
        except ValueError:
            # This happens on Safari, the extra comma cause funkage.
            pass

    if not items:
        return HttpResponse(JSMessage("Select at least one item to review.", is_error=True))

    qcr = QCResponseDoc.objects.start_qc_for_items(items, request.user)

    return HttpResponse(JSMessage(reverse("qc_edit_qc2", args=[qcr.id])))
