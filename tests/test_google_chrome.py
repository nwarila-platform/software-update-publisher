"""Tests for the Google Chrome product module.

Offline: the upstream response is a recorded fixture, so the suite never depends on a vendor
being reachable or on what they published this morning.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from software_update_publisher._contracts import ArtifactClass
from software_update_publisher.products.google_chrome import DECLARATION, check
from software_update_publisher.products.google_chrome import product as chrome

_FIXTURE = Path(chrome.__file__).parent / "fixtures" / "version_feed.json"


def _recorded() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return payload


class TestDeclaration:
    def test_declares_the_consumer_pin_key_verbatim(self) -> None:
        # Not derived: the bucket path and the pin key are spelled differently for several
        # products, so this value is copied from the consumer rather than computed.
        assert DECLARATION.pdq_variable == "Google-LLC_Google-Chrome"
        assert DECLARATION.vendor == "Google LLC"
        assert DECLARATION.application == "Google Chrome"

    def test_is_an_msi_so_its_identity_is_extractable(self) -> None:
        assert DECLARATION.artifact_class is ArtifactClass.MSI


class TestChannel:
    def test_tracks_extended_stable_not_stable(self) -> None:
        # The fleet's pin is on the 152 line while Stable has moved on; pairing one channel's
        # version with the other's artifact publishes a binary that contradicts its own pin.
        assert chrome.CHANNEL == "extended"
        assert "/channels/extended/" in chrome.VERSION_FEED

    def test_downloads_the_extended_artifact(self) -> None:
        # The same URL without this segment serves Stable and also responds 200, so the mistake
        # would be silent until someone read the version out of the file.
        assert "/install/extended/" in chrome.DOWNLOAD_URL


class TestCheck:
    def test_reports_the_version_the_feed_carries(self) -> None:
        candidate = check(lambda _url: _recorded())
        assert candidate.advertised_version == _recorded()["versions"][0]["version"]

    def test_names_the_file_after_the_advertised_version(self) -> None:
        candidate = check(lambda _url: _recorded())
        assert candidate.file_name == f"Google-LLC_Google-Chrome_{candidate.advertised_version}_x64.msi"

    def test_declares_no_vendor_digest_because_google_publishes_none_here(self) -> None:
        # Recorded rather than assumed: the release document must say the digest was computed
        # from the bytes fetched, not attested by the vendor.
        assert check(lambda _url: _recorded()).vendor_digest is None

    def test_asks_the_extended_channel(self) -> None:
        seen: list[str] = []

        def fetch(url: str) -> dict[str, Any]:
            seen.append(url)
            return _recorded()

        check(fetch)
        assert seen == [chrome.VERSION_FEED]

    @pytest.mark.parametrize("payload", [{}, {"versions": []}, {"versions": [{}]}])
    def test_refuses_a_feed_that_carries_no_version(self, payload: dict[str, Any]) -> None:
        with pytest.raises(ValueError, match="no versions"):
            check(lambda _url: payload)
