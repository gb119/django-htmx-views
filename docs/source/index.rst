django-htmx-views
=================

``django-htmx-views`` provides reusable view mixins and linked-select helpers
for Django applications that use HTMX. It is the standalone successor to the
``apps.htmx_views`` applications in LabMan and PHAS Vitals.

The package supports:

* HTMX-aware dispatch for Django class-based views;
* handlers selected by trigger name, trigger ID, or target ID;
* HTMX-specific templates and context data;
* HTMX-aware form validation handlers; and
* optional linked selects backed by ``django-ajax-selects``.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   views
   linked-selects
   api

