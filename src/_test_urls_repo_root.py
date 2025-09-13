"""
Repo-root minimal URLConf kept for reference but renamed to avoid
conflicts with package-level `gchub_db.test_urls` during unittest discovery.
"""

try:
    # Django < 2.0
    from django.conf.urls import include, url  # type: ignore[attr-defined]
except Exception:
    from django.urls import include
    from django.urls import re_path as url

urlpatterns = [
    url(r"^workflow/", include("gchub_db.apps.workflow.urls")),
]
