from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import RequestFactory

from htmx_views.views import LinkedSelectEndpointView, dispatch, temp_attr
from htmx_views.widgets import HTMXSelectWidget


class DummyQuerySet(list):
    def distinct(self):
        return self


class DummyItem:
    def __init__(self, pk, label):
        self.pk = pk
        self.label = label

    def __str__(self):
        return self.label


def test_temp_attr_restores_original_value():
    obj = SimpleNamespace(flag="original")
    with temp_attr(obj, "flag", "temporary"):
        assert obj.flag == "temporary"
    assert obj.flag == "original"


def test_dispatch_uses_htmx_handler_for_htmx_requests():
    view = MagicMock()
    view.http_method_names = ["get"]
    view.htmx_http_method_names = ["get"]
    request = MagicMock(method="GET", htmx=SimpleNamespace())

    dispatch(view, request)

    view.htmx_get.assert_called_once_with(request)


def test_htmx_select_widget_sets_htmx_attributes(monkeypatch):
    lookup = SimpleNamespace(parameter_name="parent")
    monkeypatch.setattr("htmx_views.widgets.registry.get", lambda _: lookup)

    widget = HTMXSelectWidget("channels")

    assert "_htmx_parent=parent" in str(widget.attrs["hx-get"])
    assert widget.attrs["hx-trigger"] == "change from:#id_parent"
    assert widget.attrs["hx-include"] == "#id_parent"


def test_htmx_select_widget_requires_parent_when_lookup_has_none(monkeypatch):
    lookup = SimpleNamespace(parameter_name=None)
    monkeypatch.setattr("htmx_views.widgets.registry.get", lambda _: lookup)

    with pytest.raises(ImproperlyConfigured):
        HTMXSelectWidget("channels")


def test_linked_select_endpoint_builds_options(monkeypatch):
    class Lookup:
        parameter_name = "module"

        @staticmethod
        def check_auth(request):
            return None

        @staticmethod
        def get_query(query, request):
            assert query == 12
            return DummyQuerySet([DummyItem(1, "One"), DummyItem(2, "Two")])

    monkeypatch.setattr("htmx_views.views.registry.get", lambda _: Lookup)
    rf = RequestFactory()
    request = rf.get("/select/channels/?module=12")

    response = LinkedSelectEndpointView.as_view()(request, lookup_channel="channels")

    assert response.status_code == 200
    content = response.render().content.decode()
    assert '<option value="1">One</option>' in content
    assert '<option value="2">Two</option>' in content


def test_dispatch_non_htmx_uses_original_dispatch():
    class StubView:
        http_method_names = ["get"]

        def _non_htmx_dispatch(self, request, *args, **kwargs):
            return HttpResponse("non-htmx")

    request = MagicMock(method="GET", htmx=False)
    response = dispatch(StubView(), request)
    assert response.content == b"non-htmx"
