from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "gchub_db.apps.accounts"
    verbose_name = "Accounts"

    def ready(self):
        # Create a developer admin user during local development when DEBUG=True.
        # This runs once when Django initializes the app registry.
        try:
            from django.conf import settings

            if not getattr(settings, "DEBUG", False):
                return

            # Defer DB imports until ready() is called
            from django.contrib.auth import get_user_model
            from django.db import IntegrityError
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType
            from gchub_db.apps.workflow.models import Workflow

            User = get_user_model()

            username = getattr(settings, "DEV_ADMIN_USERNAME", "devtest")
            password = getattr(settings, "DEV_ADMIN_PASSWORD", "devtest")
            email = getattr(settings, "DEV_ADMIN_EMAIL", "devadmin@example.com")

            # Create user if missing
            try:
                user, created = User.objects.get_or_create(username=username, defaults={"email": email})
                if created:
                    user.set_password(password)
                    user.is_active = True
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
            except IntegrityError:
                user = User.objects.filter(username=username).first()

            # Grant broad permissions for all workflows (best-effort).
            try:
                # Some projects use a custom permission set per workflow; try granting
                # all permissions relating to workflow models as a simple approach.
                workflow_ct = ContentType.objects.get_for_model(Workflow)
                perms = Permission.objects.filter(content_type=workflow_ct)
                for p in perms:
                    user.user_permissions.add(p)
            except Exception:
                # best-effort: if workflow model or permissions aren't present,
                # skip granting model-specific perms; superuser already sufficient.
                pass
        except Exception:
            # Don't raise during app registry setup in dev; log would be better,
            # but avoid importing logging here to keep this lightweight.
            pass
