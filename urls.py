"""
URL configuration for Gold3 project.
Delegates to config.urls for the actual URL patterns.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("config.urls")),
]
