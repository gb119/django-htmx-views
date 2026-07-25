HTMX-aware class-based views
============================

Importing :mod:`htmx_views.views` installs the existing HTMX-aware dispatch
hook on Django's base :class:`django.views.View`. Non-HTMX requests continue
through the original Django dispatch method.

Routing requests
----------------

Combine :class:`htmx_views.views.HTMXProcessMixin` with a Django class-based
view:

.. code-block:: python

   from django.http import HttpResponse
   from django.views.generic import TemplateView

   from htmx_views.views import HTMXProcessMixin


   class ResultsView(HTMXProcessMixin, TemplateView):
       template_name = "results/page.html"
       template_name_results = "results/_table.html"

       def htmx_get_refresh(self, request, *args, **kwargs):
           return HttpResponse("refreshed")

For an HTMX request, the mixin examines ``request.htmx.trigger_name``,
``request.htmx.trigger``, and ``request.htmx.target`` in that order. Each value
is lowercased and stripped of characters other than letters, numbers, and
underscores.

An HTMX ``GET`` associated with an element named ``refresh`` first looks for
``htmx_get_refresh``. Equivalent handlers are supported for ``DELETE``,
``PATCH``, ``POST``, and ``PUT``. If no element-specific handler exists, the
ordinary verb handler is used.

Templates and context
---------------------

The same element selection supports:

* ``template_name_<element>`` attributes;
* ``get_template_names_<element>()`` methods;
* ``get_context_data_<element>()`` methods;
* ``context_object_<element>`` attributes; and
* ``get_context_object_name_<element>()`` methods.

Form views
----------

:class:`htmx_views.views.HTMXFormMixin` extends the process mixin with
``htmx_form_valid_<element>()`` and ``htmx_form_invalid_<element>()`` hooks.
It also supports the general ``htmx_form_valid()`` and
``htmx_form_invalid()`` fallbacks.

HTMX form handlers must not recursively call the same mixin handler. They can
return a response directly or use ``super()`` according to the surrounding
Django view's normal form-processing contract.

