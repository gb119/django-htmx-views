Bootstrap template components
=============================

The optional ``htmx_views_bootstrap`` template-tag library provides Bootstrap
3 button migration helpers and generates the Bootstrap 5 structure and
accessibility attributes needed by common HTMX-powered interfaces.

Install the ``bootstrap5`` extra and add ``django_bootstrap5`` to
``INSTALLED_APPS`` when using the button, form, or asset tags:

.. code-block:: console

   python -m pip install "django-htmx-views[bootstrap5]"

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "django_bootstrap5",
       "htmx_views",
   ]

The components do not load CSS or JavaScript. Include Bootstrap 5 in the page
through ``django-bootstrap5`` or the consuming application's existing asset
pipeline.

Bootstrap 3 button migration
----------------------------

``django-bootstrap5`` retained ``bootstrap_button`` but removed
``bootstrap_icon`` and the ``buttons`` block. Load this library after
``django_bootstrap5`` to add those helpers and extend ``bootstrap_button`` with
the former ``icon`` argument:

.. code-block:: django

   {% load django_bootstrap5 htmx_views_bootstrap %}

   {% bootstrap_icon "info-sign" title="Information" %}
   {% bootstrap_button "Save" button_type="submit" icon="floppy-disk" %}

The loading order is deliberate: ``htmx_views_bootstrap`` registers its
conversion-friendly ``bootstrap_button`` after the original tag. It delegates
the final button rendering to ``django-bootstrap5``, so arguments such as
``button_type``, ``href``, ``name``, and ``extra_classes`` remain available.

The compatibility tag also translates ``btn-default`` to ``btn-secondary``.
The old ``xs``, ``small``, ``medium``, and ``large`` size values become
``sm``, ``sm``, ``md``, and ``lg`` respectively. ``icon_position="end"`` puts
an icon after the content. For example, an accessible icon-only control can
use ``aria_label``:

.. code-block:: django

   {% bootstrap_button "" button_type="button" icon="remove" aria_label="Close" %}

``bootstrap_icon`` uses the separate `Bootstrap Icons
<https://icons.getbootstrap.com/>`_ font rather than Bootstrap 3's removed
Glyphicons. Include Bootstrap Icons through the application's asset pipeline,
or add its stylesheet to the page. Untitled icons are marked decorative with
``aria-hidden="true"``; passing ``title`` gives a standalone icon an accessible
label.

Common legacy names such as ``floppy-disk``, ``info-sign``, ``ok``,
``remove``, and ``warning-sign`` are mapped to their closest Bootstrap Icons
counterparts. Names without an explicit mapping are treated as Bootstrap Icon
names, so existing templates can be migrated incrementally. The
``glyphicon-`` and ``bi-`` prefixes may be omitted.

Button blocks
~~~~~~~~~~~~~

The former ``buttons`` block is available for source-compatible form action
rows:

.. code-block:: django

   {% buttons submit="Save" reset="Cancel" submit_icon="floppy-disk" %}
     <a class="btn btn-link" href="{% url 'documents:list' %}">Back</a>
   {% endbuttons %}

The optional submit and reset buttons are rendered first, followed by nested
content, matching the old tag's ordering. The wrapper defaults to Bootstrap 5
spacing utilities ``mb-3 d-flex flex-wrap gap-2``. Its options are ``submit``,
``reset``, ``submit_class``, ``reset_class``, ``submit_icon``, ``reset_icon``,
``size``, and ``wrapper_class``.

New templates can use the collision-resistant
``bootstrap_buttons``/``endbootstrap_buttons`` names for the same block:

.. code-block:: django

   {% bootstrap_buttons submit="Continue" wrapper_class="d-grid" %}
   {% endbootstrap_buttons %}

The old jQuery loader is intentionally not ported: Bootstrap 5 and HTMX do not
require jQuery.

HTMX modal dialogs
------------------

A modal has two parts: a persistent target in the full page and content
returned by an HTMX view.

Place ``bootstrap_modal_target`` once in the full page:

.. code-block:: django

   {% load htmx_views_bootstrap %}

   {% bootstrap_modal_target size="lg" %}

The defaults match the LabMan convention: the outer modal is ``#modal`` and
HTMX swaps response content into ``#dialog``. Supported keyword arguments are:

``modal_id``
   Outer modal ID. Defaults to ``"modal"``.

``target_id``
   HTMX swap-target ID. Defaults to ``"dialog"``.

``title_id``
   Heading ID used by ``aria-labelledby``. Defaults to ``"dialog-title"``.

