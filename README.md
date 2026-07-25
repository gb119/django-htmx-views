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

## Installation

Install the core package:

```console
python -m pip install django-htmx-views
```

Install linked-select support as well:

```console
python -m pip install "django-htmx-views[linked-selects]"
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

## Development and builds

Create a development environment and run the tests:

```console
python -m pip install -e ".[test,linked-selects]"
python -m pytest
```

Build and validate the wheel and source distribution:

```console
python -m build
python -m twine check dist/*
```

Build the noarch Conda package with `conda-build`:

```console
conda build conda-recipe
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

Configure these GitHub Actions repository secrets before publishing:

- `PYPI_TOKEN`: a PyPI API token authorised for `django-htmx-views`;
- `ANACONDA`: an Anaconda.org API token authorised to upload to `phygbu`.

The upload steps deliberately refuse to overwrite an existing Conda package.

## License

MIT
