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
}


def read_msi_identity(artifact: Path) -> ArtifactIdentity:
    """Return the identity an MSI declares in its Property table.

    Uses a pure-Python reader so that a run needs no system package. Its output is checked
    against a recorded fixture by the test suite, because the library is pinned at a pre-release
    version and a silent change in what it returns would be a wrong pin rather than a crash.
    """
    package = Package(artifact)
    try:
        table: Any = package.get("Property")
        if table is None:
            raise IdentityError(
                what=f"{artifact.name} declares no Property table.",
                why="An MSI carries its identity there; this file does not have one.",
                fix="Confirm the download is an MSI and not an error page saved under that name.",
            )
        properties: dict[str, str] = {}
        for row in table.rows:
            values = list(row.values()) if hasattr(row, "values") else list(row)
            if len(values) >= 2:
                properties[str(values[0])] = str(values[1])
    finally:
        package.close()  # type: ignore[no-untyped-call]

    identity = ArtifactIdentity(**{field: properties.get(name) for field, name in _MSI_PROPERTIES.items()})
    if identity.display_version is None:
        raise IdentityError(
            what=f"{artifact.name} declares no ProductVersion.",
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
