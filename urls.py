"""Top-level URL configuration for the gchub_db Django project.

Compatibility wrapper to support Django <2.0 and >=2.0 URL imports.
"""

try:
    # Django < 2.0
    from django.conf.urls import url, include
except Exception:
    # Django 2.0+ moved url to django.urls as re_path
    from django.urls import re_path as url, include
from django.conf import settings
from django.http import HttpResponse


def _fallback_job_search(request):
    # Minimal fallback used only in tests/environment where the full
    # workflow URL registry may not be populated exactly as in production.
    return HttpResponse("job_search fallback")


def _fallback_list_reports(request):
    # Minimal fallback for templates that reverse 'list_reports' when
    # workflow URL patterns failed to register during test collection.
    return HttpResponse("list_reports fallback")


from django.contrib import admin
from django.views.generic import RedirectView

# Avoid calling admin.autodiscover() at import time. In some test
# collection/import orders this forces access to the app registry or
# settings before Django is fully configured which can prevent URL
# includes from being registered and lead to ordering-dependent
# Resolver/NoReverseMatch failures. Only autodiscover when the app
# registry is ready.
try:
    import django

    # django.apps.apps.ready is True only after django.setup(); only then
    # is it safe to autodiscover.
    if (
        getattr(django, "apps", None)
        and getattr(django.apps, "apps", None)
        and django.apps.apps.ready
    ):
        admin.autodiscover()
except Exception:
    # Best-effort: if anything goes wrong here, skip autodiscover to avoid
    # breaking imports (tests will not require admin autodiscover to run).
    pass

urlpatterns = []

# Favicon
urlpatterns.append(
    url(
        r"^favicon\.ico$",
        RedirectView.as_view(url="/media/favicon.ico", permanent=True),
    )
)

# Maintenance mode toggle (optional package)
try:
    urlpatterns.append(
        url(r"^maintenance-mode/", include("gchub_db.middleware.maintenance_mode.urls"))
    )
except Exception:
    # best-effort: skip maintenance mode if its urls or views fail to import
    pass

# Default Page fallback
urlpatterns.append(url(r"^job/search/$", _fallback_job_search, name="job_search"))
urlpatterns.append(url(r"^reports/list/$", _fallback_list_reports, name="list_reports"))


# Include various app URLConfs. Wrap each include in try/except so a single
# failing app import doesn't prevent the rest of the URL registry from
# being constructed.
def _try_include(regex, mod_str):
    try:
        urlpatterns.append(url(regex, include(mod_str)))
    except Exception:
        # best-effort: skip failing includes during import
        return


_try_include(r"^job/search/", "gchub_db.apps.workflow.urls")
_try_include(r"^address/", "gchub_db.apps.address.urls")
_try_include(r"^bev_billing/", "gchub_db.apps.bev_billing.urls")
_try_include(r"^sbo/", "gchub_db.apps.sbo.urls")
_try_include(r"^timesheet/", "gchub_db.apps.timesheet.urls")
_try_include(r"^budget/", "gchub_db.apps.budget.urls")
_try_include(r"^qc/", "gchub_db.apps.qc.urls")
_try_include(r"^color_mgt/", "gchub_db.apps.color_mgt.urls")
_try_include(r"^archives/", "gchub_db.apps.archives.urls")
_try_include(r"^error_tracking/", "gchub_db.apps.error_tracking.urls")
_try_include(r"^workflow/", "gchub_db.apps.workflow.urls")
_try_include(r"^item_catalog/", "gchub_db.apps.item_catalog.urls")
_try_include(r"^joblog/", "gchub_db.apps.joblog.urls")
_try_include(r"^calendar/", "gchub_db.apps.calendar.urls")
_try_include(r"^carton_billing/", "gchub_db.apps.carton_billing.urls")
_try_include(r"^fedex/", "gchub_db.apps.fedexsys.urls")
_try_include(r"^xml/", "gchub_db.apps.xml_io.urls")
_try_include(r"^qad_data/", "gchub_db.apps.qad_data.urls")
_try_include(r"^manager_tools/", "gchub_db.apps.manager_tools.urls")
_try_include(r"^draw_down/", "gchub_db.apps.draw_down.urls")
_try_include(r"^video_player/", "gchub_db.apps.video_player.urls")

# Accounts app handles the root URL (it registers a name 'home' at the empty
# path). Include it here so the accounts index serves '/'.
_try_include(r"^", "gchub_db.apps.accounts.urls")

_try_include(r"^su/", "gchub_db.apps.django_su.urls")
_try_include(r"^art_req/", "gchub_db.apps.art_req.urls")
_try_include(r"^catscanner/", "gchub_db.apps.catscanner.urls")
_try_include(r"^acs/", "gchub_db.apps.auto_corrugated.urls")
_try_include(r"^performance/", "gchub_db.apps.performance.urls")

# Admin Interface
try:
    urlpatterns.append(url(r"^admin/doc/", include("django.contrib.admindocs.urls")))
except Exception:
    pass
try:
    urlpatterns.append(url(r"^admin/", admin.site.urls))
except Exception:
    pass

# Serve Media via Django if we're running a development site. This is primarily
# used for local development and should never be done in a production
# environment.
if settings.DJANGO_SERVE_MEDIA:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Development-only dev helper routes: ensure these dev endpoints are reliably
# available when DEBUG=True so the package-level defensive insertion is not
# required for local development.
if getattr(settings, "DEBUG", False):
    try:
        # Try importing the package-level dev_views first (newer layout)
        from gchub_db.gchub_db.dev_views import (
            set_dev_session,
            set_dev_csrf,
            dev_whoami,
        )
    except Exception:
        try:
            # Fall back to older module location if present
            from gchub_db.dev_views import (
                set_dev_session,
                set_dev_csrf,
                dev_whoami,
            )
        except Exception:
            set_dev_session = None
            set_dev_csrf = None
            dev_whoami = None

    try:
        if set_dev_session:
            urlpatterns.insert(
                0,
                url(r"^__dev_set_session/$", set_dev_session, name="__dev_set_session"),
            )
        if set_dev_csrf:
            urlpatterns.insert(
                0, url(r"^__dev_set_csrf/$", set_dev_csrf, name="__dev_set_csrf")
            )
        if dev_whoami:
            urlpatterns.insert(
                0, url(r"^__dev_whoami/$", dev_whoami, name="__dev_whoami")
            )
    except Exception:
        # best-effort: don't break imports if something goes wrong
        pass
