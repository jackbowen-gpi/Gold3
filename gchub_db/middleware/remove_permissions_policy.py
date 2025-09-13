"""
Development middleware to remove restrictive Permissions-Policy/Feature-Policy
headers so legacy vendor scripts that register "unload" handlers continue to work
when running with DEBUG=True.

This is intentionally minimal and only intended for development use. Do NOT enable
in production.
"""

from typing import Callable


class RemovePermissionsPolicyHeaderMiddleware:
    """
    Remove Permissions-Policy and Feature-Policy response headers.

    Many older libraries (Prototype, YUI, SWF helpers) register `unload` event
    handlers. Newer browsers may block those handlers unless the document's
    Permissions-Policy allows them. During local development we prefer to remove
    restrictive headers so the app behaves like older deployments.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Remove both canonical and legacy header names if present.
        for header in ("Permissions-Policy", "Feature-Policy"):
            try:
                if header in response:
                    del response[header]
            except Exception:
                # Some response-like objects expose headers differently; ignore
                # failures since this middleware is only for DEBUG convenience.
                pass

        return response
