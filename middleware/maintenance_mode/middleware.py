# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import resolve, reverse, NoReverseMatch
from maintenance_mode import core, settings


class MaintenanceModeMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if settings.MAINTENANCE_MODE or core.get_maintenance_mode():
            url_off = reverse("maintenance_mode_off")

            try:
                resolve(url_off)

                if url_off == request.path_info:
                    return None

            except NoReverseMatch:
                # maintenance_mode.urls not added
                pass

            if hasattr(request, "user"):
                if settings.MAINTENANCE_MODE_IGNORE_STAFF and request.user.is_staff:
                    return None

                if (
                    settings.MAINTENANCE_MODE_IGNORE_SUPERUSER
                    and request.user.is_superuser
                ):
                    return None

            for ip_address_re in settings.MAINTENANCE_MODE_IGNORE_IP_ADDRESSES_RE:
                if ip_address_re.match(request.META["REMOTE_ADDR"]):
                    return None

            for url_re in settings.MAINTENANCE_MODE_IGNORE_URLS_RE:
                if url_re.match(request.path_info):
                    return None

            if settings.MAINTENANCE_MODE_REDIRECT_URL:
                return HttpResponseRedirect(settings.MAINTENANCE_MODE_REDIRECT_URL)
            else:
                return render(
                    request,
                    settings.MAINTENANCE_MODE_TEMPLATE,
                    content_type="text/html",
                )

        else:
            return response

    # Process Request does not appear to be used any more as of DJango 1.10
    def process_request(self, request):
        if settings.MAINTENANCE_MODE or core.get_maintenance_mode():
            url_off = reverse("maintenance_mode_off")

            try:
                resolve(url_off)

                if url_off == request.path_info:
                    return None

            except NoReverseMatch:
                # maintenance_mode.urls not added
                pass

            if hasattr(request, "user"):
                if settings.MAINTENANCE_MODE_IGNORE_STAFF and request.user.is_staff:
                    return None

                if (
                    settings.MAINTENANCE_MODE_IGNORE_SUPERUSER
                    and request.user.is_superuser
                ):
                    return None

            for ip_address_re in settings.MAINTENANCE_MODE_IGNORE_IP_ADDRESSES_RE:
                if ip_address_re.match(request.META["REMOTE_ADDR"]):
                    return None

            for url_re in settings.MAINTENANCE_MODE_IGNORE_URLS_RE:
                if url_re.match(request.path_info):
                    return None

            if settings.MAINTENANCE_MODE_REDIRECT_URL:
                return HttpResponseRedirect(settings.MAINTENANCE_MODE_REDIRECT_URL)
            else:
                return render(
                    request,
                    settings.MAINTENANCE_MODE_TEMPLATE,
                    content_type="text/html",
                )

        else:
            return None
