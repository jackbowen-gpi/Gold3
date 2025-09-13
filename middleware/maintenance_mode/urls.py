# -*- coding: utf-8 -*-

from django.urls import re_path

# The maintenance_mode package is optional. If it's not installed, expose no
# URL patterns so importing the top-level URLConf doesn't fail during startup.
try:
    from gchub_db.middleware.maintenance_mode.views import (
        maintenance_mode_off,
        maintenance_mode_on,
    )

    urlpatterns = [
        re_path(r"^off/$", maintenance_mode_off, name="maintenance_mode_off"),
        re_path(r"^on/$", maintenance_mode_on, name="maintenance_mode_on"),
    ]
except Exception:
    urlpatterns = []