``size``
   ``"sm"``, ``"lg"``, ``"xl"``, or an empty value. Defaults to ``"lg"``.

``centred``
   Adds ``modal-dialog-centered`` when true. Defaults to ``True``.

``scrollable``
   Adds ``modal-dialog-scrollable`` when true. Defaults to ``False``.

Return the matching modal content from the HTMX view:

.. code-block:: django

   {% load django_bootstrap5 htmx_views_bootstrap %}

   {{ form.media }}
   {% bootstrap_modal_content title="Manage document" %}
     <form id="document" method="post" hx-post="{{ request.path }}">
       {% csrf_token %}
       {% bootstrap_form form layout="horizontal" %}
       <button type="submit" class="btn btn-primary">Save</button>
     </form>
   {% endbootstrap_modal_content %}

The target ID also selects the backend mixin hooks. For example,
``hx-target="#dialog"`` selects ``template_name_dialog`` for both the initial
``GET`` and an invalid ``POST``:

.. code-block:: python

   from django.http import HttpResponse
   from django.views.generic import CreateView

   from htmx_views.views import HTMXFormMixin

   from .forms import DocumentForm
   from .models import Document


   class DocumentDialogView(HTMXFormMixin, CreateView):
       model = Document
       form_class = DocumentForm
       template_name = "documents/document_form_page.html"
       template_name_dialog = "documents/_document_dialog.html"

       def htmx_form_valid_dialog(self, form):
           self.object = form.save()
           response = HttpResponse(status=204)
           response.headers["HX-Trigger"] = "documentsChanged"
           return response

Use the modal response template shown above as
``documents/_document_dialog.html``. A full page can open it and provide the
persistent target:

.. code-block:: django

   <button hx-get="{% url 'documents:create' %}" hx-target="#dialog">
     Add document
   </button>
   {% bootstrap_modal_target %}

``HTMXFormMixin`` routes a valid submission to
``htmx_form_valid_dialog()``. It must return a response directly rather than
calling ``super().form_valid()``, which would re-enter the mixin handler. The
204 response works with a client-side ``htmx:beforeSwap`` listener that closes
the modal, while ``HX-Trigger`` can refresh the surrounding list.

``bootstrap_modal_content`` accepts these keyword arguments:

``title``
   Required modal heading. Values are escaped according to the template's
   auto-escaping rules.

``target``
   Inherited HTMX target. Defaults to ``"#dialog"``.

``title_id``
   Heading ID. It must match the target's ``title_id``.

``close_button``
   Include the Bootstrap header close button. Defaults to ``True``.

``content_class``, ``header_class``, and ``body_class``
   Additional classes for the respective modal elements.

``hx-target`` is placed on ``.modal-content``. HTMX controls inside it inherit
the target, so forms normally need only their request attribute such as
``hx-post``. Applications still control when to show and hide the modal. For
example, they can listen for ``htmx:afterSwap`` and ``htmx:beforeSwap`` and use
Bootstrap's modal JavaScript API.

Accordions
----------

Use ``bootstrap_accordion`` around one or more
``bootstrap_accordion_item`` blocks:

.. code-block:: django

   {% load htmx_views_bootstrap %}

   {% bootstrap_accordion id="documents" %}
     {% for category, documents in grouped_documents.items %}
       {% bootstrap_accordion_item id=category.slug title=category.name expanded=forloop.first %}
         {% include "documents/_list.html" %}
       {% endbootstrap_accordion_item %}
     {% endfor %}
   {% endbootstrap_accordion %}

The outer tag requires ``id``. Set ``flush=True`` for Bootstrap's flush style,
``always_open=True`` to permit several open items, or pass additional classes
with ``class="..."``.

Each item requires an ``id`` and ``title``. The tag prefixes its header and
collapse IDs with the accordion ID, connects the control using
``aria-controls`` and ``aria-labelledby``, and keeps ``aria-expanded`` aligned
with the ``expanded`` option. ``heading_level`` accepts integers from 2 to 6.

Lazy accordion bodies
~~~~~~~~~~~~~~~~~~~~~

Pass ``hx_get`` to load a body the first time a collapsed item opens:

.. code-block:: django

   {% url "accounts:active" as active_accounts_url %}
   {% bootstrap_accordion id="accounts" %}
     {% bootstrap_accordion_item id="active" title="Active accounts" hx_get=active_accounts_url %}
       <span class="spinner-border" role="status">
         <span class="visually-hidden">Loading...</span>
       </span>
     {% endbootstrap_accordion_item %}
   {% endbootstrap_accordion %}

