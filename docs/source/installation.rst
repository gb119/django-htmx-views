Installation
============

Install the core package from PyPI:

.. code-block:: console

   python -m pip install django-htmx-views

Install the optional linked-select integration when it is needed:

.. code-block:: console

   python -m pip install "django-htmx-views[linked-selects]"

Install the optional Bootstrap 5 integration, including
``django-bootstrap5``, when using the Bootstrap template components:

.. code-block:: console

   python -m pip install "django-htmx-views[bootstrap5]"

Django settings
---------------

Add the package to ``INSTALLED_APPS`` and enable the ``django-htmx``
middleware:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "htmx_views",
   ]

   MIDDLEWARE = [
       # ...
       "django_htmx.middleware.HtmxMiddleware",
   ]

Add ``"django_bootstrap5"`` to ``INSTALLED_APPS`` as well when using its form,
button, CSS, or JavaScript template tags. The structural tags supplied by
``htmx_views`` do not load Bootstrap assets automatically.

Migrating an existing application
---------------------------------

#. Install the package and add ``htmx_views`` to ``INSTALLED_APPS``.
#. Replace imports beginning with ``apps.htmx_views`` with ``htmx_views``.
#. Include ``htmx_views.urls`` if the application uses linked selects.
#. Run the consuming application's tests before removing its copied
   ``apps/htmx_views`` directory.
