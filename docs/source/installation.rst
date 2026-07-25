Installation
============

Install the core package from PyPI:

.. code-block:: console

   python -m pip install django-htmx-views

Install the optional linked-select integration when it is needed:

.. code-block:: console

   python -m pip install "django-htmx-views[linked-selects]"

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

Migrating an existing application
---------------------------------

#. Install the package and add ``htmx_views`` to ``INSTALLED_APPS``.
#. Replace imports beginning with ``apps.htmx_views`` with ``htmx_views``.
#. Include ``htmx_views.urls`` if the application uses linked selects.
#. Run the consuming application's tests before removing its copied
   ``apps/htmx_views`` directory.
