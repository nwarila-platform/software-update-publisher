"""Google Chrome, Extended Stable channel.

The channel is a DECISION recorded here, not a property read off the fleet. The consumer's pin
``152.0.7977.76`` was released on both the Stable and the Extended Stable trains, and nothing
in the artifact distinguishes them -- the Stable, Extended and pinned MSIs all share one
UpgradeCode. The simpler reading of the evidence is that the pin was set when Stable was 152
and never moved.

Extended Stable is the ratified choice for this fleet (2026-09-18): fewer version changes, at
the cost of running roughly eight weeks behind the Stable train on non-security fixes. Security
fixes are delivered on both. Revisiting that trade means changing this one line, which is
deliberately the only place that decides it.

It is stated with no default because the two channels are served from different URLs and
pairing one channel's version with the other's artifact publishes a binary that contradicts
its own pin.

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

    ``advertised_version`` is what the feed says and is used to notice change. It is not the
    published version and never becomes part of an object key: for this product the two have
    been measured to differ. Google publishes no digest for this URL, so none is declared, and
    the release document records the digest as computed from the bytes fetched rather than
    attested by the vendor.
    """
    return UpstreamCandidate(
        advertised_version=parse_feed(fetch_json(VERSION_FEED)),
        download_url=DOWNLOAD_URL,
        vendor_digest=None,
    )
