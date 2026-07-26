"""Provide Bootstrap 5 modal and accordion template components.

The tags in this module generate the structural Bootstrap markup and related
accessibility attributes used by HTMX-powered interfaces.  They do not load
Bootstrap assets; the consuming application remains responsible for including
Bootstrap's CSS and JavaScript.
"""

# Python imports
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Django imports
from django import template
from django.forms.utils import flatatt
from django.template.base import token_kwargs
from django.utils.html import format_html

register = template.Library()

_ACCORDION_CONTEXT_KEY = "_htmx_views_bootstrap_accordion"
_HTML_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_MODAL_SIZES = {"sm", "lg", "xl"}
_LAZY_PAGE_ELEMENTS = {"div", "li", "tr"}
_LAZY_PAGE_METHODS = {"get", "post"}


def _validate_html_id(value, argument_name):
    """Return a safe HTML ID or raise a helpful template error."""
    html_id = str(value)
    if not _HTML_ID_PATTERN.fullmatch(html_id):
        raise template.TemplateSyntaxError(
            f"{argument_name} must start with a letter and contain only letters, numbers, underscores, or hyphens."
        )
    return html_id


def _parse_block_tag(parser, token, end_tag, required_arguments, allowed_arguments, node_class):
    """Parse keyword arguments and content shared by the block tags."""
    bits = token.split_contents()
    tag_name = bits.pop(0)
    arguments = token_kwargs(bits, parser)
    if bits:
        raise template.TemplateSyntaxError(f"{tag_name!r} accepts keyword arguments only.")

    missing = set(required_arguments) - arguments.keys()
    if missing:
        names = ", ".join(sorted(missing))
        raise template.TemplateSyntaxError(f"{tag_name!r} requires the following argument(s): {names}.")
    unexpected = arguments.keys() - set(allowed_arguments)
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise template.TemplateSyntaxError(f"{tag_name!r} received unexpected argument(s): {names}.")

    nodelist = parser.parse((end_tag,))
    parser.delete_first_token()
    return node_class(nodelist, arguments)


def _resolve(arguments, context):
    """Resolve compiled template expressions against the current context."""
    return {name: expression.resolve(context) for name, expression in arguments.items()}


def _replace_query_parameter(url, name, value):
    """Replace one query-string parameter while retaining the remaining URL."""
    split_url = urlsplit(str(url))
    query = [(key, item) for key, item in parse_qsl(split_url.query, keep_blank_values=True) if key != name]
    query.append((name, str(value)))
    return urlunsplit((split_url.scheme, split_url.netloc, split_url.path, urlencode(query), split_url.fragment))


@register.simple_tag
def bootstrap_modal_target(
    modal_id="modal",
    target_id="dialog",
    title_id="dialog-title",
    size="lg",
    centred=True,
    scrollable=False,
):
    """Render the empty target into which an HTMX modal response is swapped.

    Keyword Parameters:
        modal_id (str):
            ID of the outer Bootstrap modal.
        target_id (str):
            ID of the HTMX swap target inside the modal.
        title_id (str):
            ID used by the modal content heading.
        size (str):
            Bootstrap modal size: ``"sm"``, ``"lg"``, or ``"xl"``.
        centred (bool):
            Whether to centre the dialog vertically.
        scrollable (bool):
            Whether the modal body should be independently scrollable.

    Returns:
        (SafeString):
            Bootstrap modal target markup.

    Raises:
        TemplateSyntaxError:
            If an ID or modal size is invalid.

    Examples:
        Load the tag library and create a large modal target:

        .. code-block:: django

            {% load htmx_views_bootstrap %}
            {% bootstrap_modal_target size="lg" %}
    """
    modal_id = _validate_html_id(modal_id, "modal_id")
    target_id = _validate_html_id(target_id, "target_id")
    title_id = _validate_html_id(title_id, "title_id")
    if size not in _MODAL_SIZES and size not in (None, ""):
        sizes = ", ".join(sorted(_MODAL_SIZES))
        raise template.TemplateSyntaxError(f"size must be one of {sizes}, or an empty value.")

    dialog_classes = ["modal-dialog"]
    if size:
        dialog_classes.append(f"modal-{size}")
    if centred:
        dialog_classes.append("modal-dialog-centered")
    if scrollable:
        dialog_classes.append("modal-dialog-scrollable")

    modal_attributes = {
        "id": modal_id,
        "class": "modal modal-blur fade",
        "style": "display: none",
        "tabindex": "-1",
        "aria-labelledby": title_id,
        "aria-hidden": "true",
    }
    dialog_attributes = {
        "id": target_id,
        "class": " ".join(dialog_classes),
        "role": "document",
    }
    return format_html(
        '<div{}><div{}><div class="modal-content"></div></div></div>',
        flatatt(modal_attributes),
        flatatt(dialog_attributes),
    )


