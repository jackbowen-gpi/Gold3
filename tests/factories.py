from django.contrib.auth import get_user_model


def create_user(username="testuser", password="password", is_staff=False, **kwargs):
    """Create and return a Django user for tests.

    Keeps things minimal so legacy tests can import `tests.factories.create_user`.
    """
    User = get_user_model()
    user = User.objects.create_user(username=username, password=password, **kwargs)
    user.is_staff = is_staff
    user.save()
    return user


"""Test factories using factory_boy when available.

Expose small helpers `create_site()` and `create_user()` used by tests.
When `factory_boy` is installed we use lightweight `DjangoModelFactory`
factories. Otherwise provide minimal ORM-based fallbacks so tests run
without extra dev dependencies.
"""

import uuid

from django.contrib.sites.models import Site

User = get_user_model()


# Prefer factory_boy when available, but fall back to minimal helpers so tests run
try:
    import factory
    from factory.django import DjangoModelFactory

    class SiteFactory(DjangoModelFactory):
        class Meta:
            model = Site

        domain = factory.LazyAttribute(lambda o: f"site-{uuid.uuid4()}.local")
        name = factory.LazyAttribute(lambda o: f"site-{str(uuid.uuid4())[:6]}")

    class UserFactory(DjangoModelFactory):
        class Meta:
            model = User

        username = factory.LazyAttribute(lambda o: f"user-{uuid.uuid4()}")
        # use PostGenerationMethodCall to set a usable password
        password = factory.PostGenerationMethodCall("set_password", "p")

    def create_site(name_prefix="site", domain=None, name=None, **kwargs):
        # backward-compatible convenience helper using factory_boy
        # If caller supplies explicit domain/name, use them.
        if domain is None:
            domain = f"{name_prefix}-{uuid.uuid4()}.local"
        if name is None:
            # Map common test prefixes to the canonical workflow names used in logic
            name = name_prefix
            if isinstance(name_prefix, str):
                if "food" in name_prefix:
                    name = "Foodservice"
                elif "bev" in name_prefix:
                    name = "Beverage"
                elif "carton" in name_prefix or "icon-cart" in name_prefix:
                    name = "Carton"
                else:
                    # Title-case for nicer defaults
                    name = name_prefix.capitalize()
        return SiteFactory(domain=domain, name=name, **kwargs)

    def create_user(username_prefix="user", username=None, password=None, **kwargs):
        # Accept explicit username/password via kwargs or fall back to prefix
        if username is None:
            username = f"{username_prefix}-{uuid.uuid4()}"
        if password is None:
            # UserFactory uses PostGenerationMethodCall to set password, so pass it here
            return UserFactory(username=username, **kwargs)
        else:
            return UserFactory(username=username, password=password, **kwargs)

except Exception:
    # factory_boy isn't installed / import failed — provide tiny fallbacks so tests still run
    def create_site(name_prefix="site", domain=None, name=None, **kwargs):
        # Allow caller to specify full domain/name via kwargs
        if domain is None:
            domain = f"{name_prefix}-{uuid.uuid4()}.local"
        if name is None:
            name = name_prefix
            if isinstance(name_prefix, str):
                if "food" in name_prefix:
                    name = "Foodservice"
                elif "bev" in name_prefix:
                    name = "Beverage"
                elif "carton" in name_prefix or "icon-cart" in name_prefix:
                    name = "Carton"
                else:
                    name = name_prefix.capitalize()
        return Site.objects.create(domain=domain, name=name, **kwargs)

    def create_user(username_prefix="user", **kwargs):
        # Accept explicit username/password via kwargs or fall back to prefix
        if "username" in kwargs:
            username = kwargs.pop("username")
        else:
            username = f"{username_prefix}-{uuid.uuid4()}"
        password = kwargs.pop("password", "p")
        return User.objects.create_user(username=username, password=password, **kwargs)