Collapsed items default to ``hx-trigger="shown.bs.collapse once"`` and target
their uniquely identified ``.accordion-body``. Initially expanded items use
``load`` instead. Override these defaults with ``hx_trigger``, ``hx_target``,
and ``hx_swap``.

Set ``target_id`` when the accordion body should select a concise
``HTMXProcessMixin`` template or context handler:

.. code-block:: django

   {% bootstrap_accordion id="dashboard" %}
     {% bootstrap_accordion_item id="documents" title="Documents" hx_get=request.path target_id="document_panel" %}
       <span class="spinner-border" role="status">
         <span class="visually-hidden">Loading...</span>
       </span>
     {% endbootstrap_accordion_item %}
   {% endbootstrap_accordion %}

The corresponding view can serve a full dashboard normally and return only the
panel for an HTMX request targeting ``#document_panel``:

.. code-block:: python

   from django.views.generic import TemplateView

   from htmx_views.views import HTMXProcessMixin

   from .models import Document


   class DocumentDashboardView(HTMXProcessMixin, TemplateView):
       template_name = "documents/dashboard.html"
       template_name_document_panel = "documents/_document_list.html"

       def get_context_data_document_panel(self, **kwargs):
           context = super().get_context_data(**kwargs)
           context["documents"] = Document.objects.order_by("title")
           return context

The mixin checks the trigger and target names in order. The generated trigger
ID has no matching override here, so the ``document_panel`` target selects both
``template_name_document_panel`` and
``get_context_data_document_panel()``.

Lazy paged lists
----------------

``bootstrap_lazy_page`` renders an HTMX loading sentinel with a Bootstrap
spinner. When given a Django paginator ``Page``, it appends the next page number
to the URL and renders nothing after the final page:

.. code-block:: django

   {% with column_count=table.columns|length %}
     {% bootstrap_lazy_page url=request.path page=table.page method="post" element="tr" colspan=column_count %}
   {% endwith %}

The table-row form wraps the spinner in a ``td`` with the requested
``colspan``. The default ``div`` form is suitable for lists and card grids.
``li`` is also supported.

The tag defaults to ``hx-trigger="intersect once"``. Unlike ``revealed``,
``intersect`` works predictably inside an overflow-scrolling responsive table.
It swaps the next response over the sentinel with ``outerHTML``, allowing that
response to finish with another sentinel.

Use ``include="form"`` when the next request must resubmit the current filters.
``method`` can be ``"get"`` or ``"post"``. ``element_id`` defaults to
``"next_batch"`` and is also used as the default target, retaining the target
name used by ``HTMXProcessMixin`` to select a ``next_batch`` response template.

Lists that use a continuation token instead of Django pagination can supply a
precomputed next URL and use ``when`` to suppress the final sentinel:

.. code-block:: django

   {% bootstrap_lazy_page url=next_url when=next_code element_id="table_part" %}

Other options are ``trigger``, ``target``, ``swap``, ``page_parameter``,
``label``, and ``extra_class``. Dynamic values retain Django's normal escaping
behaviour.

A paginated ``ListView`` can use the sentinel's default ``next_batch`` ID to
select a batch-only response template:

.. code-block:: python

   from django.views.generic import ListView

   from htmx_views.views import HTMXProcessMixin

   from .models import Document


   class DocumentListView(HTMXProcessMixin, ListView):
       model = Document
       context_object_name = "documents"
       paginate_by = 25
       template_name = "documents/document_list.html"
       template_name_next_batch = "documents/_document_batch.html"

The full template includes the first batch:

.. code-block:: django

   <ul id="document-list">
     {% include "documents/_document_batch.html" %}
   </ul>

The shared ``documents/_document_batch.html`` renders the current page and
ends with the next sentinel:

.. code-block:: django

   {% load htmx_views_bootstrap %}

   {% for document in documents %}
     <li>{{ document.title }}</li>
   {% endfor %}
   {% bootstrap_lazy_page url=request.path page=page_obj element="li" %}

When the sentinel intersects the viewport, its ID becomes the HTMX target.
``HTMXProcessMixin`` therefore selects ``template_name_next_batch``. The
returned rows replace the old sentinel and finish with a new one until
``page_obj.has_next()`` becomes false.

IDs and escaping
----------------

Component IDs must start with a letter and contain only letters, numbers,
underscores, or hyphens. This deliberate restriction keeps generated Bootstrap
and HTMX selectors valid. Titles, URLs, classes, and rendered block content
retain Django's normal escaping behaviour.
