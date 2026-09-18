"""Readers that establish what an artifact will register in Add/Remove Programs.

This is the shared half of the owner's split: identity comes out of the artifact wherever the
artifact declares it, and only where it genuinely cannot does a module supply its own scheme.
An MSI declares it in the Property table, so every MSI product is served by one reader here
rather than by a rule per product.

Why it is read at all, rather than transformed from the vendor's number: the two disagree often
enough that a transform is a liability. The AWS command line's installer declares a build its own
download pages do not mention; Python declares a version nobody would derive from `3.13.15`. An
extracted value cannot drift from what the machine will report, because it is what the machine
will report.
"""

from __future__ import annotations

import mmap
from pathlib import Path
from typing import Any

from pymsi import Package  # type: ignore[attr-defined]

from ._contracts import ArtifactClass, ArtifactIdentity
from .exceptions import IdentityError

_MSI_PROPERTIES = {
    "display_name": "ProductName",
    "publisher": "Manufacturer",
    "display_version": "ProductVersion",
    "product_code": "ProductCode",
    "upgrade_code": "UpgradeCode",
}


def read_msi_identity(artifact: Path) -> ArtifactIdentity:
    """Return the identity an MSI declares in its Property table.

    Uses a pure-Python reader so that a run needs no system package. Its output is checked against
    a recorded fixture by the test suite, because the library is pinned at a pre-release version
    and a silent change in what it returns would be a wrong pin rather than a crash.
    """
    # The file is opened here rather than by the library: its constructor opens the file and
    # then parses, so a parse failure leaves a handle owned by a half-built object that no
    # finally block can reach. Owning it means the close is deterministic on every path.
    with artifact.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as view:
        return _read_identity_from(artifact.name, view)


def _read_identity_from(name: str, view: mmap.mmap) -> ArtifactIdentity:
    """Read the identity out of an already-open package."""
    try:
        package = Package(view)
    except Exception as exc:
        # The realistic failures all land here rather than further down: a vendor serving an HTML
        # error page under an installer's name, a download truncated by a dropped connection, a
        # mirror returning something that is not an installer at all. The library's own message
        # for those names nothing about the artifact, so it is translated rather than surfaced.
        raise IdentityError(
            what=f"{name} could not be read as an installer package.",
            why=f"The file does not parse as one: {exc}",
            fix=(
                "Check what the download actually returned; an error page saved under an "
                "installer's name looks like this."
            ),
        ) from exc

    try:
        table: Any = package.get("Property")
        if table is None:
            # Reached by a structurally valid package that carries no Property table, which a
            # build pipeline can emit and a corrupt download cannot.
            raise IdentityError(
                what=f"{name} declares no Property table.",
                why="An MSI carries its identity there; this package has none.",
                fix="Inspect the package: a valid installer always has one.",
            )
        properties: dict[str, str] = {}
        for row in table.rows:
            # Read by column name rather than position: the row is a mapping, and depending on
            # column order would break silently if the library ever reordered it.
            prop: Any = row.get("Property")
            value: Any = row.get("Value")
            if prop is not None and value is not None:
                properties[str(prop)] = str(value)
    finally:
        package.close()  # type: ignore[no-untyped-call]

    identity = ArtifactIdentity(**{field: properties.get(name) for field, name in _MSI_PROPERTIES.items()})
    if identity.display_version is None:
        raise IdentityError(
            what=f"{name} declares no ProductVersion.",
            why="Add/Remove Programs takes its version from that property; without it there is no pin.",
            fix="Inspect the package: a valid installer always sets ProductVersion.",
        )
    return identity


_READERS = {ArtifactClass.MSI: read_msi_identity}


def read_identity(artifact_class: ArtifactClass, artifact: Path) -> ArtifactIdentity:
    """Return the identity for *artifact*, using the reader its class selects.

    A class with no shared reader raises rather than guessing. An archive has no Add/Remove
    Programs identity at all, and inventing one would produce a pin no machine can satisfy.
    """
    reader = _READERS.get(artifact_class)
    if reader is None:
        raise IdentityError(
            what=f"no shared identity reader for {artifact_class.value}.",
            why="Only artifact classes that declare their own registration can be read here.",
            fix="Have the product module supply its own identity, or publish it without a pin.",
        )
    return reader(artifact)
