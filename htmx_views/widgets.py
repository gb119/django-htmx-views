"""HTMX-backed select widgets."""

from urllib.parse import urlencode

from ajax_select import registry
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import Select
from django.urls import reverse_lazy
from django.utils.text import format_lazy


class HTMXSelectWidget(Select):
    """Update select options based on another field via HTMX."""

    def __init__(self, lookup_channel, parent=None, *args, **kwargs):
        try:
            self.lookup = registry.get(lookup_channel)
        except ImproperlyConfigured as error:
            raise ImproperlyConfigured(
                f"Attempting to use a htmx_views widget with lookup channel {lookup_channel} that does not exist."
            ) from error

        self.lookup_channel = lookup_channel
        if parent is None:
            parent = getattr(self.lookup, "parameter_name", None)
        if parent is None:
            raise ImproperlyConfigured(
                f"Creating an htmx_views widget for {lookup_channel} without knowing the trigger."
            )

        self.parent_name = parent
        endpoint = reverse_lazy("htmx_views:select", args=(self.lookup_channel,))
        query_string = urlencode({"_htmx_parent": self.parent_name})
        attrs = dict(kwargs.pop("attrs", {}))
        attrs.update(
            {
                "hx-get": format_lazy("{}?{}", endpoint, query_string),
                "hx-trigger": f"change from:#id_{self.parent_name}",
                "hx-include": f"#id_{self.parent_name}",
            }
        )
        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        attrs = dict(attrs or {})
        attrs["hx-target"] = f"#id_{name}"
        return super().get_context(name, value, attrs)
