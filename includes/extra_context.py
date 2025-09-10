"""These are extra context processors that add extra things to the global
template context. Make -sure- not to add anything here unless it's absolutely
necessary, anything here is used on every single page load. This can cause
severe performance degradation in the case of a query.
"""

from django.conf import settings


def common_urls(request):
    """Populates some other common URLs."""
    return {
        "YUI_URL": settings.YUI_URL,
        # This is the URL to the downloader instance of Thundercuddles.
        "DLOADER_URL": settings.DLOADER_URL,
        "EMAIL_SUPPORT": settings.EMAIL_SUPPORT,
        "EMAIL_GCHUB": settings.EMAIL_GCHUB,
        # Development-only: show all navigation links regardless of permissions.
        # Default to True while developing; set to False in local_settings or env
        # for testing.
        "SHOW_ALL_LINKS": getattr(settings, "DEV_SHOW_ALL_LINKS", True)
        and settings.DEBUG,
    }
