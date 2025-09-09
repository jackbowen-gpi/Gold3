from django.urls import path

from . import views

app_name = "performance"

urlpatterns = [
    path("recent/", views.recent_slow_requests, name="recent_slow_requests"),
]
