"""URL configuration for htmx_views."""

from django.urls import path

from .views import LinkedSelectEndpointView

app_name = "htmx_views"

urlpatterns = [
    path("select/<str:lookup_channel>/", LinkedSelectEndpointView.as_view(), name="select"),
]
