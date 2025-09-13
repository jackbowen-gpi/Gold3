"""Generic extra widgets that are not specific to one app."""

from django.forms.widgets import SelectDateWidget
from django.utils import timezone


class GCH_SelectDateWidget(SelectDateWidget):
    """SelectDateWidget with a repository-default year range."""

    def __init__(self, attrs=None, years=None):
        """Use a sensible default year range instead of Django's default."""
        if not years:
            this_year = timezone.now().year
            years = range(1999, this_year + 3)

        # Call the super class's init (SelectDateWidget) with modified values.
        super(GCH_SelectDateWidget, self).__init__(attrs=attrs, years=years)
