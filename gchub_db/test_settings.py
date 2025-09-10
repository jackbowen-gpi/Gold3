"""Minimal test settings that extend the project's settings and fill gaps for CI.
This shim imports the real settings then ensures minimal values for tests to run
locally (database, secret key, essential contrib apps, WORKFLOW_ROOT_DIR).
"""

import os
import sys

# Force the inner package directory and repo root/parent onto sys.path in order
# so imports like `gchub_db.apps.*` and top-level `settings_common` resolve
# consistently when pytest/django calls django.setup().
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_parent = os.path.abspath(os.path.join(repo_root, ".."))
# Prepend repo_root and its parent to sys.path so the inner `gchub_db`
# package is importable as `gchub_db` and not treated as a nested package.
for p in (repo_root, repo_parent):
    if p not in sys.path:
        sys.path.insert(0, p)

from .settings import *  # noqa: F401,F403

# Base dir (inner package) -> project base
BASE_DIR = globals().get(
    "BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Ensure a SECRET_KEY for test runs
if not globals().get("SECRET_KEY"):
    SECRET_KEY = "test-secret-key-please-change"

# Prefer Postgres for test runs when configured via environment variables.
# If TEST_PG_NAME / PG_TEST_DB is present in the environment, force the
# test configuration to use that Postgres instance. This intentionally
# overrides any DATABASES imported from the project's normal settings so
# CI can safely point tests at an ephemeral Postgres service started by the
# workflow.
TEST_PG_NAME = os.environ.get("TEST_PG_NAME") or os.environ.get("PG_TEST_DB")
TEST_PG_USER = os.environ.get("TEST_PG_USER") or os.environ.get("PG_TEST_USER")
TEST_PG_PASSWORD = os.environ.get("TEST_PG_PASSWORD") or os.environ.get(
    "PG_TEST_PASSWORD"
)
TEST_PG_HOST = (
    os.environ.get("TEST_PG_HOST") or os.environ.get("PG_TEST_HOST") or "localhost"
)
TEST_PG_PORT = (
    os.environ.get("TEST_PG_PORT") or os.environ.get("PG_TEST_PORT") or "5432"
)

if TEST_PG_NAME:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": TEST_PG_NAME,
            "USER": TEST_PG_USER or "",
            "PASSWORD": TEST_PG_PASSWORD or "",
            "HOST": TEST_PG_HOST,
            "PORT": TEST_PG_PORT,
            # Let Django create the test database (it will prefix with
            # 'test_' unless TEST.NAME is explicitly provided); we set TEST
            # name only when the caller explicitly requests the same DB name
            # for tests.
            "TEST": {"NAME": TEST_PG_NAME},  # type: ignore[dict-item]
        }
    }
else:
    # No explicit test DB provided via env vars. If the project already
    # defines DATABASES in its settings we leave that in place; otherwise
    # tests will surface a clear error rather than silently creating a
    # sqlite DB file.
    pass

# Ensure essential contrib apps are present (ContentType & Sites needed by many apps/tests)
essential = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
]
# For pytest runs, keep INSTALLED_APPS minimal to avoid importing many legacy
# apps that require extra environment. We still include the workflow app so its
# tests can run.
minimal_apps = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.admin",
    # Add small set of legacy apps that workflow imports at module import-time
    # so django.setup() can import their models without raising runtime errors.
    "gchub_db.apps.fedexsys",
    "gchub_db.apps.address",
    "gchub_db.apps.color_mgt",
    "gchub_db.apps.item_catalog",
    "gchub_db.apps.joblog",
    "gchub_db.apps.workflow",
]
# By default use the project's INSTALLED_APPS (imported from settings.py) so
# django.setup() can import all app models cleanly. If a caller wants to force
# a smaller test-only set, set __TESTING_OVERRIDE__ = True and define
# INSTALLED_APPS before importing this module.
if globals().get("__TESTING_OVERRIDE__"):
    # Caller explicitly opted in to override; respect their INSTALLED_APPS.
    INSTALLED_APPS = list(globals().get("INSTALLED_APPS", minimal_apps))
else:
    # Use the full INSTALLED_APPS from the real settings (if present),
    # otherwise fall back to the minimal_apps list.
    INSTALLED_APPS = list(globals().get("INSTALLED_APPS", minimal_apps))

