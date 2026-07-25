from django.urls import include, path

urlpatterns = [
    path("", include(("htmx_views.urls", "htmx_views"), namespace="htmx_views")),
]
