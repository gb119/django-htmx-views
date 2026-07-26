"""Tests for the optional Bootstrap 5 template components."""

# Django imports
# external imports
import pytest
from django.core.paginator import Paginator
from django.template import Context, Template, TemplateSyntaxError

# package imports
from htmx_views import _optional


def render_template(source, context=None):
    """Render a template using the package's configured Django engine."""
    return Template("{% load htmx_views_bootstrap %}" + source).render(Context(context or {}))


class TestBootstrap3ButtonCompatibility:
    """Tests for the Bootstrap 3 button migration helpers."""

    def test_renders_bootstrap_icon_and_translates_common_glyphicon(self):
        """A legacy Glyphicon name becomes decorative Bootstrap Icons markup."""
        rendered = render_template('{% bootstrap_icon "info-sign" %}')

        assert rendered == '<i aria-hidden="true" class="bi bi-info-circle"></i>'

    def test_labelled_icon_has_accessible_attributes(self):
        """A titled icon exposes its label to assistive technology."""
        rendered = render_template(
            '{% bootstrap_icon "star" title=title extra_classes="text-warning" %}', {"title": "Favourite"}
        )

        assert 'class="bi bi-star text-warning"' in rendered
        assert 'aria-label="Favourite"' in rendered
        assert 'role="img"' in rendered
        assert 'title="Favourite"' in rendered

    def test_bootstrap_button_supports_legacy_icon_class_and_size(self):
        """Legacy button options are translated to Bootstrap 5 equivalents."""
        rendered = render_template(
            '{% bootstrap_button "Save" button_type="submit" icon="floppy-disk" '
            'button_class="btn-default" size="large" %}'
        )

        assert '<button class="btn btn-secondary btn-lg" type="submit">' in rendered
        assert '<i aria-hidden="true" class="bi bi-floppy me-1"></i>Save' in rendered

    def test_loading_after_django_bootstrap5_overrides_its_button_tag(self):
        """Documented library order selects the icon-compatible button tag."""
        rendered = Template(
            '{% load django_bootstrap5 htmx_views_bootstrap %}{% bootstrap_button "Edit" icon="edit" %}'
        ).render(Context())

        assert '<i aria-hidden="true" class="bi bi-pencil-square me-1"></i>Edit' in rendered

    def test_button_supports_end_icon_and_accessible_icon_only_content(self):
        """Icons can follow text and icon-only controls can receive a button label."""
        rendered = render_template(
            '{% bootstrap_button "" button_type="button" icon="remove" aria_label="Close" %}'
            '{% bootstrap_button "Next" href="/next/" icon="arrow-right" icon_position="end" %}'
        )

        assert 'aria-label="Close"' in rendered
        assert '<i aria-hidden="true" class="bi bi-x-lg"></i>' in rendered
        assert 'Next<i aria-hidden="true" class="bi bi-arrow-right ms-1"></i>' in rendered
        assert 'href="/next/"' in rendered
        assert 'role="button"' in rendered

    def test_buttons_block_wraps_custom_content_and_generated_actions(self):
        """The legacy block retains nested controls and adds configured actions."""
        rendered = render_template(
            '{% buttons submit="Save" reset="Cancel" submit_icon="floppy-disk" size="small" %}'
            '<a class="btn btn-link" href="/">Back</a>'
            "{% endbuttons %}"
        )

        assert '<div class="mb-3 d-flex flex-wrap gap-2">' in rendered
        assert '<a class="btn btn-link" href="/">Back</a>' in rendered
        assert '<button class="btn btn-primary btn-sm" type="submit">' in rendered
        assert '<button class="btn btn-secondary btn-sm" type="reset">Cancel</button>' in rendered
        assert rendered.index('type="submit"') < rendered.index(">Back</a>")

    def test_bootstrap_buttons_alias_uses_explicit_closing_tag(self):
        """The namespaced alias avoids collisions in new templates."""
        rendered = render_template(
            '{% bootstrap_buttons submit="Continue" wrapper_class="d-grid" %}{% endbootstrap_buttons %}'
        )

        assert '<div class="d-grid">' in rendered
        assert 'type="submit">Continue</button>' in rendered

    def test_button_content_and_attributes_remain_escaped(self):
        """Compatibility options retain Django's normal auto-escaping."""
        rendered = render_template(
            '{% bootstrap_button content button_type="button" icon="star" aria_label=label %}',
            {"content": "<script>alert(1)</script>", "label": 'Save" onclick="alert(1)'},
        )

        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
        assert 'aria-label="Save&quot; onclick=&quot;alert(1)"' in rendered
        assert "<script>" not in rendered

    def test_missing_optional_renderer_has_installation_guidance(self, monkeypatch):
        """The button tag explains how to install its optional renderer."""
        missing_dependency = ModuleNotFoundError("No module named 'django_bootstrap5'")
        missing_dependency.name = "django_bootstrap5"

        def raise_missing_dependency(_module_name):
            raise missing_dependency

        monkeypatch.setattr(_optional, "import_module", raise_missing_dependency)

        with pytest.raises(ImportError, match=r"django-htmx-views\[bootstrap5\]"):
            _optional.get_bootstrap5_render_button()

    def test_transitive_optional_import_error_is_not_hidden(self, monkeypatch):
        """An error inside django-bootstrap5 is preserved for diagnosis."""
        transitive_error = ModuleNotFoundError("No module named 'unexpected_dependency'")
        transitive_error.name = "unexpected_dependency"

        def raise_transitive_error(_module_name):
            raise transitive_error

        monkeypatch.setattr(_optional, "import_module", raise_transitive_error)

        with pytest.raises(ModuleNotFoundError, match="unexpected_dependency"):
            _optional.get_bootstrap5_render_button()

    @pytest.mark.parametrize(
        "source",
        [
            '{% bootstrap_icon "invalid icon" %}',
            '{% bootstrap_button "Save" icon="star" icon_position="middle" %}',
            '{% buttons unknown="value" %}{% endbuttons %}',
        ],
    )
    def test_rejects_invalid_compatibility_options(self, source):
        """Invalid icon names, positions, and block options fail clearly."""
        with pytest.raises(TemplateSyntaxError):
            render_template(source)


