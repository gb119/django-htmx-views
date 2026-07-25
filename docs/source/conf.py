"""Configure the Sphinx documentation for django-htmx-views."""

# Python imports
import os
import sys
from pathlib import Path

# Django imports
import django

# external imports
from better import better_theme_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# package imports
from htmx_views import __version__  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
django.setup()

project = "django-htmx-views"
author = "Gavin Burnell"
copyright = "2026, Gavin Burnell"

release = __version__
version = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
intersphinx_mapping = {
    "django": ("https://docs.djangoproject.com/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
}

html_theme = "better"
html_theme_path = [better_theme_path]
html_logo = "images/StonerLogo2.png"
html_title = f"{project} {release}"
html_theme_options = {
    "linktotheme": True,
    "rightsidebar": False,
    "showheader": True,
    "showrelbarbottom": True,
    "showrelbartop": True,
    "sidebarwidth": "16rem",
}
