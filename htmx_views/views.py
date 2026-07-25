"""HTMX-aware view helpers and linked-select endpoint."""

import logging
import re
from contextlib import contextmanager

from ajax_select import registry
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.views import View
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


@contextmanager
def temp_attr(obj, attr, value):
    """Temporarily set an attribute and restore original state afterwards."""

    has_attr = hasattr(obj, attr)
    original_value = getattr(obj, attr, None)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        if has_attr:
            setattr(obj, attr, original_value)
        else:
            delattr(obj, attr)


def dispatch(self, request, *args, **kwargs):
    """Dispatch method patched onto View to support HTMX verb handlers."""

    if not getattr(request, "htmx", False):
        return self._non_htmx_dispatch(request, *args, **kwargs)

    allowed_names = getattr(self, "htmx_http_method_names", self.http_method_names)
    if request.method.lower() in allowed_names:
        handler = getattr(self, f"htmx_{request.method.lower()}", getattr(self, request.method.lower(), self.http_method_not_allowed))
    else:
        handler = self.http_method_not_allowed
    if not callable(handler):
        handler = self.http_method_not_allowed
    return handler(request, *args, **kwargs)


class HTMXProcessMixin:
    """Mixin to route HTMX requests and rendering by trigger/target."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._htmx_get_context_data = False
        self._htmx_get_context_object_name = False
        self._htmx_get_template_names = False

    def htmx_elements(self):
        for attr in ["trigger_name", "trigger", "target"]:
            if elem := getattr(self.request.htmx, attr, None):
                elem = re.sub(r"[^A-Za-z0-9_]", "", elem).lower()
                if settings.DEBUG:
                    logger.debug(elem)
                yield elem

    def get_context_data(self, **kwargs):
        if not getattr(self.request, "htmx", False) or self._htmx_get_context_data:
            return super().get_context_data(**kwargs)

        handler = self.get_context_data_function(**kwargs)
        if handler is not None:
            with temp_attr(self, "_htmx_get_context_data", True):
                return handler(**kwargs)
        return super().get_context_data(**kwargs)

    def get_context_data_function(self, **kwargs):
        del kwargs
        for elem in self.htmx_elements():
            handler = getattr(self, f"get_context_data_{elem}", None)
            if callable(handler):
                return handler
        return None

    def get_context_object_name(self, object_list):
        if not getattr(self.request, "htmx", False) or self._htmx_get_context_object_name:
            return super().get_context_object_name(object_list)

        for elem in self.htmx_elements():
            for handler_name in (f"get_context_object_name_{elem}", f"get_context_object_name{elem}"):
                if callable(handler := getattr(self, handler_name, None)):
                    with temp_attr(self, "_htmx_get_context_object_name", True):
                        return handler(object_list)
            if sub_name := getattr(self, f"context_object_{elem}", False):
                return sub_name

        return super().get_context_object_name(object_list)

    def get_template_names(self):
        if not getattr(self.request, "htmx", False) or self._htmx_get_template_names:
            return super().get_template_names()

        for elem in self.htmx_elements():
            handler = getattr(self, f"get_template_names_{elem}", None)
            if callable(handler):
                with temp_attr(self, "_htmx_get_template_names", True):
                    return handler()
            sub_name = getattr(self, f"template_name_{elem}", False)
            if sub_name:
                return sub_name
        return super().get_template_names()

    def _dispatch_to_verb_element_handler(self, verb, request, *args, **kwargs):
        for elem in self.htmx_elements():
            handler = getattr(self, f"htmx_{verb}_{elem}", None)
            if callable(handler):
                break
        else:
            handler = getattr(self, verb, self.http_method_not_allowed)
        if not callable(handler):
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

    def htmx_delete(self, request, *args, **kwargs):
        return self._dispatch_to_verb_element_handler("delete", request, *args, **kwargs)

    def htmx_get(self, request, *args, **kwargs):
        return self._dispatch_to_verb_element_handler("get", request, *args, **kwargs)

    def htmx_patch(self, request, *args, **kwargs):
        return self._dispatch_to_verb_element_handler("patch", request, *args, **kwargs)

    def htmx_post(self, request, *args, **kwargs):
        return self._dispatch_to_verb_element_handler("post", request, *args, **kwargs)

    def htmx_put(self, request, *args, **kwargs):
        return self._dispatch_to_verb_element_handler("put", request, *args, **kwargs)


class HTMXFormMixin(HTMXProcessMixin):
    """Mixin to route form_valid/form_invalid for HTMX by trigger."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._htmx_form_valid = False
        self._htmx_form_invalid = False

    def form_valid(self, form):
        if not getattr(self.request, "htmx", False) or self._htmx_form_valid:
            return super().form_valid(form)
        for elem in self.htmx_elements():
            handler = getattr(self, f"htmx_form_valid_{elem}", None)
            if callable(handler):
                with temp_attr(self, "_htmx_form_valid", True):
                    return handler(form)
        if callable(handler := getattr(self, "htmx_form_valid", None)):
            with temp_attr(self, "_htmx_form_valid", True):
                return handler(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        if not getattr(self.request, "htmx", False) or self._htmx_form_invalid:
            return super().form_invalid(form)

        for elem in self.htmx_elements():
            handler = getattr(self, f"htmx_form_invalid_{elem}", None)
            if callable(handler):
                with temp_attr(self, "_htmx_form_invalid", True):
                    return handler(form)
        if callable(handler := getattr(self, "htmx_form_invalid", None)):
            with temp_attr(self, "_htmx_form_invalid", True):
                return handler(form)
        return super().form_invalid(form)


class LinkedSelectEndpointView(TemplateView):
    """Template endpoint that renders linked options for a registered lookup."""

    http_method_names = ["get", "head", "options"]
    template_name = "htmx_views/widgets/options.html"

    def dispatch(self, request, *args, **kwargs):
        self.lookup_channel = kwargs.get("lookup_channel")
        try:
            self.lookup = registry.get(self.lookup_channel)
        except ImproperlyConfigured as error:
            raise Http404("Unknown linked-select lookup channel.") from error

        self.lookup.check_auth(request)
        self.parent = request.GET.get("_htmx_parent") or getattr(self.lookup, "parameter_name", None)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if self.parent is None:
            raise ImproperlyConfigured(
                f"Creating an htmx_views widget for {self.lookup_channel} without knowing the trigger."
            )

        query = self.request.GET.get(self.parent)
        try:
            query = int(query)
        except (TypeError, ValueError):
            pass

        context = super().get_context_data(**kwargs)
        context["options"] = []
        if query:
            context["options"] = [
                (item.pk, str(item)) for item in self.lookup.get_query(query, self.request).distinct()
            ]
        return context


def _install_htmx_dispatch(view_class=View):
    if not hasattr(view_class, "_non_htmx_dispatch"):
        setattr(view_class, "_non_htmx_dispatch", view_class.dispatch)
    setattr(view_class, "dispatch", dispatch)


_install_htmx_dispatch()
