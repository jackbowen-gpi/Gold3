from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from gchub_db.apps.carton_billing.models import CartonSapEntry
from gchub_db.apps.joblog.app_defs import JOBLOG_TYPE_NOTE
from gchub_db.apps.joblog.models import JobLog
from gchub_db.includes import general_funcs
from gchub_db.middleware import threadlocals


class SapEntryQueue(ListView):
    """Listing of all pending SAP billing entries."""

    # Gather the entries without qad entry dates.
    queryset = CartonSapEntry.objects.filter(qad_entry_date__isnull=True).order_by(
        "-creation_date"
    )
    paginate_by = 25
    template_name = "carton_billing/search_results.html"

    def get_context_data(self, **kwargs):
        context = super(SapEntryQueue, self).get_context_data(**kwargs)
        context["page_title"] = "Carton SAP Billing Entries Pending"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context

    # Require the user to be logged in to GOLD to view.
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SapEntryQueue, self).dispatch(*args, **kwargs)


@login_required
def complete_sap_entry(request, entry_id):
    """Mark an entry as entered into SAP."""
    # Mark the entry as completed.
    entry = CartonSapEntry.objects.get(id=entry_id)
    entry.qad_entry_date = date.today()
    entry.qad_entry_user = threadlocals.get_current_user()
    entry.save()
    # Put a note about it in the joblog.
    new_log = JobLog()
    new_log.job = entry.job
    new_log.type = JOBLOG_TYPE_NOTE
    new_log.user = threadlocals.get_current_user()
    new_log.log_text = (
        "Billing has been entered into SAP and GREQ has been closed by %s."
        % threadlocals.get_current_user()
    )
    new_log.save()
    return HttpResponseRedirect(reverse("sap_entry_queue"))
