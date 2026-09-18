"""Pure validation functions, called from model validators and from the publisher.

Each one answers a question that has bitten this fleet in production, and each returns the
validated value so it can be used inline.
"""

from __future__ import annotations

import re

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PIN_KEY = re.compile(r"^[A-Za-z0-9.+-]+_[A-Za-z0-9.+-]+$")

MUTABLE_VERSION_WORDS = frozenset({"current", "latest", "stable", "release", "newest"})
"""Words that must never be a version directory.

A mutable version label means the bytes under a key change over time, which defeats the pinned
digest, the create-only write, and the property that an older version stays available for
rollback. The application repository already contains one such directory; the publisher must
not create another.
"""


def validate_sha256(digest: str) -> str:
    """Return *digest* if it is a lowercase 64-character hex string."""
    if not _SHA256.match(digest):
        message = f"not a lowercase 64-character sha256: {digest!r}"
        raise ValueError(message)
    return digest


def validate_version_component(version: str) -> str:
    """Return *version* if it is usable as an immutable object-key component.

    A deployment interpolates this string straight into a file path, so whitespace and path
    separators are rejected outright, and a mutable word is rejected because the key it builds
    would not stay the same bytes.
    """
    if not version or version.strip() != version:
        message = f"version must be non-empty and unpadded: {version!r}"
        raise ValueError(message)
    if any(character in version for character in "/\\"):
        message = f"version must not contain a path separator: {version!r}"
        raise ValueError(message)
    if version.lower() in MUTABLE_VERSION_WORDS:
        message = f"version must name a build, not a moving target: {version!r}"
        raise ValueError(message)
    return version


def validate_pin_key(key: str) -> str:
    """Return *key* if it has the consumer's ``Vendor-Name_Product-Name`` shape.

    The key is never derived from the bucket path: several products spell them differently, so
    it is carried as declared data and only checked for shape here.
    """
    if not _PIN_KEY.match(key):
        message = f"not a Vendor_Product pin key: {key!r}"
        raise ValueError(message)
    return key
