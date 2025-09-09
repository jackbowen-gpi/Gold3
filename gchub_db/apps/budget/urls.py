from django.urls import re_path as url

from gchub_db.apps.budget.views import (
    billing_home,
    display_pricing_tables,
    line_item_monthly,
    monthly_by_plant,
    yearly_report,
)

urlpatterns = [
    url(r"^summary/$", billing_home, name="billing_home"),
    url(
        r"^billing/(?P<year_num>\d+)/(?P<month_num>\d+)/(?P<workflow>\D+)/(?P<datatype>\D+)/$",
        monthly_by_plant,
        name="monthly_by_plant",
    ),
    url(
        r"^billing/line_item/(?P<year_num>\d+)/(?P<month_num>\d+)/(?P<workflow>\D+)/(?P<datatype>\D+)/$",
        line_item_monthly,
        name="line_item_monthly",
    ),
    url(
        r"^billing/(?P<year_num>\d+)/yearly_report/$",
        yearly_report,
        name="yearly_report",
    ),
    url(
        r"^(?P<workflow>\D+)/display_pricing_tables/$",
        display_pricing_tables,
        name="display_pricing_tables",
    ),
]
