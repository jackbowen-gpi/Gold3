"""Autocomplete views for workflow search functionality."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q

from gchub_db.apps.workflow.models import Job, Item


@login_required
def job_autocomplete(request):
    """Autocomplete API for job search universal search box."""
    term = request.GET.get("term", "").strip()
    if len(term) < 2:  # Only search if at least 2 characters
        return JsonResponse([], safe=False)

    # Search across multiple fields and limit results
    jobs = Job.objects.filter(
        Q(id__icontains=term)
        | Q(name__icontains=term)
        | Q(brand_name__icontains=term)
        | Q(customer_name__icontains=term)
        | Q(po_number__icontains=term)
        | Q(customer_po_number__icontains=term)
        | Q(e_tools_id__icontains=term)
    ).distinct()[:10]  # Limit to 10 results

    suggestions = []
    for job in jobs:
        # Create descriptive text for each suggestion
        label = f"Job #{job.id}"
        if job.name:
            label += f" - {job.name}"
        if job.brand_name:
            label += f" ({job.brand_name})"
        if job.customer_name:
            label += f" - {job.customer_name}"

        suggestions.append(
            {
                "id": job.id,
                "label": label,
                "value": str(job.id),  # What gets filled in the search box
            }
        )

    return JsonResponse(suggestions, safe=False)


@login_required
def item_autocomplete(request):
    """Autocomplete API for item search universal search box."""
    term = request.GET.get("term", "").strip()
    if len(term) < 2:  # Only search if at least 2 characters
        return JsonResponse([], safe=False)

    # Search across multiple fields and limit results
    items = (
        Item.objects.filter(
            Q(job__id__icontains=term)
            | Q(size__size__icontains=term)
            | Q(bev_item_name__icontains=term)
            | Q(description__icontains=term)
            | Q(upc_number__icontains=term)
            | Q(bom_number__icontains=term)
            | Q(wrin_number__icontains=term)
            | Q(job__name__icontains=term)
            | Q(job__brand_name__icontains=term)
            | Q(job__customer_name__icontains=term)
        )
        .distinct()
        .select_related("job", "size")[:10]
    )  # Limit to 10 results

    suggestions = []
    for item in items:
        # Create descriptive text for each suggestion
        label = f"Job #{item.job.id}"
        if item.size and item.size.size:
            label += f" - {item.size.size}"
        if item.description:
            label += f" - {item.description}"
        if item.job.name:
            label += f" ({item.job.name})"

        # For items, we might want to search by job number or item details
        value = str(item.job.id) if term.isdigit() else (item.description or str(item.job.id))

        suggestions.append({"id": item.id, "label": label, "value": value})

    return JsonResponse(suggestions, safe=False)
