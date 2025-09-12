from django.urls import re_path as url

from gchub_db.apps.draw_down.views import (
    home,
    show,
    show_legacy,
    delete_drawdown,
    edit_drawdown,
    view_drawdown,
    drawdown_search,
    drawdown_search_results,
    complete_drawdown,
    pending_drawdown,
)

urlpatterns = [
    url(r"^$", home, name="drawdown_home"),
    url(r"^(?P<job_id>\d+)/$", home, name="drawdown_home"),
    url(r"^show/$", show, name="drop_down_show"),
    url(r"^show/legacy/$", show_legacy, name="drop_down_show_legacy"),
    url(r"^delete/(?P<contact_id>\d+)/$", delete_drawdown, name="drawdown_delete"),
    url(r"^edit/(?P<contact_id>\d+)/$", edit_drawdown, name="drawdown_edit"),
    url(r"^view/(?P<contact_id>\d+)/$", view_drawdown, name="drawdown_view"),
    url(r"^search/$", drawdown_search, name="drop_down_search"),
    url(r"^search_results/$", drawdown_search_results, name="drop_down_search"),
    url(r"^complete/(?P<drawdown_id>\d+)/$", complete_drawdown, name="drawdown_complete"),
    url(r"^pending/(?P<drawdown_id>\d+)/$", pending_drawdown, name="drawdown_pending"),
]
