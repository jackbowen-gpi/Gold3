"""
The urls.py file handles URL dispatching for the workflow module. Requests
that begin with /xml are sent here. The major models get their own
URL matching sections below, which are combined into urlpatterns at the end
of the file for matching.
"""

from django.urls import re_path as url

from gchub_db.apps.xml_io.views import echo_input, run_jdf_jobitem, generate_jdf_jobitem

jmf_views = [
    url(r"^echo$", echo_input),
    url(
        r"^jdf/run/(?P<job_id>\d+)/(?P<item_num>\d+)/(?P<genxml_func>\D+)",
        run_jdf_jobitem,
        name="jdf-run-item",
    ),
    url(
        r"^jdf/gen/(?P<job_id>\d+)/(?P<item_num>\d+)/(?P<genxml_func>\D+)",
        generate_jdf_jobitem,
        name="jdf-gen-item",
    ),
]

# Combine the components.
urlpatterns = jmf_views
