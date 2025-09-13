"""
Middleware for optimizing static file serving with proper caching headers.
"""

import re
from django.conf import settings


class StaticFileCacheMiddleware:
    """
    Middleware to add proper caching headers to static files.
    This improves performance by allowing browsers and CDNs to cache static assets effectively.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Compile regex pattern for static file URLs
        static_url = getattr(settings, "STATIC_URL", "/static/")
        # Remove leading/trailing slashes for pattern matching
        static_pattern = static_url.strip("/")
        self.static_pattern = re.compile(rf"^/{static_pattern}/")

    def __call__(self, request):
        response = self.get_response(request)

        # Only apply to static file requests
        if self._is_static_file_request(request):
            self._add_cache_headers(response)

        return response

    def _is_static_file_request(self, request):
        """Check if the request is for a static file."""
        return self.static_pattern.match(request.path_info or request.path)

    def _add_cache_headers(self, response):
        """Add appropriate caching headers to static file responses."""
        # Set cache control headers for static files
        cache_timeout = getattr(settings, "STATIC_CACHE_TIMEOUT", 31536000)  # 1 year default

        # Add cache control header
        response["Cache-Control"] = f"public, max-age={cache_timeout}, immutable"

        # Add expires header for older browsers
        from datetime import datetime, timedelta

        expires = datetime.utcnow() + timedelta(seconds=cache_timeout)
        response["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # Add ETag if not present (for cache validation)
        if not response.get("ETag") and hasattr(response, "content"):
            import hashlib

            content_hash = hashlib.md5(response.content).hexdigest()
            response["ETag"] = f'"{content_hash}"'

        # Add Last-Modified if not present
        if not response.get("Last-Modified"):
            from django.utils.http import http_date

            response["Last-Modified"] = http_date()

        # Enable gzip compression if supported
        if getattr(settings, "STATICFILES_USE_GZIP", True):
            response["Vary"] = "Accept-Encoding"
            if "gzip" in response.get("Content-Encoding", ""):
                response["Content-Encoding"] = "gzip"