class TestBootstrapModalTarget:
    """Tests for the Bootstrap modal target tag."""

    def test_renders_labman_compatible_default_target(self):
        """The default target uses the IDs expected by the modal event handler."""
        rendered = render_template("{% bootstrap_modal_target %}")

        assert 'id="modal"' in rendered
        assert 'id="dialog"' in rendered
        assert 'class="modal-dialog modal-lg modal-dialog-centered"' in rendered
        assert 'aria-labelledby="dialog-title"' in rendered
        assert '<div class="modal-content"></div>' in rendered

    def test_supports_size_position_and_scrolling_options(self):
        """Modal presentation options map to the corresponding Bootstrap classes."""
        rendered = render_template(
            '{% bootstrap_modal_target size="xl" centred=False scrollable=True %}',
        )

        assert "modal-xl" in rendered
        assert "modal-dialog-scrollable" in rendered
        assert "modal-dialog-centered" not in rendered

    @pytest.mark.parametrize("argument", ['modal_id="not valid"', 'target_id="#dialog"', 'size="medium"'])
    def test_rejects_invalid_identifiers_and_sizes(self, argument):
        """Invalid values fail during rendering instead of producing broken selectors."""
        with pytest.raises(TemplateSyntaxError):
            render_template(f"{{% bootstrap_modal_target {argument} %}}")


class TestBootstrapModalContent:
    """Tests for the response-side Bootstrap modal wrapper."""

    def test_wraps_rendered_content_and_inherits_dialog_target(self):
        """The body remains rendered HTML and descendants inherit the HTMX target."""
        rendered = render_template(
            """
            {% bootstrap_modal_content title=title %}
                <form hx-post="/documents/"><input name="title"></form>
            {% endbootstrap_modal_content %}
            """,
            {"title": "Manage documents"},
        )

        assert 'class="modal-content" hx-target="#dialog"' in rendered
        assert '<h5 class="modal-title" id="dialog-title">Manage documents</h5>' in rendered
        assert 'class="btn-close"' in rendered
        assert '<form hx-post="/documents/"><input name="title"></form>' in rendered

    def test_escapes_title_and_custom_classes(self):
        """Untrusted title and class values cannot inject markup or attributes."""
        rendered = render_template(
            """
            {% bootstrap_modal_content title=title body_class=body_class %}
                Body
            {% endbootstrap_modal_content %}
            """,
            {
                "title": "<script>alert(1)</script>",
                "body_class": 'wide" onclick="alert(1)',
            },
        )

        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
        assert 'class="modal-body wide&quot; onclick=&quot;alert(1)"' in rendered
        assert "<script>" not in rendered

    def test_close_button_can_be_omitted(self):
        """Consumers can retain an existing in-form cancel control."""
        rendered = render_template(
            """
            {% bootstrap_modal_content title="Manage" close_button=False %}
                Body
            {% endbootstrap_modal_content %}
            """,
        )

        assert "btn-close" not in rendered

    def test_rejects_unknown_arguments(self):
        """A misspelt option raises an actionable template error."""
        with pytest.raises(TemplateSyntaxError, match="unexpected argument"):
            render_template(
                """
                {% bootstrap_modal_content title="Manage" close_buton=False %}
                    Body
                {% endbootstrap_modal_content %}
                """,
            )


