"""Google Chrome, Extended Stable channel.

The fleet tracks Chrome's Extended Stable train, not Stable: the pinned version is on the 152
line while Stable has moved to 154. That choice is stated here with no default, because the two
channels are served from different URLs and pairing one channel's version with the other's
artifact publishes a binary that does not match its own pin.

Chrome is a plain MSI. Its Property table carries the full four-field version, so the pin is
extracted rather than transformed -- which matters here more than most, because the channel feed
and the artifact do not always agree: the feed reported 152.0.7977.134 while the artifact it
serves declared 152.0.7977.130. Pinning the feed's number would name a version no published file
produces.
"""

from __future__ import annotations

from typing import Any, Final

from ..._contracts import ArtifactClass, ProductDeclaration, UpstreamCandidate

DECLARATION: Final = ProductDeclaration(
    key="google_chrome",
    vendor="Google LLC",
    application="Google Chrome",
    pdq_variable="Google-LLC_Google-Chrome",
    artifact_class=ArtifactClass.MSI,
    architecture="x64",
)

CHANNEL: Final = "extended"
"""Extended Stable. Changing this changes which train the fleet runs."""

VERSION_FEED: Final = (
    f"https://versionhistory.googleapis.com/v1/chrome/platforms/win64/channels/{CHANNEL}/versions?pageSize=1"
)

DOWNLOAD_URL: Final = "https://dl.google.com/dl/chrome/install/extended/googlechromestandaloneenterprise64.msi"
"""The Extended Stable enterprise MSI.

The URL without the ``extended`` segment serves Stable. Both respond 200, so a mistake here is
silent until someone compares the version inside the file.
"""


def parse_feed(payload: dict[str, Any]) -> str:
    """Return the version the channel feed reports."""
    versions = payload.get("versions") or []
    if not versions or "version" not in versions[0]:
        message = f"version feed returned no versions for the {CHANNEL} channel"
        raise ValueError(message)
    return str(versions[0]["version"])


def check(fetch_json: Any) -> UpstreamCandidate:
    """Ask the channel feed what Chrome is at, and say where the artifact is.

    ``advertised_version`` is what the feed says and is used to notice change. The published pin
    comes from the downloaded file, not from here. Google publishes no digest for this URL, so
    none is declared: the release document records that the digest was computed from the bytes
    we fetched rather than attested by the vendor.
    """
    advertised = parse_feed(fetch_json(VERSION_FEED))
    return UpstreamCandidate(
        advertised_version=advertised,
        download_url=DOWNLOAD_URL,
        file_name=f"Google-LLC_Google-Chrome_{advertised}_x64.msi",
        vendor_digest=None,
    )
