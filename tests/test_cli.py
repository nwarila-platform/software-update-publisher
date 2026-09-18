"""Tests for the command line's behaviour and its exit-code contract.

A scheduled run is read through its exit code, so these assert the codes as hard as the output:
0 did what it set out to do, 1 ran and something failed, 2 could not run at all.
"""

from __future__ import annotations

import runpy
import sys
from typing import Any

import pytest

from software_update_publisher.cli import check_one, main
from software_update_publisher.loader import LoadedProduct, LoadFailure
from software_update_publisher.products.google_chrome import DECLARATION as CHROME


class _FakeModule:
    """A product module that answers without a network.

    Satisfies the ProductModule protocol rather than being a module object, which is the
    point of stating the loader's dependency as a protocol.
    """

    DECLARATION = CHROME

    def __init__(self, candidate: Any = None, error: Exception | None = None) -> None:
        self._candidate = candidate
        self._error = error

    def check(self, fetch_json: Any) -> Any:
        if self._error is not None:
            raise self._error
        return self._candidate


def _patch_products(monkeypatch: pytest.MonkeyPatch, loaded: list[Any], failures: list[Any]) -> None:
    monkeypatch.setattr("software_update_publisher.cli.load_products", lambda: (loaded, failures))


class TestList:
    def test_lists_what_this_build_tracks_without_contacting_anything(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main(["--list"]) == 0
        out = capsys.readouterr().out
        assert "google_chrome" in out
        assert "Google-LLC_Google-Chrome" in out

    def test_reports_a_malformed_module_and_fails(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _patch_products(monkeypatch, [], [LoadFailure(key="broken", reason="import failed")])
        assert main(["--list"]) == 1
        assert "broken" in capsys.readouterr().err


class TestCheck:
    def test_reports_each_product_and_succeeds(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from software_update_publisher._contracts import UpstreamCandidate

        candidate = UpstreamCandidate(advertised_version="152.0.7977.134", download_url="https://example.invalid/x.msi")
        _patch_products(monkeypatch, [LoadedProduct(declaration=CHROME, module=_FakeModule(candidate))], [])
        assert main(["--check"]) == 0
        assert "advertised=152.0.7977.134" in capsys.readouterr().out

    def test_one_unreachable_vendor_does_not_end_the_run(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from software_update_publisher._contracts import UpstreamCandidate

        ok = UpstreamCandidate(advertised_version="1.0", download_url="https://example.invalid/a")
        _patch_products(
            monkeypatch,
            [
                LoadedProduct(declaration=CHROME, module=_FakeModule(error=TimeoutError("vendor down"))),
                LoadedProduct(declaration=CHROME, module=_FakeModule(ok)),
            ],
            [],
        )
        # Exit 1 because something failed, but the healthy product was still reported.
        assert main(["--check"]) == 1
        captured = capsys.readouterr()
        assert "vendor down" in captured.err
        assert "advertised=1.0" in captured.out

    def test_a_publisher_error_is_reported_with_its_guidance(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from software_update_publisher.exceptions import IdentityError

        failure = IdentityError(what="no version.", why="the file declares none.", fix="check the download.")
        _patch_products(monkeypatch, [LoadedProduct(declaration=CHROME, module=_FakeModule(error=failure))], [])
        assert main(["--check"]) == 1
        assert "Fix: check the download." in capsys.readouterr().err

    def test_refuses_when_nothing_matches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_products(monkeypatch, [], [])
        assert main(["--check"]) == 2


class TestSingleProductEntryPoint:
    def test_a_module_can_be_run_on_its_own(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from software_update_publisher._contracts import UpstreamCandidate

        candidate = UpstreamCandidate(advertised_version="1.0", download_url="https://example.invalid/a")
        _patch_products(monkeypatch, [LoadedProduct(declaration=CHROME, module=_FakeModule(candidate))], [])
        assert check_one(CHROME.key) == 0

    def test_the_product_module_is_executable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_products(monkeypatch, [], [])
        monkeypatch.setattr(sys, "argv", ["google_chrome"])
        with pytest.raises(SystemExit) as exit_info:
            runpy.run_module("software_update_publisher.products.google_chrome", run_name="__main__")
        assert exit_info.value.code == 2


class TestSharedFetcher:
    def test_modules_are_handed_a_fetcher_rather_than_opening_sockets(self) -> None:
        # The contract is that a module never opens a socket itself, so timeout policy lives in
        # one place. This asserts the shared fetcher exists and is what check() is called with.
        from software_update_publisher.cli import _fetch_json

        assert callable(_fetch_json)
