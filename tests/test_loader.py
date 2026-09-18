"""Tests for product discovery and the declaration contract.

The loader is the piece that makes "adding a product is adding a folder" true, so these tests
are mostly about what it refuses: a folder that is not a package, a module that forgets part of
the contract, and a module whose import blows up.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from software_update_publisher._contracts import ArtifactClass, ProductDeclaration
from software_update_publisher.exceptions import DeclarationError
from software_update_publisher.loader import load_products, product_keys, require_products

_GOOD = """
from software_update_publisher._contracts import ArtifactClass, ProductDeclaration

DECLARATION = ProductDeclaration(
    key="{key}", vendor="V", application="A", pdq_variable="{pin}",
    artifact_class=ArtifactClass.MSI, architecture="x64",
)

def check(fetch_json):
    return None
"""


@pytest.fixture
def product_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A throwaway products package, so these tests never depend on what is shipped.

    The package name is unique per test: a shared name would be cached in ``sys.modules``
    after the first test and every later one would silently load the first test's tree.
    """
    name = f"fake_products_{abs(hash(tmp_path)) % 10**8}"
    root = tmp_path / name
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    package = importlib.import_module(name)
    monkeypatch.setattr("software_update_publisher.loader.products", package)
    yield root
    for module in [key for key in sys.modules if key == name or key.startswith(f"{name}.")]:
        del sys.modules[module]


def _module(key: str, pin: str | None = None) -> str:
    """A well-formed module. Pin keys are unique by default: two modules may not share one."""
    return _GOOD.format(key=key, pin=pin or f"Vendor_{key.replace(chr(95), chr(45))}")


def _add(root: Path, key: str, body: str) -> None:
    folder = root / key
    folder.mkdir()
    (folder / "__init__.py").write_text(body, encoding="utf-8")


class TestDiscovery:
    def test_finds_packages_in_a_stable_order(self, product_tree: Path) -> None:
        for key in ("zebra", "alpha", "middle"):
            _add(product_tree, key, _module(key))
        assert product_keys() == ["alpha", "middle", "zebra"]

    def test_ignores_a_loose_module_beside_the_packages(self, product_tree: Path) -> None:
        # Without the ispkg filter a stray notes.py would be offered as a product.
        _add(product_tree, "real", _module("real"))
        (product_tree / "notes.py").write_text("", encoding="utf-8")
        assert product_keys() == ["real"]

    def test_ignores_a_directory_that_is_not_a_package(self, product_tree: Path) -> None:
        _add(product_tree, "real", _module("real"))
        (product_tree / "scratch").mkdir()
        (product_tree / "scratch" / "product.py").write_text("", encoding="utf-8")
        assert product_keys() == ["real"]


class TestDeclarationContract:
    def test_accepts_a_well_formed_module(self, product_tree: Path) -> None:
        _add(product_tree, "good", _module("good"))
        loaded, failures = load_products()
        assert failures == []
        assert [product.declaration.key for product in loaded] == ["good"]

    def test_rejects_a_module_whose_key_does_not_match_its_folder(self, product_tree: Path) -> None:
        _add(product_tree, "folder_name", _module("something_else"))
        loaded, failures = load_products()
        assert loaded == []
        assert "declares key" in failures[0].reason

    def test_rejects_a_module_with_no_declaration(self, product_tree: Path) -> None:
        _add(product_tree, "bare", "def check(fetch_json):\n    return None\n")
        _, failures = load_products()
        assert "DECLARATION" in failures[0].reason

    def test_rejects_a_module_with_no_check(self, product_tree: Path) -> None:
        _add(product_tree, "nocheck", _module("nocheck").replace("def check(fetch_json):", "def other():"))
        _, failures = load_products()
        assert "check()" in failures[0].reason

    def test_one_broken_import_does_not_hide_the_others(self, product_tree: Path) -> None:
        # Forty vendors should not share a fate because one module has a typo.
        _add(product_tree, "broken", "raise RuntimeError('boom')\n")
        _add(product_tree, "healthy", _module("healthy"))
        loaded, failures = load_products()
        assert [product.declaration.key for product in loaded] == ["healthy"]
        assert failures[0].key == "broken"
        assert "import failed" in failures[0].reason

    def test_require_products_refuses_a_partial_view(self, product_tree: Path) -> None:
        _add(product_tree, "broken", "raise RuntimeError('boom')\n")
        with pytest.raises(DeclarationError, match="malformed"):
            require_products()


class TestShippedProducts:
    def test_every_shipped_module_satisfies_the_contract(self) -> None:
        # The property is asserted once here rather than in a test per product.
        loaded, failures = load_products()
        assert failures == [], f"malformed product modules: {failures}"
        assert loaded, "no product modules are shipped"

    def test_every_shipped_declaration_is_internally_consistent(self) -> None:
        for product in load_products()[0]:
            declaration = product.declaration
            assert isinstance(declaration, ProductDeclaration)
            if declaration.artifact_class is ArtifactClass.ARCHIVE:
                assert declaration.pdq_variable is None


class TestContainment:
    def test_a_module_that_exits_on_import_is_reported_not_obeyed(self, product_tree: Path) -> None:
        # A module-level sys.exit(), directly or from a vendor library's import-time check, is a
        # defect in this repository. Letting it through would discard every product already
        # loaded and exit outside this command's own code contract.
        _add(product_tree, "aaa", _module("aaa"))
        _add(product_tree, "exiting", "raise SystemExit(3)\n")
        loaded, failures = load_products()
        assert [product.declaration.key for product in loaded] == ["aaa"]
        assert failures[0].key == "exiting"

    def test_a_forgotten_init_is_loud_rather_than_silent(self, product_tree: Path) -> None:
        # Copying an existing module and missing the empty __init__.py is the realistic path, and
        # the outcome would otherwise be a product that is simply never tracked.
        folder = product_tree / "forgot_init"
        folder.mkdir()
        (folder / "product.py").write_text("DECLARATION = None\n", encoding="utf-8")
        _, failures = load_products()
        assert any("no __init__.py" in failure.reason for failure in failures)

    def test_a_scratch_directory_is_still_ignored(self, product_tree: Path) -> None:
        # The forgotten-init check must not turn every stray directory into a failure.
        _add(product_tree, "aaa", _module("aaa"))
        (product_tree / "scratch").mkdir()
        loaded, failures = load_products()
        assert [product.declaration.key for product in loaded] == ["aaa"]
        assert failures == []

    def test_two_modules_cannot_claim_the_same_consumer_pin(self, product_tree: Path) -> None:
        # Folder names cannot collide, but the key that reaches a console can. The symptom would
        # be a pin that flips between two products' versions.
        _add(product_tree, "aaa", _module("aaa", pin="Shared_Key"))
        _add(product_tree, "bbb", _module("bbb", pin="Shared_Key"))
        loaded, failures = load_products()
        assert [product.declaration.key for product in loaded] == ["aaa"]
        assert "already claims" in failures[0].reason
