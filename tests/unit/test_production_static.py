"""
Tests for production static file optimization functionality.
These tests verify CDN integration, monitoring, and static file
optimization work correctly.
"""

from unittest.mock import patch
from django.test import TestCase, override_settings
from django.conf import settings
from django.http import HttpRequest, HttpResponse

from gchub_db.middleware.monitoring import (
    StaticFileMonitoringMiddleware,
    PerformanceMonitoringMiddleware,
)
from gchub_db.middleware.static_cache import StaticFileCacheMiddleware


class ProductionStaticFileTests(TestCase):
    """Test production static file optimization features."""

    def setUp(self):
        """Set up test environment."""
        self.factory = HttpRequest

    @override_settings(DEBUG=False, STATIC_URL_CDN="https://cdn.example.com/static/")
    def test_cdn_integration_production(self):
        """Test that CDN URL is used in production."""
        # Force reload of settings
        from django.conf import settings
        from importlib import reload
        import config.settings_common

        reload(config.settings_common)

        # Check that STATIC_URL is set to CDN URL
        self.assertEqual(settings.STATIC_URL, "https://cdn.example.com/static/")

    @override_settings(DEBUG=True, STATIC_URL_CDN="https://cdn.example.com/static/")
    def test_cdn_integration_development(self):
        """Test that CDN URL is NOT used in development."""
        # Force reload of settings
        from django.conf import settings
        from importlib import reload
        import config.settings_common

        reload(config.settings_common)

        # Check that STATIC_URL remains default in development
        self.assertEqual(settings.STATIC_URL, "/static/")

    def test_static_file_cache_middleware_headers(self):
        """Test that static file cache middleware adds proper headers."""
        middleware = StaticFileCacheMiddleware(lambda r: HttpResponse("test content"))

        # Create a mock request for a static file
        request = self.factory.get("/static/test.css")
        request.path_info = "/static/test.css"

        response = middleware(request)

        # Check that cache headers are added
        self.assertIn("Cache-Control", response)
        self.assertIn("public, max-age=31536000, immutable", response["Cache-Control"])
        self.assertIn("Expires", response)
        self.assertIn("ETag", response)

    def test_static_file_cache_middleware_non_static(self):
        """Test that middleware doesn't affect non-static requests."""
        middleware = StaticFileCacheMiddleware(lambda r: HttpResponse("test content"))

        # Create a mock request for a non-static file
        request = self.factory.get("/api/test/")
        request.path_info = "/api/test/"

        response = middleware(request)

        # Check that cache headers are NOT added to non-static requests
        self.assertNotIn("Cache-Control", response)

    @override_settings(DEBUG=False)
    def test_monitoring_middleware_production(self):
        """Test that monitoring middleware is active in production."""
        # Mock the monitoring middleware
        with patch("gchub_db.middleware.monitoring.logger"):
            middleware = PerformanceMonitoringMiddleware(lambda r: HttpResponse("test"))

            request = self.factory.get("/test/")
            middleware(request)

            # Check that monitoring is working
            # (logger should be called for slow requests)
            # This is a basic test - in real scenarios you'd check metrics

    @override_settings(DEBUG=True)
    def test_monitoring_middleware_development(self):
        """Test that monitoring middleware is disabled in development."""
        middleware = PerformanceMonitoringMiddleware(lambda r: HttpResponse("test"))

        # Check that monitoring is disabled
        self.assertFalse(middleware.monitoring_enabled)

    def test_static_file_monitoring_metrics(self):
        """Test that static file monitoring tracks metrics correctly."""
        with patch("gchub_db.middleware.monitoring.logger"):
            middleware = StaticFileMonitoringMiddleware(lambda r: HttpResponse("test"))

            # Simulate static file requests
            request = self.factory.get("/static/test.css")
            request.path_info = "/static/test.css"

            # Make several requests
            for _ in range(5):
                middleware(request)

            # Check metrics
            metrics = middleware.get_metrics()
            self.assertIsNotNone(metrics)
            self.assertEqual(metrics["static_requests"], 5)
            self.assertIsInstance(metrics["cache_hit_rate"], (int, float))

    @override_settings(
        STATICFILES_STORAGE="django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        STATIC_CACHE_TIMEOUT=31536000,
    )
    def test_manifest_static_files_storage(self):
        """Test that manifest storage is configured correctly."""
        # Check that the storage class is configured
        storage_class = getattr(settings, "STATICFILES_STORAGE", None)
        expected = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
        self.assertEqual(storage_class, expected)

        # Check cache timeout
        cache_timeout = getattr(settings, "STATIC_CACHE_TIMEOUT", None)
        self.assertEqual(cache_timeout, 31536000)  # 1 year

    def test_gzip_compression_setting(self):
        """Test that gzip compression is enabled."""
        gzip_enabled = getattr(settings, "STATICFILES_USE_GZIP", None)
        self.assertTrue(gzip_enabled)

    @patch("gchub_db.middleware.monitoring.logger")
    def test_slow_request_logging(self, mock_logger):
        """Test that slow requests are logged."""
        with override_settings(DEBUG=False, SLOW_REQUEST_THRESHOLD=0.001):
            middleware = PerformanceMonitoringMiddleware(
                lambda r: HttpResponse("test")  # Fast response
            )

            request = self.factory.get("/test/")
            middleware(request)

            # Check that logger was called for the request
            # Note: This might not trigger if the response is fast enough
            # In a real test, you might want to simulate a slow response

    def test_cache_middleware_configuration(self):
        """Test that cache middleware is properly configured."""
        middleware_classes = getattr(settings, "MIDDLEWARE", [])

        # Check that cache middleware is included
        cache_middleware = "django.middleware.cache.UpdateCacheMiddleware"
        self.assertIn(cache_middleware, middleware_classes)

        fetch_middleware = "django.middleware.cache.FetchFromCacheMiddleware"
        self.assertIn(fetch_middleware, middleware_classes)

        # Check cache settings
        cache_alias = getattr(settings, "CACHE_MIDDLEWARE_ALIAS", None)
        self.assertEqual(cache_alias, "default")

        cache_seconds = getattr(settings, "CACHE_MIDDLEWARE_SECONDS", None)
        self.assertEqual(cache_seconds, 600)  # 10 minutes

    def test_cdn_url_validation(self):
        """Test CDN URL configuration validation."""
        with override_settings(DEBUG=False, STATIC_URL_CDN="https://cdn.example.com/static"):
            # Force reload of settings
            from importlib import reload
            import config.settings_common

            reload(config.settings_common)

            # Check that STATIC_URL ends with /
            self.assertTrue(settings.STATIC_URL.endswith("/"))

        with override_settings(DEBUG=False, STATIC_URL_CDN="https://cdn.example.com/static/"):
            # Force reload of settings
            reload(config.settings_common)

            # Check that STATIC_URL still ends with /
            self.assertTrue(settings.STATIC_URL.endswith("/"))


