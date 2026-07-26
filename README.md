[![Tests](https://github.com/gb119/django-htmx-views/actions/workflows/tests.yml/badge.svg)](https://github.com/gb119/django-htmx-views/actions/workflows/tests.yml)
[![Build](https://github.com/gb119/django-htmx-views/actions/workflows/build.yml/badge.svg)](https://github.com/gb119/django-htmx-views/actions/workflows/build.yml)
[![GitHub version](https://badge.fury.io/gh/gb119%2Fdjango-htmx-views.svg)](https://badge.fury.io/gh/gb119%2Fdjango-htmx-views)
![GitHub Release Date](https://img.shields.io/github/release-date/gb119/django-htmx-views)
[![PyPI version](https://badge.fury.io/py/django-htmx-views.svg)](https://badge.fury.io/py/django-htmx-views)
[![Conda Version](https://anaconda.org/phygbu/django-htmx-views/badges/version.svg)](https://anaconda.org/phygbu/django-htmx-views)

# django-htmx-views

Reusable Django view mixins and widgets for building HTMX-enabled applications.
This package extracts the `htmx_views` app used by
[`gb119/labman`](https://github.com/gb119/labman) and
[`uolphysicsteaching/phas_vitals`](https://github.com/uolphysicsteaching/phas_vitals)
so that the implementation can be installed and maintained independently.

The initial package source is an exact copy of the newer `phas_vitals`
implementation at commit
[`1008bc4`](https://github.com/uolphysicsteaching/phas_vitals/commit/1008bc475a28a0ccca40df8769ad6902b68edebc).
The two upstream apps were compared before extraction and are not currently
identical; see [UPSTREAM_COMPARISON.md](UPSTREAM_COMPARISON.md) for the
verification details.

## Features

- HTMX-aware dispatch for Django class-based views.
- Routing by HTMX trigger name, trigger ID, or target ID.
- HTMX-specific templates, context data, and context object names.
- HTMX-aware form-valid and form-invalid handlers.
- Optional linked `<select>` widgets backed by `django-ajax-selects`.
- Optional Bootstrap 3 button migration helpers and Bootstrap 5 modal,
  accordion, and lazy-pagination template components.

## Installation

Install the core package:

```console
python -m pip install django-htmx-views
```

Install linked-select support as well:

```console
python -m pip install "django-htmx-views[linked-selects]"
```

Install the Bootstrap 5 integration, including `django-bootstrap5`, with:

```console
python -m pip install "django-htmx-views[bootstrap5]"
```

Add the app and `django-htmx` middleware to the host project's settings:

```python
INSTALLED_APPS = [
    # ...
    "htmx_views",
]

MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
]
```

## HTMX-aware views

Importing `htmx_views.views` installs the existing HTMX-aware dispatch hook on
Django's base `View` class. Mix `HTMXProcessMixin` into a class-based view to
route HTMX requests to element-specific handlers:

```python
from django.http import HttpResponse
from django.views.generic import TemplateView

from htmx_views.views import HTMXProcessMixin


class ResultsView(HTMXProcessMixin, TemplateView):
    template_name = "results/page.html"
    template_name_results = "results/_table.html"

    def htmx_get_refresh(self, request, *args, **kwargs):
        return HttpResponse("refreshed")
```

For an HTMX `GET`, the mixin looks for handlers using the request's
`trigger_name`, `trigger`, and `target`, in that order. Element names are
lowercased and stripped of characters other than letters, numbers, and
underscores. The same convention is available for `DELETE`, `PATCH`, `POST`,
and `PUT`.

`HTMXFormMixin` adds equivalent `htmx_form_valid_<element>` and
`htmx_form_invalid_<element>` hooks for form views.

## Linked selects

Linked selects are optional because they require `django-ajax-selects`. After
installing the `linked-selects` extra, include the package URLs:

```python
from django.urls import include, path

urlpatterns = [
    path(
        "htmx-views/",
        include(("htmx_views.urls", "htmx_views"), namespace="htmx_views"),
    ),
]
```

Then use a registered `django-ajax-selects` lookup:

```python
from django import forms

from htmx_views.widgets import HTMXSelectWidget


class EquipmentForm(forms.Form):
    module = forms.ModelChoiceField(queryset=...)
    category = forms.ModelChoiceField(
        queryset=...,
        widget=HTMXSelectWidget("categories", parent="module"),
    )
```

The linked-select endpoint runs the lookup's authorisation check before
querying it. Importing linked-select modules without the optional dependency
raises an actionable `ImportError`; the core view mixins remain usable.

## Migrating an existing project

1. Install this package and add `"htmx_views"` to `INSTALLED_APPS`.
2. Replace imports beginning with `apps.htmx_views` with `htmx_views`.
3. If linked selects are used, install the extra and include
   `htmx_views.urls` under the `htmx_views` namespace.
4. Remove the project's copied `apps/htmx_views` directory after its tests
   pass against the package.

The former `htmx_views.views.LinkedSelectEndpointView` import remains available
for compatibility.

## Bootstrap 5 template components

Load `htmx_views_bootstrap` after `django_bootstrap5` to restore the Bootstrap
3 `bootstrap_icon` and `buttons` helpers and add the former `icon` argument to
`bootstrap_button`:

```django
{% load django_bootstrap5 htmx_views_bootstrap %}

{% bootstrap_button "Save" button_type="submit" icon="floppy-disk" %}
{% buttons submit="Save" reset="Cancel" %}
{% endbuttons %}
```

Icons use Bootstrap Icons, which the consuming application must load
separately. Common Glyphicon names, `btn-default`, and legacy button sizes are
translated to Bootstrap 5 equivalents.

The modal tags separate the persistent page target from the content returned
by an HTMX request:

```django
{% load htmx_views_bootstrap %}

{% bootstrap_modal_target size="lg" %}
```

```django
{% load django_bootstrap5 htmx_views_bootstrap %}

{% bootstrap_modal_content title="Manage document" %}
  <form method="post" hx-post="{{ post_url }}">
    {% csrf_token %}
    {% bootstrap_form form layout="horizontal" %}
    <button type="submit" class="btn btn-primary">Save</button>
  </form>
{% endbootstrap_modal_content %}
```

The modal-content wrapper supplies `hx-target="#dialog"`, which is inherited by
the form and other HTMX controls within it. A complete accordion uses nested
block tags:

```django
{% bootstrap_accordion id="documents" %}
  {% for category, documents in grouped_documents.items %}
    {% bootstrap_accordion_item id=category.slug title=category.name expanded=forloop.first %}
      {% include "documents/_list.html" %}
    {% endbootstrap_accordion_item %}
  {% endfor %}
{% endbootstrap_accordion %}
```

An accordion item can load its body on first expansion by passing `hx_get`.
Lazy paged lists can replace their loading sentinel with the next batch:

```django
{% bootstrap_lazy_page url=request.path page=table.page method="post" element="tr" colspan=column_count %}
```

The tag omits itself on the final `Page`, adds the next page number to the URL,
and defaults to `hx-trigger="intersect once"` and `hx-swap="outerHTML"`. Lists
with a custom continuation token can instead pass a precomputed URL and
`when=next_code`.

See the
[Bootstrap template components documentation](https://gb119.github.io/django-htmx-views/bootstrap-components.html)
for the complete options and integration requirements.

## Development and builds

Create a development environment and run the tests:

```console
python -m pip install -e ".[test,linked-selects,bootstrap5]"
python -m pytest
```

Build and validate the wheel and source distribution:

```console
python -m build
python -m twine check dist/*
```

Build the noarch Conda package with `conda-build`:

```console
conda-build conda-recipe
```

The GitHub Actions build workflow runs the tests and produces both Python and
Conda package artifacts.

## Documentation

The full documentation is published at
[gb119.github.io/django-htmx-views](https://gb119.github.io/django-htmx-views/).

Build it locally with:

```console
python -m pip install -e ".[docs]"
python -m sphinx -W --keep-going -b html docs/source docs/build/html
```

The documentation workflow rebuilds and deploys GitHub Pages for published
releases and pre-releases, and can also be started manually.

## Publishing a release

Creating a GitHub release, including a pre-release, runs the release workflow.
It verifies that the release tag (for example, `vX.Y.Z`) matches
`htmx_views.__version__`, reruns the tests, builds both package formats, and
publishes:

- the wheel and source distribution to PyPI;
- the noarch Conda package to the `phygbu` Anaconda channel with the `main`
  label.

The release workflow can also be started manually from a branch containing
workflow-only fixes. Supply the existing release tag in the `release_tag`
input; the workflow definition comes from the selected branch, while the
package source is checked out from that tag.

Configure these GitHub Actions repository secrets before publishing:

- `PYPI_TOKEN`: a PyPI API token authorised for `django-htmx-views`;
- `ANACONDA`: an Anaconda.org API token authorised to upload to `phygbu`.

The upload steps deliberately refuse to overwrite an existing Conda package.

## License

MIT