@register.simple_tag
def bootstrap_lazy_page(
    url,
    page=None,
    when=True,
    method="get",
    element="div",
    element_id="next_batch",
    include=None,
    trigger="intersect once",
    target=None,
    swap="outerHTML",
    page_parameter="page",
    colspan=1,
    label="Loading...",
    extra_class="",
):
    """Render a Bootstrap loading sentinel for the next HTMX page.

    Args:
        url (str):
            URL used to load the next batch.

    Keyword Parameters:
        page (Page):
            Optional Django paginator page. The sentinel is omitted on the last
            page and the next page number is added to ``url``.
        when (bool):
            Additional condition controlling whether the sentinel is rendered.
        method (str):
            HTMX request method, either ``"get"`` or ``"post"``.
        element (str):
            Outer element: ``"div"``, ``"li"``, or ``"tr"``.
        element_id (str):
            ID of the loading sentinel and default HTMX target.
        include (str):
            Optional ``hx-include`` selector, such as ``"form"``.
        trigger (str):
            HTMX trigger. Defaults to ``"intersect once"``.
        target (str):
            HTMX target. Defaults to the sentinel's own ID.
        swap (str):
            HTMX swap mode. Defaults to ``"outerHTML"``.
        page_parameter (str):
            Query-string parameter used for the page number.
        colspan (int):
            Number of columns spanned when ``element="tr"``.
        label (str):
            Visually hidden accessible loading label.
        extra_class (str):
            Additional class or classes for the outer element.

    Returns:
        (SafeString):
            Loading-sentinel markup, or an empty string when there is no next
            page.

    Raises:
        TemplateSyntaxError:
            If an option would produce invalid markup.

    Examples:
        Render the next row for a paginated ``django-tables2`` table:

        .. code-block:: django

            {% bootstrap_lazy_page url=path page=page method="post" element="tr" colspan=columns %}
    """
    if not when:
        return ""
    if page is not None:
        try:
            has_next = page.has_next()
            next_page_number = page.next_page_number() if has_next else None
        except (AttributeError, TypeError) as error:
            raise template.TemplateSyntaxError("page must provide has_next() and next_page_number().") from error
        if not has_next:
            return ""
        url = _replace_query_parameter(url, str(page_parameter), next_page_number)

    method = str(method).lower()
    if method not in _LAZY_PAGE_METHODS:
        methods = ", ".join(sorted(_LAZY_PAGE_METHODS))
        raise template.TemplateSyntaxError(f"method must be one of {methods}.")
    element = str(element).lower()
    if element not in _LAZY_PAGE_ELEMENTS:
        elements = ", ".join(sorted(_LAZY_PAGE_ELEMENTS))
        raise template.TemplateSyntaxError(f"element must be one of {elements}.")
    element_id = _validate_html_id(element_id, "element_id")
    try:
        colspan = int(colspan)
    except (TypeError, ValueError) as error:
        raise template.TemplateSyntaxError("colspan must be a positive integer.") from error
    if colspan < 1:
        raise template.TemplateSyntaxError("colspan must be a positive integer.")

    attributes = {
        "id": element_id,
        f"hx-{method}": url,
        "hx-trigger": trigger,
        "hx-swap": swap,
        "hx-target": target or f"#{element_id}",
    }
    if extra_class:
        attributes["class"] = str(extra_class)
    if include:
        attributes["hx-include"] = include

    spinner = format_html(
        '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">{}</span></div>',
        label,
    )
    if element == "tr":
        return format_html(
            "<tr{}><td{}>{}</td></tr>",
            flatatt(attributes),
            flatatt({"class": "text-center", "colspan": colspan}),
            spinner,
        )
    return format_html("<{}{}>{}</{}>", element, flatatt(attributes), spinner, element)