# SITE_ID required by django.contrib.sites
SITE_ID = globals().get("SITE_ID", 1)

# Minimal middleware for tests: exclude project-specific middleware that
# expects runtime objects (threadlocals, maintenance middleware, etc.).
# We force the minimal list here so tests don't execute heavy project
# middleware during request handling. Tests can opt-out by setting
# __TESTING_OVERRIDE__ and defining MIDDLEWARE before importing this file.
if not globals().get("__TESTING_OVERRIDE__"):
    MIDDLEWARE = [
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ]

# Optional diagnostic middleware: when DIAG_RESOLVER=1 the middleware will
# write a resolver state dump at request time to help reproduce ordering issues.
if os.environ.get("DIAG_RESOLVER") == "1":
    # Prepend so it runs early in the request cycle
    MIDDLEWARE = [
        "gchub_db.middleware.diagnostic_resolver_dump.DiagnosticResolverDumpMiddleware"
    ] + MIDDLEWARE

# Make sure WORKFLOW_ROOT_DIR exists and is set
if not globals().get("WORKFLOW_ROOT_DIR"):
    WORKFLOW_ROOT_DIR = os.path.join(BASE_DIR, "workflow_root")
    try:
        os.makedirs(WORKFLOW_ROOT_DIR, exist_ok=True)
    except Exception:
        pass

# Use timezone-aware behavior
USE_TZ = True

# Testing flags
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Silence any email backends
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# During tests, use a small stable URLConf that imports the workflow
# app directly and provides safe fallback names. This avoids import-time
# ordering problems caused by the legacy repo-root `urls.py`.
# Default to the top-level `test_urls` module to avoid ambiguity between
# the repository root and the nested package when Python resolves
# `gchub_db.test_urls` in different sys.path orderings.
ROOT_URLCONF = globals().get("TEST_ROOT_URLCONF", "test_urls")

# If diagnostics are enabled, attempt to force population of the URL resolver
# now and write a small diagnostic file with the result. This helps catch
# import-time failures that would otherwise leave the reverse_dict empty at
# request time.
if os.environ.get("DIAG_RESOLVER") == "1":
    try:
        import traceback

        from django.urls import get_resolver

        resolver = get_resolver(None)
        try:
            # Force population; if any import-time errors occur this will raise
            resolver._populate()
            out_path = os.path.join(BASE_DIR, "resolver_force_populate_ok.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("OK\n")
                try:
                    f.write("reverse keys sample:\n")
                    for k in list(resolver.reverse_dict.keys())[:200]:
                        f.write(repr(k) + "\n")
                except Exception as e:
                    f.write("error listing reverse keys: " + repr(e) + "\n")

            # Also write a structural dump of top-level url_patterns and a
            # small sample of nested resolvers so we can see which includes
            # are present and which subpatterns they contain.
            struct_path = os.path.join(BASE_DIR, "resolver_structure_dump.txt")
            with open(struct_path, "w", encoding="utf-8") as sf:
                sf.write("Top-level url_patterns:\n")
                for i, p in enumerate(resolver.url_patterns):
                    try:
                        sf.write("\n--- PATTERN %d ---\n" % i)
                        sf.write("repr: %s\n" % (repr(p),))
                        sf.write("type: %s\n" % type(p))
                        # name/pattern may not exist on resolvers
                        sf.write("name: %r\n" % getattr(p, "name", None))
                        sf.write("pattern: %r\n" % getattr(p, "pattern", None))
                        # If this is a resolver, list a few subpattern names
                        subp = getattr(p, "url_patterns", None)
                        if subp is not None:
                            sf.write("subpatterns sample (first 20):\n")
                            for sp in list(subp)[:20]:
                                sf.write(
                                    "  -> %r (name=%r)\n"
                                    % (repr(sp), getattr(sp, "name", None))
                                )
                    except Exception as e:
                        sf.write("error dumping pattern %d: %r\n" % (i, e))
        except Exception:
            out_path = os.path.join(BASE_DIR, "resolver_force_populate_error.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
    except Exception:
        # If this diagnostic itself fails, don't crash test settings import.
        pass
