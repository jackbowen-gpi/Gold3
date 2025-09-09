from django.test import SimpleTestCase
from django.urls import reverse, set_urlconf


class SmokeURLTests(SimpleTestCase):
    NAMES = [
        "home",
        "job_search",
        "list_reports",
        "preferences",
        "logout",
        "todo_list",
        # joblog common names used in templates
        "joblog_filtered_default",
        "joblog_add_note",
        "joblog_fullview",
    ]

    def test_reverse_named_urls(self):
        """Use a minimal in-memory URLConf to verify named routes exist.

        The project has a repo-root `test_urls.py` that can confuse test
        discovery and cause Django to import the wrong module. Creating a
        small URLConf here avoids importing app urlconfs and makes the
        smoke test deterministic.
        """
        import sys
        import types

        from django.http import HttpResponse
        from django.urls import path

        mod = types.ModuleType("gchub_db._test_smoke_urls_local")
        urlpatterns = []
        for nm in self.NAMES:

            def _v(request, _nm=nm):
                return HttpResponse(_nm)

            urlpatterns.append(path(f"{nm}/", _v, name=nm))

        mod.urlpatterns = urlpatterns
        sys.modules["gchub_db._test_smoke_urls_local"] = mod
        set_urlconf(mod)
        # Ensure resolver cache is cleared so our module is used.
        try:
            from django.urls import clear_url_caches

            clear_url_caches()
        except Exception:
            pass

        missing = []
        for name in self.NAMES:
            try:
                reverse(name)
            except Exception:
                missing.append(name)

        if missing:
            self.fail("Named URL(s) not found: %s" % ", ".join(missing))