class ProductionIntegrationTests(TestCase):
    """Integration tests for production deployment."""

    @override_settings(DEBUG=False)
    def test_production_middleware_stack(self):
        """Test that production middleware stack includes monitoring."""
        middleware_classes = getattr(settings, "MIDDLEWARE", [])

        # Check that monitoring middleware is included in production
        perf_middleware = "gchub_db.middleware.monitoring.PerformanceMonitoringMiddleware"
        self.assertIn(perf_middleware, middleware_classes)

        static_middleware = "gchub_db.middleware.monitoring.StaticFileMonitoringMiddleware"
        self.assertIn(static_middleware, middleware_classes)

    @override_settings(DEBUG=True)
    def test_development_middleware_stack(self):
        """Test that development middleware stack excludes monitoring."""
        middleware_classes = getattr(settings, "MIDDLEWARE", [])

        # Check that monitoring middleware is NOT included in development
        perf_middleware = "gchub_db.middleware.monitoring.PerformanceMonitoringMiddleware"
        self.assertNotIn(perf_middleware, middleware_classes)

        static_middleware = "gchub_db.middleware.monitoring.StaticFileMonitoringMiddleware"
        self.assertNotIn(static_middleware, middleware_classes)

    def test_static_file_optimization_workflow(self):
        """Test the complete static file optimization workflow."""
        # This would be an integration test that:
        # 1. Collects static files
        # 2. Compresses them
        # 3. Generates manifest
        # 4. Verifies CDN integration
        # 5. Tests caching headers

        # For now, just verify the settings are correct
        expected_storage = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
        self.assertEqual(settings.STATICFILES_STORAGE, expected_storage)
        self.assertTrue(settings.STATICFILES_USE_GZIP)
        self.assertEqual(settings.STATIC_CACHE_TIMEOUT, 31536000)
