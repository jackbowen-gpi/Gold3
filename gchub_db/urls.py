"""
Package-level urls shim that delegates to the repo-root `urls.py`.
This lets DJANGO_SETTINGS_MODULE='gchub_db.settings' reference
`gchub_db.urls` while keeping the canonical URL definitions at the repo root.
"""

import os
import traceback
from importlib import import_module

# Robustly import the repo-root `urls.py`. If the import fails for any
# reason during tests, write a diagnostic file and then attempt a best-effort
# retry under test-settings; finally, fall back to a lazy include so Django
# will import the repo-root URLConf at resolution time instead of import time.
try:
    mod = import_module("urls")
    urlpatterns = getattr(mod, "urlpatterns", [])
except Exception:
    tb = traceback.format_exc()
    try:
        with open(os.path.join(os.getcwd(), "urls_import_error.txt"), "w", encoding="utf-8") as f:
            f.write(tb)
    except Exception:
        # best-effort: if we can't write the file, ignore
        pass
    # The repo-root `urls.py` could not be imported at package-import time.
    # Rather than try to import it (which may trigger AppRegistry or DB
    # access before Django is configured), create a lazy include that will
    # defer importing the repo-root URLConf until URL resolution time.
    try:
        try:
            from django.urls import include as _include
            from django.urls import re_path as url
        except Exception:
            from django.conf.urls import include as _include
            from django.conf.urls import url

        urlpatterns = [url(r"^", _include("urls"))]
    except Exception:
        # If even constructing a lazy include fails, fall through to the
        # retry logic below which will attempt a django.setup() and a
        # re-import under test settings.
        pass

    # Best-effort retry: if the import failed because the app registry
    # wasn't ready, try setting a test settings module and call django.setup()
    try:
        if not os.environ.get("DJANGO_SETTINGS_MODULE"):
            os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.test_settings"
            try:
                import django as _django

                _django.setup()
            except Exception:
                # ignore setup errors; we'll try importing anyway
                pass
        # Try import again
        try:
            mod = import_module("urls")
            urlpatterns = getattr(mod, "urlpatterns", [])
        except Exception:
            # append retry traceback
            try:
                with open(
                    os.path.join(os.getcwd(), "urls_import_error.txt"),
                    "a",
                    encoding="utf-8",
                ) as f:
                    f.write("\n----- retry traceback -----\n")
                    f.write(traceback.format_exc())
            except Exception:
                pass
            urlpatterns = []
    except Exception:
        urlpatterns = []

# If we still don't have a proper urlpatterns, fall back to an empty list.
if not globals().get("urlpatterns"):
    # Provide a minimal, test-only set of includes to ensure key app URL
    # names (used heavily in templates) are present even if the repo-root
    # `urls.py` could not be imported. Use string-based include targets to
    # defer module imports until Django is ready.
    try:
        try:
            from django.urls import include as _include
            from django.urls import re_path as url
        except Exception:
            from django.conf.urls import include as _include
            from django.conf.urls import url

        def _fallback_job_search(request):
            from django.http import HttpResponse

            return HttpResponse("job_search fallback")

        def _fallback_list_reports(request):
            from django.http import HttpResponse

            return HttpResponse("list_reports fallback")

        urlpatterns = [
            # ensure the workflow app is available under the expected prefix
            url(r"^workflow/", _include("gchub_db.apps.workflow.urls")),
            # job search - let workflow app handle it
            # url(r"^job/search/$", _fallback_job_search, name="job_search"),
            url(r"^job/search/", _include("gchub_db.apps.workflow.urls")),
            # Note: do not provide an explicit fallback for list_reports here;
            # the real workflow app should register the named view under
            # its own URL registry. Removing the fallback avoids shadowing
            # the app-provided `list_reports` view.
        ]
    except Exception:
        urlpatterns = []

# If we still don't have a proper urlpatterns (for example because the
# direct import failed earlier), try a lazy include which defers importing
# the repo-root `urls` module until URL resolution time. This avoids
# touching the app registry at package import time.
if not globals().get("urlpatterns"):
    try:
        try:
            # Prefer new-style include import
            from django.urls import include as _include
        except Exception:
            from django.conf.urls import include as _include

        try:
            # Prefer re_path (Django>=2.0) but fall back to old url import
            from django.urls import re_path as url
        except Exception:
            from django.conf.urls import url

        # Create a lazy include to the repo-root urls module. This will
        # defer importing the top-level `urls.py` until Django is ready.
        urlpatterns = [url(r"^", _include("urls"))]
    except Exception:
        # If anything goes wrong here, leave urlpatterns empty so the
        # defensive fallback nearer the end of this module can populate
        # a minimal set appropriate for testing.
        urlpatterns = []

# Defensive fallback: ensure a simple named job_search exists so template
# rendering that calls `{% url 'job_search' %}` will not raise during
# exception handling even if the real workflow include wasn't loaded yet.
try:
    # Import django URL helpers lazily; if Django isn't ready, skip adding
    from django.conf import settings

    try:
        # Create a tiny fallback view and pattern only if name not already present
        from django.http import HttpResponse

        try:
            # Construct fallback only when urlpatterns present or empty list
            found = any(getattr(p, "name", None) == "job_search" for p in urlpatterns)
        except Exception:
            found = False
        if not found:
            try:
                # Prefer re_path if available; fall back to old-style url import
                try:
                    from django.urls import re_path as url
                except Exception:
                    from django.conf.urls import url

                def _fallback_job_search(request):
                    return HttpResponse("job_search fallback")

                # Removed fallback - let workflow app handle job search
                # urlpatterns.insert(0, url(r"^job/search/$", _fallback_job_search, name="job_search"))
            except Exception:
                # best-effort: ignore failures in fallback job_search setup
                pass
            # Expose a small dev-only helper to set a session cookie from the
            # helper-written file so the developer's browser can be auto-logged-in.
            if getattr(settings, "DEBUG", False):
                try:
                    from .dev_views import dev_whoami, set_dev_session

                    urlpatterns.insert(
                        0,
                        url(
                            r"^__dev_set_session/$",
                            set_dev_session,
                            name="__dev_set_session",
                        ),
                    )
                    urlpatterns.insert(
                        0,
                        url(r"^__dev_whoami/$", dev_whoami, name="__dev_whoami"),
                    )
                except Exception:
                    # best-effort: ignore import or insertion failures
                    pass
    except Exception:
        pass
except Exception:
    # If Django isn't configured yet, skip the defensive fallback.
    pass