class TestBootstrapLazyPage:
    """Tests for the Bootstrap lazy-page loading sentinel."""

    def test_renders_next_paginated_table_batch(self):
        """A table page produces a POST sentinel for its next page."""
        page = Paginator(range(3), 2).page(1)
        rendered = render_template(
            '{% bootstrap_lazy_page url="/results/?module=PHY&page=1#rows" page=page '
            'method="post" element="tr" colspan=columns include="form" %}',
            {"page": page, "columns": 7},
        )

        assert 'id="next_batch"' in rendered
        assert 'hx-post="/results/?module=PHY&amp;page=2#rows"' in rendered
        assert 'hx-trigger="intersect once"' in rendered
        assert 'hx-include="form"' in rendered
        assert 'hx-swap="outerHTML"' in rendered
        assert 'hx-target="#next_batch"' in rendered
        assert '<td class="text-center" colspan="7">' in rendered
        assert 'class="spinner-border text-primary"' in rendered
        assert '<span class="visually-hidden">Loading...</span>' in rendered

    def test_omits_sentinel_on_last_page(self):
        """The final paginator page renders no loading placeholder."""
        page = Paginator(range(3), 2).page(2)
        rendered = render_template('{% bootstrap_lazy_page url="/results/" page=page %}', {"page": page})

        assert rendered == ""

    def test_supports_precomputed_custom_next_url(self):
        """Non-paginator lists can supply their own URL and condition."""
        rendered = render_template(
            '{% bootstrap_lazy_page url=next_url when=next_code element_id="table_part" '
            'label="Loading tutorial groups" extra_class="my-3" %}',
            {
                "next_code": "GROUP2",
                "next_url": "/tutorial/engagement/GROUP2/?codes=A%2CB",
            },
        )

        assert 'id="table_part"' in rendered
        assert 'class="my-3"' in rendered
        assert 'hx-get="/tutorial/engagement/GROUP2/?codes=A%2CB"' in rendered
        assert "Loading tutorial groups" in rendered

    def test_false_condition_omits_custom_sentinel(self):
        """A false custom continuation value renders nothing."""
        rendered = render_template('{% bootstrap_lazy_page url="/next/" when=next_code %}', {"next_code": None})

        assert rendered == ""

    def test_escapes_url_label_and_classes(self):
        """Dynamic values remain protected by Django's HTML escaping."""
        rendered = render_template(
            "{% bootstrap_lazy_page url=url label=label extra_class=class_name %}",
            {
                "url": '"><script>alert(1)</script>',
                "label": "<strong>Loading</strong>",
                "class_name": 'wide" onclick="alert(1)',
            },
        )

        assert "&lt;script&gt;" in rendered
        assert "&lt;strong&gt;Loading&lt;/strong&gt;" in rendered
        assert 'class="wide&quot; onclick=&quot;alert(1)"' in rendered
        assert "<script>" not in rendered

    @pytest.mark.parametrize(
        "arguments",
        [
            'method="patch"',
            'element="span"',
            'element_id="invalid id"',
            "colspan=0",
        ],
    )
    def test_rejects_invalid_markup_options(self, arguments):
        """Unsupported methods, elements, IDs, and spans raise template errors."""
        with pytest.raises(TemplateSyntaxError):
            render_template(f'{{% bootstrap_lazy_page url="/next/" {arguments} %}}')

    def test_rejects_non_page_object(self):
        """Supplying an unrelated object as a page gives an actionable error."""
        with pytest.raises(TemplateSyntaxError, match=r"has_next\(\)"):
            render_template('{% bootstrap_lazy_page url="/next/" page=page %}', {"page": object()})


