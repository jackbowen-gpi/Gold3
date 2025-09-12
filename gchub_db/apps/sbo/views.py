"""Safety Behavior Observation Views"""

from datetime import date

from django import forms
from django.contrib.auth.models import Permission, User
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic.list import ListView

from gchub_db.apps.sbo.models import SBO
from gchub_db.includes import general_funcs
from gchub_db.includes.widgets import GCH_SelectDateWidget
from gchub_db.middleware import threadlocals

risk_safe_choices = (
    ("----", "----"),
    ("at_risk", "At Risk"),
    ("safe", "Safe"),
)

management = ["Richard_Gillette", "James_McCracken", "Sana_Davis", "Shelly_Congdon"]


class ModelSBOForm(ModelForm):
    class Meta:
        model = SBO
        fields = (
            "observed",
            "date_observed",
            "task",
            "behavior",
            "behavior_type",
            "reason",
            "communication",
            "describe_communication",
            "additional_comments",
        )

    def __init__(self, *args, **kwargs):
        super(ModelSBOForm, self).__init__(*args, **kwargs)
        permission = Permission.objects.get(codename="in_artist_pulldown")
        artists = User.objects.filter(
            is_active=True, groups__in=permission.group_set.all()
        ).order_by("username")

        self.fields["task"].widget.attrs["placeholder"] = (
            "What was the task being performed?"
        )
        self.fields["task"].label = "Task Performed"
        self.fields["task"].widget.attrs["height"] = 50
        self.fields["task"].widget.attrs["width"] = 200
        self.fields["behavior_type"].label = "Behavior Type"
        self.fields["behavior"].widget.attrs["placeholder"] = (
            "How was the task being performed?"
        )
        self.fields["behavior"].label = "Behavior Observed"
        self.fields["reason"].widget.attrs["placeholder"] = (
            "Why was the task performed safe or at risk?"
        )
        self.fields["reason"].label = "Reason"
        self.fields["communication"].label = "Communication"
        self.fields["describe_communication"].widget.attrs["placeholder"] = (
            "How did you communicate with the person involved in performing the task"
        )
        self.fields["describe_communication"].label = "Describe Communication"
        self.fields["additional_comments"].widget.attrs["placeholder"] = (
            "Any additional comments for this safety behavior observation"
        )
        self.fields["additional_comments"].label = "Additional Comments"
        self.fields["additional_comments"].required = False
        self.fields["date_observed"].label = "Date Observed"

        # Finish initializing fields that depend on runtime queries.
        self.fields["observed"].queryset = artists
        self.fields["observed"].label = "Person Observed"
        ob_date = general_funcs._utcnow_naive().date()
        self.fields["date_observed"].initial = ob_date.strftime("%m/%d/%Y")


def _get_artist_permission():
    try:
        return Permission.objects.get(codename="in_artist_pulldown")
    except Exception:
        return None


def _get_artist_qs():
    perm = _get_artist_permission()
    if perm is None:
        return User.objects.none()
    return User.objects.filter(
        is_active=True, groups__in=perm.group_set.all()
    ).order_by("username")


class SearchSBOForm(forms.Form):
    status_choices = [
        ("---", "---"),
        ("at_risk", "At Risk"),
        ("safe", "Safe"),
    ]
    status = behavior_type = forms.ChoiceField(
        choices=risk_safe_choices, required=False
    )
    start_date = forms.DateField(widget=GCH_SelectDateWidget, required=False)
    end_date = forms.DateField(widget=GCH_SelectDateWidget, required=False)
    # Defer DB access; populate artist choices in __init__.
    observed = forms.ChoiceField(
        choices=(("", "----"), ("Potential Risk", "Potential Risk")), required=False
    )

    class Meta:
        model = SBO
        fields = ("observed", "date_observed", "behavior_type", "communication")

    def __init__(self, *args, **kwargs):
        super(SearchSBOForm, self).__init__(*args, **kwargs)
        # Populate artist choices at runtime.
        try:
            artists_qs = _get_artist_qs()
            artists = [("", "----"), ("Potential Risk", "Potential Risk")] + [
                (u.username, u.username.replace("_", " ")) for u in artists_qs
            ]
        except Exception:
            artists = [("", "----"), ("Potential Risk", "Potential Risk")]
        self.fields["observed"].choices = artists


