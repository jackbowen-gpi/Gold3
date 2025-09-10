from django.http import HttpResponse
from django.urls import path

# Repo-root test URLConf to satisfy imports like `gchub_db.test_urls` used by tests.
# Always provide a basic 'logout' named URL so tests that reverse('logout') succeed.


def _simple_logout(request):
    return HttpResponse("logout ok")


urlpatterns = [path("logout/", _simple_logout, name="logout")]

"""This repo-root `test_urls.py` was moved to `_test_urls_repo_root.py`.

It previously caused unittest discovery to import the wrong module. The
package-level `gchub_db.test_urls` is the canonical test URLConf used by
the test suite.
"""

try:
    # no-op to keep the file importable during transition
    from django.urls import re_path as url  # type: ignore
except Exception:
    url = None  # type: ignore
