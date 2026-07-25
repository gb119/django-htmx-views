Linked selects
==============

Linked-select support is optional and uses registered ``django-ajax-selects``
lookups to populate a :class:`django.forms.Select` through HTMX.

URL configuration
-----------------

Include the package URLs under the ``htmx_views`` namespace:

.. code-block:: python

   from django.urls import include, path

   urlpatterns = [
       path(
           "htmx-views/",
           include(("htmx_views.urls", "htmx_views"), namespace="htmx_views"),
       ),
   ]

Widget usage
------------

Use :class:`htmx_views.widgets.HTMXSelectWidget` with a registered lookup:

.. code-block:: python

   from django import forms

   from htmx_views.widgets import HTMXSelectWidget


   class EquipmentForm(forms.Form):
       module = forms.ModelChoiceField(queryset=...)
       category = forms.ModelChoiceField(
           queryset=...,
           widget=HTMXSelectWidget("categories", parent="module"),
       )

If ``parent`` is omitted, the widget uses the lookup's ``parameter_name``.
The endpoint passes the selected parent value to the lookup and renders the
returned objects as escaped ``<option>`` elements.

Authorisation
-------------

The endpoint calls the lookup's ``check_auth(request)`` method before running
its query. Unknown lookup channels return HTTP 404, while permission failures
retain Django's normal HTTP 403 handling.

Importing linked-select modules without ``django-ajax-selects`` raises an
actionable :class:`ImportError`. The core view mixins remain importable without
the optional dependency.