class SBOHome(ListView):
    model = SBO
    paginate_by = 25
    template_name = "sbo/home.html"

    """
        0 = home
        1 = search
        2 = new sbo
        3 = reports
    """

    def get(self, *args, **kwargs):
        errors = []

        sboForm = ModelSBOForm(self.request.POST)
        focus = 0

        self.object_list = SBO.objects.all().order_by("-date_observed")

        context = self.get_context_data(
            object_list=self.object_list, errors=errors, focus=focus, sboForm=sboForm
        )

        return render(self.request, self.template_name, context=context)

    def post(self, *args, **kwargs):
        errors = []

        sboForm = ModelSBOForm(self.request.POST)
        if sboForm.is_valid():
            sboForm.save()
            focus = 0
        else:
            focus = 2
            for error in sboForm.errors:
                errors.append(error)

        self.object_list = SBO.objects.all().order_by("-date_observed")

        context = self.get_context_data(
            object_list=self.object_list, errors=errors, focus=focus, sboForm=sboForm
        )

        return render(self.request, self.template_name, context=context)

    def get_context_data(self, **kwargs):
        context = super(SBOHome, self).get_context_data(**kwargs)

        try:
            errors = kwargs["errors"]
        except Exception:
            errors = []
        try:
            focus = kwargs["focus"]
        except Exception:
            focus = 0
        try:
            sboForm = kwargs["sboForm"]
        except Exception:
            sboForm = ModelSBOForm()

        try:
            year = self.kwargs["year"]
        except Exception:
            year = False

        searchForm = SearchSBOForm()

        if self.request.GET and self.request.GET.get("status") is not None:
            searchForm = SearchSBOForm(self.request.GET)
            if searchForm.is_valid():
                # Call the result view directly for display.
                return SBOSearch.as_view()(self.request)
            else:
                focus = 1
                for error in searchForm.errors:
                    errors.append(error)
        if not year:
            today = general_funcs._utcnow_naive().date()
            year = today.year
        else:
            focus = 3

        sbo_annual_form = get_sbo_annual_data(year)

        # array of years used to display yearly reports
        start_year = 2016
        current_year = date.today().year
        years_to_display = []
        while start_year <= current_year:
            years_to_display.append(current_year)
            # make sure to put the years in backwards so you start at current
            current_year = current_year - 1

        user = threadlocals.get_current_user()
        manager = False
        if str(user) in management:
            manager = True

        context["page_title"] = "SBO Program"
        context["sbo_annual_form"] = sbo_annual_form
        context["years_to_display"] = years_to_display
        context["newSBOform"] = sboForm
        context["search_form"] = searchForm
        context["errors"] = errors
        context["tab_error_num"] = focus + 1
        context["focus"] = focus
        context["manager"] = manager
        context["extra_link"] = general_funcs.paginate_get_request(self.request)

        return context