class _BootstrapModalContentNode(template.Node):
    """Render the response-side Bootstrap modal wrapper."""

    def __init__(self, nodelist, arguments):
        self.nodelist = nodelist
        self.arguments = arguments

    def render(self, context):
        """Render the modal title, body, and optional close button."""
        arguments = _resolve(self.arguments, context)
        title = arguments["title"]
        target = arguments.get("target", "#dialog")
        title_id = _validate_html_id(arguments.get("title_id", "dialog-title"), "title_id")
        close_button = arguments.get("close_button", True)
        content_class = arguments.get("content_class", "")
        header_class = arguments.get("header_class", "")
        body_class = arguments.get("body_class", "")
        content = self.nodelist.render(context)

        close_markup = ""
        if close_button:
            close_markup = format_html(
                '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="{}"></button>',
                "Close",
            )

        content_attributes = {
            "class": f"modal-content {content_class}".strip(),
            "hx-target": target,
        }
        header_attributes = {"class": f"modal-header {header_class}".strip()}
        body_attributes = {"class": f"modal-body {body_class}".strip()}
        return format_html(
            '<div{}><div{}><h5 class="modal-title" id="{}">{}</h5>{}</div><div{}>{}</div></div>',
            flatatt(content_attributes),
            flatatt(header_attributes),
            title_id,
            title,
            close_markup,
            flatatt(body_attributes),
            content,
        )


@register.tag("bootstrap_modal_content")
def do_bootstrap_modal_content(parser, token):
    """Compile a ``bootstrap_modal_content`` block.

    Args:
        parser (Parser):
            Active Django template parser.
        token (Token):
            Opening template-tag token.

    Returns:
        (_BootstrapModalContentNode):
            Compiled modal-content node.

    Examples:
        Wrap an HTMX form response in Bootstrap modal markup:

        .. code-block:: django

            {% bootstrap_modal_content title="Manage document" %}
                <form hx-post="{{ post_url }}">
                    ...
                </form>
            {% endbootstrap_modal_content %}
    """
    return _parse_block_tag(
        parser,
        token,
        "endbootstrap_modal_content",
        required_arguments=("title",),
        allowed_arguments=(
            "title",
            "target",
            "title_id",
            "close_button",
            "content_class",
            "header_class",
            "body_class",
        ),
        node_class=_BootstrapModalContentNode,
    )


class _BootstrapAccordionNode(template.Node):
    """Render a Bootstrap accordion and provide its ID to nested items."""

    def __init__(self, nodelist, arguments):
        self.nodelist = nodelist
        self.arguments = arguments

    def render(self, context):
        """Render the accordion wrapper and its nested item nodes."""
        arguments = _resolve(self.arguments, context)
        accordion_id = _validate_html_id(arguments["id"], "id")
        flush = arguments.get("flush", False)
        always_open = arguments.get("always_open", False)
        extra_class = arguments.get("class", "")
        classes = ["accordion"]
        if flush:
            classes.append("accordion-flush")
        if extra_class:
            classes.append(str(extra_class))

        with context.push():
            context[_ACCORDION_CONTEXT_KEY] = {
                "id": accordion_id,
                "always_open": bool(always_open),
            }
            content = self.nodelist.render(context)

        return format_html("<div{}>{}</div>", flatatt({"id": accordion_id, "class": " ".join(classes)}), content)


@register.tag("bootstrap_accordion")
def do_bootstrap_accordion(parser, token):
    """Compile a ``bootstrap_accordion`` block.

    Args:
        parser (Parser):
            Active Django template parser.
        token (Token):
            Opening template-tag token.

    Returns:
        (_BootstrapAccordionNode):
            Compiled accordion node.

    Examples:
        Create an accordion containing item tags:

        .. code-block:: django

            {% bootstrap_accordion id="documents" %}
                ...
            {% endbootstrap_accordion %}
    """
    return _parse_block_tag(
        parser,
        token,
        "endbootstrap_accordion",
        required_arguments=("id",),
        allowed_arguments=("id", "flush", "always_open", "class"),
        node_class=_BootstrapAccordionNode,
    )


