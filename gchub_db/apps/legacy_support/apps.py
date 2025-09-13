from django.apps import AppConfig


class LegacySupportConfig(AppConfig):
    name = "gchub_db.apps.legacy_support"
    verbose_name = "Legacy support helpers"

    def ready(self):
        # Import legacy template tags to ensure they are registered with the
        # template engine during app initialization. This keeps templates using
        # legacy tags working without requiring explicit {% load %} in every file.
        try:
            import importlib

            importlib.import_module("gchub_db.templatetags.legacy_tags")
        except Exception:
            # Swallow exceptions here; if the import fails the template builtins
            # entry should still help, and we prefer Django to surface errors
            # later in a normal stacktrace.
            pass