class SBOSearch(ListView):
    model = SBO
    paginate_by = 25
    template_name = "sbo/search_sbo.html"

    def get_queryset(self):
        qset = SBO.objects.all().order_by("-date_observed")
        status = self.request.GET.get("status", "----")
        if status != "----":
            qset = qset.filter(behavior_type=status)
        # If start and end date given, search on range, else search on just start.
        date_in_start_year = self.request.GET.get("start_date_year", 0)
        date_in_start_month = self.request.GET.get("start_date_month", 0)
        date_in_start_day = self.request.GET.get("start_date_day", 0)
        date_in_end_year = self.request.GET.get("end_date_year", 0)
        date_in_end_month = self.request.GET.get("end_date_month", 0)
        date_in_end_day = self.request.GET.get("end_date_day", 0)

        try:
            date_in_start = date(
                int(date_in_start_year),
                int(date_in_start_month),
                int(date_in_start_day),
            )
        except Exception:
            date_in_start = 0
        try:
            date_in_end = date(
                int(date_in_end_year), int(date_in_end_month), int(date_in_end_day)
            )
        except Exception:
            date_in_end = 0

        observed_person = self.request.GET.get("observed", "")
        if date_in_end != 0:
            if date_in_start != 0:
                qset = qset.filter(date_observed__range=(date_in_start, date_in_end))
        elif date_in_start != 0:
            qset = qset.filter(date_observed=date_in_start)
        # If there is an observed person it will either be a username or Potential Risk
        # if it is Potential then we search for the observed users with None Type
        # else we search for the username
        # if they chose ---- then there will not be an observed person sent along and we search without that criteria
        elif observed_person != "":
            if observed_person == "Potential Risk":
                qset = qset.filter(observed=None)
            else:
                qset = qset.filter(observed__username=observed_person)

        return qset

    def get_context_data(self, **kwargs):
        context = super(SBOSearch, self).get_context_data(**kwargs)

        context["page_title"] = "SBO Search"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)

        return context

    def dispatch(self, *args, **kwargs):
        if self.get_queryset().count() == 1:
            sbo_detail_url = reverse("sbo_detail", args=[self.get_queryset()[0].id])
            return HttpResponseRedirect(sbo_detail_url)
        else:
            return super(SBOSearch, self).dispatch(*args, **kwargs)


def sbo_detail(request, sbo_id):
    try:
        sbo = SBO.objects.get(id=sbo_id)
        observer = sbo.observer
        observed = sbo.observed
    except Exception:
        observer = []
        observed = []
        sbo = []

    user = threadlocals.get_current_user()
    manager = False
    if str(user) in management:
        manager = True

    pagevars = {
        "page_title": "SBO Search Results",
        "sbo": sbo,
        "observer": observer,
        "observed": observed,
        "manager": manager,
    }

    return render(request, "sbo/sbo_detail.html", context=pagevars)


def get_sbo_annual_data(year):
    return_object = []
    return_object.append({"Jan": {}})
    return_object.append({"Feb": {}})
    return_object.append({"Mar": {}})
    return_object.append({"Apr": {}})
    return_object.append({"May": {}})
    return_object.append({"Jun": {}})
    return_object.append({"Jul": {}})
    return_object.append({"Aug": {}})
    return_object.append({"Sep": {}})
    return_object.append({"Oct": {}})
    return_object.append({"Nov": {}})
    return_object.append({"Dec": {}})

    for month_counter in range(len(return_object)):
        sbo_annual = {}

        permission = Permission.objects.get(codename="in_artist_pulldown")
        artists = User.objects.filter(
            is_active=True, groups__in=permission.group_set.all()
        ).order_by("username")

        sbos = SBO.objects.filter(
            date_observed__year=year, date_observed__month=month_counter + 1
        ).order_by("-date_observed")

        sbo_annual["total_count"] = sbos.count()
        sbo_annual["total_communicated"] = sbos.filter(communication=True).count()
        sbo_annual["safe_count"] = sbos.filter(behavior_type="safe").count()
        sbo_annual["safe_communicated"] = sbos.filter(
            behavior_type="safe", communication=True
        ).count()
        sbo_annual["risky_count"] = sbos.filter(behavior_type="at_risk").count()
        sbo_annual["risky_communicated"] = sbos.filter(
            behavior_type="at_risk", communication=True
        ).count()

        user_check = {}
        temp_total = 0
        temp_completed = 0
        for x in range(len(artists)):
            temp_total += 1
            user_check[artists[x].username] = sbos.filter(observer=artists[x]).count()
            if sbos.filter(observer=artists[x]).count() > 0:
                temp_completed += 1
        sbo_annual["user_check"] = user_check
        if temp_total > 0:
            x = "%.2f" % (float(temp_completed) / float(temp_total))
            sbo_annual["user_completion"] = float(x) * 100
        else:
            sbo_annual["user_completion"] = 0

        for month in return_object[month_counter]:
            return_object[month_counter][month] = sbo_annual

    return return_object