class _BootstrapAccordionItemNode(template.Node):
    """Render one item inside the current Bootstrap accordion."""

    def __init__(self, nodelist, arguments):
        self.nodelist = nodelist
        self.arguments = arguments

    def render(self, context):
        """Render an accordion heading, collapse region, and body."""
        parent = context.get(_ACCORDION_CONTEXT_KEY)
        if parent is None:
            raise template.TemplateSyntaxError("bootstrap_accordion_item must be nested inside bootstrap_accordion.")

        arguments = _resolve(self.arguments, context)
        item_id = _validate_html_id(arguments["id"], "id")
        expanded = bool(arguments.get("expanded", False))
        heading_level = arguments.get("heading_level", 2)
        try:
            heading_level = int(heading_level)
        except (TypeError, ValueError) as error:
            raise template.TemplateSyntaxError("heading_level must be an integer from 2 to 6.") from error
        if not 2 <= heading_level <= 6:
            raise template.TemplateSyntaxError("heading_level must be an integer from 2 to 6.")

        base_id = f"{parent['id']}-{item_id}"
        header_id = f"{base_id}-header"
        collapse_id = f"{base_id}-collapse"
        body_id = _validate_html_id(arguments.get("target_id", f"{base_id}-body"), "target_id")
        button_classes = ["accordion-button"]
        collapse_classes = ["accordion-collapse", "collapse"]
        if not expanded:
            button_classes.append("collapsed")
        if expanded:
            collapse_classes.append("show")

        collapse_attributes = {
            "id": collapse_id,
            "class": " ".join(collapse_classes),
            "aria-labelledby": header_id,
        }
        if not parent["always_open"]:
            collapse_attributes["data-bs-parent"] = f"#{parent['id']}"

        hx_get = arguments.get("hx_get")
        if hx_get:
            collapse_attributes.update(
                {
                    "hx-get": hx_get,
                    "hx-trigger": arguments.get(
                        "hx_trigger",
                        "load" if expanded else "shown.bs.collapse once",
                    ),
                    "hx-target": arguments.get("hx_target", f"#{body_id}"),
                    "hx-swap": arguments.get("hx_swap", "innerHTML"),
                }
            )

        button_attributes = {
            "class": " ".join(button_classes),
            "type": "button",
            "data-bs-toggle": "collapse",
            "data-bs-target": f"#{collapse_id}",
            "aria-expanded": str(expanded).lower(),
            "aria-controls": collapse_id,
        }
        item_class = arguments.get("class", "")
        item_attributes = {"class": f"accordion-item {item_class}".strip()}
        body_attributes = {"class": "accordion-body", "id": body_id}
        content = self.nodelist.render(context)
        heading_open = format_html("<h{}{}>", heading_level, flatatt({"class": "accordion-header", "id": header_id}))
        heading_close = format_html("</h{}>", heading_level)

        return format_html(
            "{}{}<button{}>{}</button>{}<div{}><div{}>{}</div></div></div>",
            format_html("<div{}>", flatatt(item_attributes)),
            heading_open,
            flatatt(button_attributes),
            arguments["title"],
            heading_close,
            flatatt(collapse_attributes),
            flatatt(body_attributes),
            content,
        )


@register.tag("bootstrap_accordion_item")
def do_bootstrap_accordion_item(parser, token):
    """Compile a ``bootstrap_accordion_item`` block.

    Args:
        parser (Parser):
            Active Django template parser.
        token (Token):
            Opening template-tag token.

    Returns:
        (_BootstrapAccordionItemNode):
            Compiled accordion-item node.

    Examples:
        Render an initially expanded item:

        .. code-block:: django

            {% bootstrap_accordion_item id="manuals" title="Manuals" expanded=True %}
                ...
            {% endbootstrap_accordion_item %}
    """
    return _parse_block_tag(
        parser,
        token,
        "endbootstrap_accordion_item",
        required_arguments=("id", "title"),
        allowed_arguments=(
            "id",
            "title",
            "expanded",
            "heading_level",
            "class",
            "target_id",
            "hx_get",
            "hx_trigger",
            "hx_target",
            "hx_swap",
        ),
        node_class=_BootstrapAccordionItemNode,
    )
