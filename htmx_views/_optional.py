"""Helpers for optional HTMX views integrations."""

# Python imports
from importlib import import_module


def get_ajax_select_registry():
    """Return the ajax-select registry or explain how to enable linked selects."""
    try:
        ajax_select = import_module("ajax_select")
    except ModuleNotFoundError as error:
        if error.name != "ajax_select":
            raise
        raise ImportError(
            "Linked-select support requires the optional dependency "
            "'django-ajax-selects'. Install it before importing "
            "'htmx_views.widgets' or 'htmx_views.urls'."
        ) from error
    return ajax_select.registry


def get_bootstrap5_render_button():
    """Return the optional django-bootstrap5 button renderer."""
    try:
        components = import_module("django_bootstrap5.components")
    except ModuleNotFoundError as error:
        if error.name != "django_bootstrap5":
            raise
        raise ImportError(
            "Bootstrap template components require the optional dependency "
            "'django-bootstrap5'. Install 'django-htmx-views[bootstrap5]' "
            "before loading 'htmx_views_bootstrap'."
        ) from error
    return components.render_button
