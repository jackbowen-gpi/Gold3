from django.urls import include
from django.urls import re_path as url
from django.utils.module_loading import import_string


def lazy_view(dotted_path):
    """Return a callable that imports and calls the real view on demand.

    This avoids importing the view module at URLConf import time which can
    trigger database access or AppRegistry lookups during startup.
    """

    module_name, func_name = dotted_path.rsplit(".", 1)

    def _view(request, *args, **kwargs):
        # Try normal import first
        try:
            view = import_string(dotted_path)
            return view(request, *args, **kwargs)
        except Exception:
            # If the imported module was actually a package (e.g. a
            # `views/` package) it may not expose the attribute even
            # though a sibling `views.py` file exists. Try to locate and
            # load that file directly.
            try:
                import importlib.util
                import os

                spec = None
                try:
                    spec = importlib.util.find_spec(module_name)
                except Exception:
                    spec = None

                if spec and spec.origin and spec.origin.endswith("__init__.py"):
                    # views package path -> sibling file is the __init__.py's parent
                    pkg_init = spec.origin
                    views_pkg_dir = os.path.dirname(pkg_init)
                    candidate = os.path.join(views_pkg_dir, "..", "views.py")
                    candidate = os.path.normpath(candidate)
                    if os.path.exists(candidate):
                        loader_name = module_name + "_file"
                        spec2 = importlib.util.spec_from_file_location(
                            loader_name, candidate
                        )
                        mod2 = importlib.util.module_from_spec(spec2)
                        spec2.loader.exec_module(mod2)
                        view = getattr(mod2, func_name)
                        return view(request, *args, **kwargs)
            except Exception:
                pass
            # Re-raise the original AttributeError for clarity
            raise

    return _view


urlpatterns = [
    url(r"^$", lazy_view("gchub_db.apps.accounts.views.index"), name="home"),
    url(
        r"^accounts/wiki/$",
        lazy_view("gchub_db.apps.accounts.views.add_wiki_quote"),
        name="add_wiki_quote",
    ),
    url(
        r"^accounts/login/$",
        lazy_view("gchub_db.apps.accounts.views.login_form"),
        name="login",
    ),
    url(
        r"^accounts/office_contacts/$",
        lazy_view("gchub_db.apps.accounts.views.office_contacts"),
        name="office_contacts",
    ),
    url(
        r"^accounts/password/change/$",
        lazy_view("gchub_db.apps.accounts.views.change_password"),
        name="password_change",
    ),
    url(
        r"^accounts/preferences/$",
        lazy_view("gchub_db.apps.accounts.views.change_password"),
        name="preferences",
    ),
    url(
        r"^accounts/preferences/contact_info/$",
        lazy_view("gchub_db.apps.accounts.views.preferences_contact_info"),
        name="preferences_contact_info",
    ),
    url(
        r"^accounts/preferences/settings/$",
        lazy_view("gchub_db.apps.accounts.views.preferences_settings"),
        name="preferences_settings",
    ),
    url(
        r"^accounts/test-notifications/$",
        lazy_view("gchub_db.apps.accounts.views.notification_test_page"),
        name="notification_test_page",
    ),
    url(
        r"^accounts/test-notification/$",
        lazy_view("gchub_db.apps.accounts.views.test_notification"),
        name="test_notification",
    ),
    url(
        r"^admin/send-alert/$",
        lazy_view("gchub_db.apps.accounts.admin_views.send_alert_view"),
        name="admin_send_alert",
    ),
    url(r"^accounts/", include("django.contrib.auth.urls")),
]
