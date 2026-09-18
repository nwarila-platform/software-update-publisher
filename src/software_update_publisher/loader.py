"""Finds the product modules and checks that each one declares itself properly.

Discovery is a filesystem walk of the ``products`` package rather than installed entry points.
Entry points are the conventional answer and they were rejected for one reason: they are read
from distribution metadata, so a contributor who clones this repository and runs it would find
no products at all until they installed it. For a repository whose premise is that adding a
product means adding a folder, that is the wrong failure.

The cost of the filesystem walk is that a module has to be imported before its declaration can
be read. That import is contained per module, because forty-odd independent products should not
share a fate.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import cast

from . import products
from ._contracts import ProductDeclaration, ProductModule
from .exceptions import DeclarationError


@dataclass(frozen=True, slots=True)
class LoadedProduct:
    """A module that imported cleanly and declared itself correctly."""

    declaration: ProductDeclaration
    module: ProductModule


@dataclass(frozen=True, slots=True)
class LoadFailure:
    """A module that could not be loaded, and why.

    Carried rather than raised so that one broken product does not hide the other forty.
    """

    key: str
    reason: str


def product_keys() -> list[str]:
    """Return the name of every product module, in a stable order.

    ``ispkg`` filters out a stray module file sitting beside the packages: without it, a loose
    ``notes.py`` in this directory would be offered as a product. The explicit sort is kept
    because the ordering guarantee applies within a path entry, not across them.
    """
    return sorted(module.name for module in pkgutil.iter_modules(products.__path__) if module.ispkg)


def load_products() -> tuple[list[LoadedProduct], list[LoadFailure]]:
    """Import every product module and validate what it declares.

    Returns the ones that loaded and the ones that did not. A declaration problem is a defect in
    this repository, so it is reported against the module that owns it rather than at the end of
    a run.
    """
    loaded: list[LoadedProduct] = []
    failures: list[LoadFailure] = []

    for key in product_keys():
        try:
            module = importlib.import_module(f"{products.__name__}.{key}")
        except Exception as exc:  # one product's import must not end the run
            failures.append(LoadFailure(key=key, reason=f"import failed: {exc!r}"))
            continue

        declaration = getattr(module, "DECLARATION", None)
        if not isinstance(declaration, ProductDeclaration):
            failures.append(LoadFailure(key=key, reason="does not export a ProductDeclaration named DECLARATION"))
            continue
        if declaration.key != key:
            failures.append(LoadFailure(key=key, reason=f"declares key {declaration.key!r} but lives in {key!r}"))
            continue
        if not callable(getattr(module, "check", None)):
            failures.append(LoadFailure(key=key, reason="does not define check()"))
            continue

        loaded.append(LoadedProduct(declaration=declaration, module=cast(ProductModule, module)))

    return loaded, failures


def require_products() -> list[LoadedProduct]:
    """Return every product, refusing to continue if any of them is malformed.

    Used where a partial view would be misleading -- listing what this build tracks, for one.
    """
    loaded, failures = load_products()
    if failures:
        detail = "; ".join(f"{failure.key}: {failure.reason}" for failure in failures)
        raise DeclarationError(
            what=f"{len(failures)} product module(s) are malformed.",
            why=detail,
            fix="Fix the declaration in each module named above; they are defects in this repository.",
        )
    return loaded