class TestBootstrapAccordion:
    """Tests for the Bootstrap accordion block tags."""

    def test_renders_unique_accessible_item_ids_and_state(self):
        """The item generates matched control IDs, parent linkage, and open state."""
        rendered = render_template(
            """
            {% bootstrap_accordion id="documents" %}
                {% bootstrap_accordion_item id="manuals" title="Manuals" expanded=True %}
                    Manual list
                {% endbootstrap_accordion_item %}
                {% bootstrap_accordion_item id="risk" title="Risk assessments" %}
                    Risk list
                {% endbootstrap_accordion_item %}
            {% endbootstrap_accordion %}
            """,
        )

        assert '<div class="accordion" id="documents">' in rendered
        assert 'id="documents-manuals-header"' in rendered
        assert 'data-bs-target="#documents-manuals-collapse"' in rendered
        assert 'aria-expanded="true"' in rendered
        assert 'class="accordion-collapse collapse show"' in rendered
        assert 'data-bs-parent="#documents"' in rendered
        assert 'id="documents-risk-header"' in rendered
        assert 'aria-expanded="false"' in rendered
        assert 'class="accordion-button collapsed"' in rendered

    def test_always_open_and_flush_options_change_wrapper_markup(self):
        """Independent items omit the Bootstrap parent selector."""
        rendered = render_template(
            """
            {% bootstrap_accordion id="filters" flush=True always_open=True %}
                {% bootstrap_accordion_item id="status" title="Status" %}Body{% endbootstrap_accordion_item %}
            {% endbootstrap_accordion %}
            """,
        )

        assert 'class="accordion accordion-flush"' in rendered
        assert "data-bs-parent" not in rendered

    def test_lazy_item_uses_bootstrap_event_and_relative_htmx_target(self):
        """A collapsed lazy item loads its body once when Bootstrap opens it."""
        rendered = render_template(
            """
            {% bootstrap_accordion id="accounts" %}
                {% bootstrap_accordion_item id="active" title="Active" hx_get="/accounts/active/" %}
                    Loading...
                {% endbootstrap_accordion_item %}
            {% endbootstrap_accordion %}
            """,
        )

        assert 'hx-get="/accounts/active/"' in rendered
        assert 'hx-trigger="shown.bs.collapse once"' in rendered
        assert 'hx-target="#accounts-active-body"' in rendered
        assert 'hx-swap="innerHTML"' in rendered
        assert 'class="accordion-body" id="accounts-active-body"' in rendered

    def test_lazy_item_supports_stable_backend_target_name(self):
        """An explicit body ID provides a concise HTMX mixin target."""
        rendered = render_template(
            '{% bootstrap_accordion id="documents" %}'
            '{% bootstrap_accordion_item id="manuals" title="Manuals" hx_get="/documents/" '
            'target_id="document_panel" %}'
            "{% endbootstrap_accordion_item %}"
            "{% endbootstrap_accordion %}",
        )

        assert 'hx-target="#document_panel"' in rendered
        assert 'class="accordion-body" id="document_panel"' in rendered

    def test_expanded_lazy_item_loads_immediately(self):
        """An initially expanded item does not wait for a future collapse event."""
        rendered = render_template(
            """
            {% bootstrap_accordion id="accounts" %}
                {% bootstrap_accordion_item id="active" title="Active" expanded=True hx_get="/accounts/active/" %}
                {% endbootstrap_accordion_item %}
            {% endbootstrap_accordion %}
            """,
        )

        assert 'hx-trigger="load"' in rendered

    def test_item_requires_accordion_parent(self):
        """An item outside an accordion fails with an actionable error."""
        with pytest.raises(TemplateSyntaxError, match="must be nested"):
            render_template(
                """
                {% bootstrap_accordion_item id="orphan" title="Orphan" %}
                {% endbootstrap_accordion_item %}
                """,
            )

    def test_titles_are_escaped(self):
        """Accordion titles cannot inject markup."""
        rendered = render_template(
            """
            {% bootstrap_accordion id="safe" %}
                {% bootstrap_accordion_item id="item" title=title %}Body{% endbootstrap_accordion_item %}
            {% endbootstrap_accordion %}
            """,
            {"title": "<img src=x onerror=alert(1)>"},
        )

        assert "&lt;img src=x onerror=alert(1)&gt;" in rendered
        assert "<img" not in rendered

    @pytest.mark.parametrize(
        "source",
        [
            '{% bootstrap_accordion id="invalid id" %}{% endbootstrap_accordion %}',
            (
                '{% bootstrap_accordion id="valid" %}'
                '{% bootstrap_accordion_item id="invalid.id" title="Item" %}'
                "{% endbootstrap_accordion_item %}"
                "{% endbootstrap_accordion %}"
            ),
            (
                '{% bootstrap_accordion id="valid" %}'
                '{% bootstrap_accordion_item id="item" title="Item" heading_level=1 %}'
                "{% endbootstrap_accordion_item %}"
                "{% endbootstrap_accordion %}"
            ),
        ],
    )
    def test_rejects_values_that_would_break_component_markup(self, source):
        """Invalid IDs and heading levels fail with template errors."""
        with pytest.raises(TemplateSyntaxError):
            render_template(source)
