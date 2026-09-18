"""The package version, resolved once.

It lives in its own module so that both the public API and the command line can read it without
importing each other. The distribution metadata is the single source; ``pyproject.toml`` sets it.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("software-update-publisher")
except PackageNotFoundError:  # a source tree that was never installed, e.g. PYTHONPATH=src
    __version__ = "0.0.0+source"
