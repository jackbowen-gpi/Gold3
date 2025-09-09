"""QAD_DATA Views"""

from django.db.models import Q
from django.forms import ModelForm
from django.shortcuts import render
from django.views.generic.list import ListView

from gchub_db.apps.qad_data.models import QAD_PrintGroups
from gchub_db.includes import general_funcs


class QAD_PrintGroup_Form(ModelForm):
    """QAD search form."""

    class Meta:
        model = QAD_PrintGroups
        fields = "__all__"


def qad_data(request):
    """QAD_Data Home Page"""
    pagevars = {"page_title": "QAD Data", "form": QAD_PrintGroup_Form()}

    return render(request, "qad_data/search_form.html", context=pagevars)


def search_printgroup(request):
    """Displays the QAD PrintGroup search ."""
    pagevars = {"page_title": "QAD Data", "form": QAD_PrintGroup_Form()}
    # This is the search page to be re-displayed if there's a problem or no
    # POST data.
    search_page = render(request, "qad_data/search_form.html", context=pagevars)

    if request.GET:
        form = QAD_PrintGroup_Form(request.GET)
        if form.is_valid():
            # It's easier to store a dict of the possible lookups we want, where
            # the values are the keyword arguments for the actual query.
            qdict = {
                "name": "name__icontains",
                "description": "description__icontains",
            }

            # Then we can do this all in one step instead of needing to call
            # 'filter' and deal with intermediate data structures.
            q_objs = [
                Q(**{qdict[k]: form.cleaned_data[k]})
                for k in list(qdict.keys())
                if form.cleaned_data.get(k, None)
            ]
            search_results = (
                QAD_PrintGroups.objects.select_related()
                .filter(*q_objs)
                .order_by("name")
            )

            # Call the result view directly for display.
            return PrintgroupSearchResults.as_view(queryset=search_results)(request)
        else:
            # Errors in form data, return the form with messages.
            return search_page
    else:
        # No POST data, return an empty form.
        return search_page


class PrintgroupSearchResults(ListView):
    """Displays job search results."""

    # Set up ListView stuff.
    model = QAD_PrintGroups
    paginate_by = 25
    template_name = "qad_data/search_results.html"

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(PrintgroupSearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Print Group Search Results"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context
