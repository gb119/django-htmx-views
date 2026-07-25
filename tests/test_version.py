"""Test the package's single-source version configuration."""

# Python imports
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by Python 3.10 CI
    import tomli as tomllib

# package imports
from htmx_views import __version__


def test_dunder_version_is_a_release_string():
    """The public package version uses a conventional release format."""
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[abrc]\d+)?", __version__)


def test_setuptools_reads_version_from_package():
    """Setuptools must not duplicate the version in project metadata."""
    configuration = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert "version" not in configuration["project"]
    assert "version" in configuration["project"]["dynamic"]
    assert configuration["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "htmx_views.__version__"
    }
