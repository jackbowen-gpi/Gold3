"""
Monitoring middleware for tracking static file performance and cache metrics.
"""

import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class StaticFileMonitoringMiddleware:
    """
    Middleware to monitor static file performance and cache effectiveness.
    Only active in production (when DEBUG=False).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Only enable monitoring in production
        self.monitoring_enabled = not getattr(settings, "DEBUG", True)

        if self.monitoring_enabled:
            # Initialize monitoring counters
            self.cache_hits = 0
            self.cache_misses = 0
            self.static_requests = 0
            self.total_response_time = 0.0

    def __call__(self, request):
        if not self.monitoring_enabled:
            return self.get_response(request)

        start_time = time.time()
        is_static_request = self._is_static_request(request)

        if is_static_request:
            self.static_requests += 1

        # Check if this is a cache hit (for static files)
        cache_hit = self._check_cache_hit(request)

        response = self.get_response(request)
        response_time = time.time() - start_time

        if is_static_request:
            self.total_response_time += response_time

            # Log performance metrics
            self._log_static_performance(request, response, response_time, cache_hit)

            # Update cache metrics
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

        return response

    def _is_static_request(self, request):
        """Check if the request is for a static file."""
        static_url = getattr(settings, "STATIC_URL", "/static/")
        return request.path.startswith(static_url)

    def _check_cache_hit(self, request):
        """Check if this request resulted in a cache hit."""
        # This is a simplified check - in a real implementation you might
        # check response headers or use more sophisticated cache inspection
        return hasattr(request, "_cache_hit") and request._cache_hit

    def _log_static_performance(self, request, response, response_time, cache_hit):
        """Log static file performance metrics."""
        # Only log detailed metrics for slower requests or periodically
        if response_time > 0.1 or self.static_requests % 100 == 0:
            cache_status = "HIT" if cache_hit else "MISS"
            logger.info(
                f"Static file request: {request.path} | "
                f"Response time: {response_time:.3f}s | "
                f"Cache: {cache_status} | "
                f"Status: {response.status_code}"
            )

    def get_metrics(self):
        """Get current monitoring metrics."""
        if not self.monitoring_enabled:
            return None

        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0

        avg_response_time = self.total_response_time / self.static_requests if self.static_requests > 0 else 0

        return {
            "static_requests": self.static_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "avg_response_time": round(avg_response_time, 3),
            "total_response_time": round(self.total_response_time, 3),
        }


class PerformanceMonitoringMiddleware:
    """
    General performance monitoring middleware for all requests.
    Tracks response times and can trigger alerts for slow requests.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.monitoring_enabled = not getattr(settings, "DEBUG", True)
        self.slow_request_threshold = getattr(settings, "SLOW_REQUEST_THRESHOLD", 2.0)  # seconds

        if self.monitoring_enabled:
            self.request_count = 0
            self.slow_requests = 0
            self.total_response_time = 0.0

    def __call__(self, request):
        if not self.monitoring_enabled:
            return self.get_response(request)

        start_time = time.time()
        self.request_count += 1

        response = self.get_response(request)
        response_time = time.time() - start_time

        self.total_response_time += response_time

        # Check for slow requests
        if response_time > self.slow_request_threshold:
            self.slow_requests += 1
            self._log_slow_request(request, response_time)

        # Periodic performance summary
        if self.request_count % 1000 == 0:
            self._log_performance_summary()

        return response

    def _log_slow_request(self, request, response_time):
        """Log slow request for monitoring."""
        logger.warning(
            f"SLOW REQUEST: {request.method} {request.path} | "
            f"Time: {response_time:.3f}s | "
            f"User: {request.user if hasattr(request, 'user') else 'Anonymous'}"
        )

    def _log_performance_summary(self):
        """Log periodic performance summary."""
        avg_response_time = self.total_response_time / self.request_count
        slow_request_percentage = (self.slow_requests / self.request_count) * 100

        logger.info(
            f"PERFORMANCE SUMMARY: {self.request_count} requests | "
            f"Avg response time: {avg_response_time:.3f}s | "
            f"Slow requests: {self.slow_requests} ({slow_request_percentage:.1f}%)"
        )

    def get_metrics(self):
        """Get current performance metrics."""
        if not self.monitoring_enabled:
            return None

        avg_response_time = self.total_response_time / self.request_count if self.request_count > 0 else 0

        return {
            "total_requests": self.request_count,
            "slow_requests": self.slow_requests,
            "avg_response_time": round(avg_response_time, 3),
            "slow_request_percentage": round(
                (self.slow_requests / self.request_count * 100) if self.request_count > 0 else 0,
                2,
            ),
        }
