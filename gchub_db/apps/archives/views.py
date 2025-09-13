"""Archive search views."""

from django import forms
from django.db.models import Q
from django.forms import ModelForm
from django.shortcuts import render
from django.views.generic.list import ListView

from gchub_db.apps.archives.models import KentonArchive, RenMarkArchive
from gchub_db.includes import general_funcs


class KentonArchiveForm(ModelForm):
    class Meta:
        model = KentonArchive
        fields = "__all__"

    file = forms.CharField(required=False)


class RenMarkArchiveForm(ModelForm):
    class Meta:
        model = RenMarkArchive
        fields = "__all__"

    item = forms.CharField(required=False)
    folder_items = forms.CharField(required=False)


class SearchResults(ListView):
    """Displays job search results."""

    # Set up ListView stuff.
    paginate_by = 25
    template_name = "archive/search_results.html"
    # Extra parameter to specify which archive to search.
    archive = None

    # Searching and filtering.
    def get_queryset(self):
        # Grab appropriate archive objects.
        if self.archive == "renmark":
            qset = RenMarkArchive.objects.all()
        else:
            qset = KentonArchive.objects.all()

        # Filter via search terms.
        if self.request.GET:
            # Filter using kenton fields.
            if self.archive == "kenton":
                s_file = self.request.GET.get("file", "")
                if s_file != "":
                    qset = qset.filter(file__icontains=s_file)

                s_cd = self.request.GET.get("cd", "")
                if s_cd != "":
                    qset = qset.filter(cd__icontains=s_cd)

                # Hell yeah. Filters everything containing each word in the search.
                s_job_name = self.request.GET.get("job_name", "")
                if s_job_name != "":
                    search_words = s_job_name.split(" ")
                    q = Q()
                    for word in search_words:
                        q &= Q(job_name__icontains=word)
                    qset = qset.filter(q)

                s_art_reference = self.request.GET.get("art_reference", "")
                if s_art_reference != "":
                    qset = qset.filter(art_reference__icontains=s_art_reference)

                s_size = self.request.GET.get("size", "")
                if s_size != "":
                    qset = qset.filter(size__icontains=s_size)

                s_item_number = self.request.GET.get("item_number", "")
                if s_item_number != "":
                    qset = qset.filter(item_number__icontains=s_item_number)

                s_document_number = self.request.GET.get("document_number", "")
                if s_document_number != "":
                    qset = qset.filter(document_number=s_document_number)

            # Filter using renmark fields.
            if self.archive == "renmark":
                s_item = self.request.GET.get("item", "")
                if s_item != "":
                    qset = qset.filter(item__icontains=s_item)

                s_folder_items = self.request.GET.get("folder_items", "")
                if s_folder_items != "":
                    qset = qset.filter(folder_items__icontains=s_folder_items)

        # Sort records.
        qset = qset.order_by("-id")

        return qset

    # Set context data.
    def get_context_data(self, **kwargs):
        context = super(SearchResults, self).get_context_data(**kwargs)
        context["page_title"] = "Archive Search Results"
        context["archive"] = self.archive
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context


def search(request, archive):
    """Displays the search form."""
    if archive == "renmark":
        form = RenMarkArchiveForm(request.GET)
    else:
        form = KentonArchiveForm(request.GET)

    if request.GET and form.is_valid():
        # Call the result view directly for display.
        return SearchResults.as_view(archive=archive)(request)
    else:
        # This is the search page to be re-displayed if there's a problem or no
        # POST data.
        if archive == "renmark":
            form = RenMarkArchiveForm()
        else:
            form = KentonArchiveForm()

        pagevars = {
            "page_title": "Archive Search",
            "archive": archive,
            "form": form,
        }
        return render(request, "archive/search_form.html", context=pagevars)
