"""Pure validation functions, called from model validators and from the publisher.

Each one answers a question that has already bitten this fleet, and each returns the validated
value so it can be used inline. They use ``re.fullmatch`` rather than an anchored ``re.match``
because ``$`` also matches immediately before a trailing newline, and a digest read from a
vendor checksum file arrives with exactly that.
"""

from __future__ import annotations

import re

_SHA256 = re.compile(r"[0-9a-f]{64}")
_PIN_KEY = re.compile(r"[A-Za-z0-9.+-]+_[A-Za-z0-9.+-]+")

# A version becomes a directory in the object key and is interpolated straight into a Windows
# deployment path, so it is restricted to a set that is safe in both. Every value in the
# consumer's live pin map satisfies it.
_VERSION_COMPONENT = re.compile(r"[A-Za-z0-9._+-]+")

# Windows refuses these as path components whatever their extension, so an object key built
# from one cannot be written to the repository volume the deployments read from.
_RESERVED_DEVICE_NAMES = frozenset(
    {"con", "prn", "aux", "nul"} | {f"com{digit}" for digit in "123456789"} | {f"lpt{digit}" for digit in "123456789"}
)

MUTABLE_VERSION_LABELS = frozenset({"current", "latest", "stable", "release", "newest", "edge"})
"""Words that must never appear in a version directory.

A mutable label means the bytes under a key change over time, which defeats the pinned digest,
the create-only write, and the property that an older version stays available for rollback. The
application repository already contains one such directory; the publisher must not create
another. Matched as a whole word or a dash/dot/underscore-delimited part, so ``latest-v22`` is
caught as well as ``latest``.
"""


def validate_sha256(digest: str) -> str:
    """Return *digest* if it is a lowercase 64-character hex string, and nothing else."""
    if not _SHA256.fullmatch(digest):
        message = f"not a lowercase 64-character sha256: {digest!r}"
        raise ValueError(message)
    return digest


def validate_version_component(version: str) -> str:
    """Return *version* if it is usable as an immutable object-key path component.

    Rejects anything that would break the path a deployment installs from, and anything that
    names a moving target rather than one build.
    """
    if not _VERSION_COMPONENT.fullmatch(version):
        message = f"version may contain only letters, digits, dot, underscore, plus and hyphen: {version!r}"
        raise ValueError(message)
    if version in {".", ".."} or version.endswith("."):
        message = f"version must not be a relative path component: {version!r}"
        raise ValueError(message)
    if version.split(".")[0].lower() in _RESERVED_DEVICE_NAMES:
        message = f"version must not be a reserved Windows device name: {version!r}"
        raise ValueError(message)
    if MUTABLE_VERSION_LABELS.intersection(re.split(r"[.\-_]", version.lower())):
        message = f"version must name a build, not a moving target: {version!r}"
        raise ValueError(message)
    return version


def validate_pin_key(key: str) -> str:
    """Return *key* if it has the consumer's ``Vendor-Name_Product-Name`` shape.

    The key is never derived from the bucket path -- several products spell the two differently
    -- so it is carried as declared data and only checked for shape here.
    """
    if not _PIN_KEY.fullmatch(key):
        message = f"not a Vendor_Product pin key: {key!r}"
        raise ValueError(message)
    return key
