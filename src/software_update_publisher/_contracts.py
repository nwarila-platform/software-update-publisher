"""The data contract between a product module and the orchestrator.

One distinction runs through all of it: a vendor advertises one version and Windows
Add/Remove Programs reports another, they routinely differ, and only the second may become a
pin. ``VersionFacts`` therefore carries both and records which derivation produced the pin,
because a pin taken from a vendor page is a claim while a pin read out of the artifact is a
fact about the bytes that were published.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum, auto
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, ConfigDict, model_validator

T = TypeVar("T")


class FrozenContract(BaseModel):
    """Base for every contract model: immutable, and unknown fields are an error."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ArtifactClass(StrEnum):
    """What kind of file an artifact is, which decides how its identity is read.

    The class selects a shared reader. It is not cosmetic: MSI and BURN_EXE identities are
    extractable before install, ARCHIVE identities do not exist at all, and treating one as the
    other produces a confident wrong answer rather than a failure.
    """

    MSI = auto()
    BURN_EXE = auto()
    EXE = auto()
    ARCHIVE = auto()
    NUPKG = auto()


class Derivation(StrEnum):
    """Where a version string came from, which governs what may be done with it."""

    EXTRACTED = auto()
    """Read out of the artifact itself. A fact about the bytes we published."""

    DECLARED = auto()
    """Stated by the vendor. A fact about the vendor's claim, not about Add/Remove Programs."""

    MINTED = auto()
    """Invented here because the artifact carries no version. A convention of ours."""

    NONE = auto()
    """No honest version can be stated."""


class ResultCode(StrEnum):
    """Outcome of one product's pass through the lifecycle."""

    PUBLISHED = auto()
    UNCHANGED = auto()
    FAILED = auto()


class Result(FrozenContract, Generic[T]):
    """A value or an error, never both, and never neither."""

    code: ResultCode
    value: T | None = None
    error: str | None = None

    @model_validator(mode="after")
    def _exactly_one_outcome(self) -> Result[T]:
        """Reject the shapes the docstring forbids, rather than describing them."""
        if self.code is ResultCode.FAILED and self.error is None:
            message = "a failed result must carry its error"
            raise ValueError(message)
        if self.code is not ResultCode.FAILED and self.error is not None:
            message = f"a {self.code.value} result must not carry an error"
            raise ValueError(message)
        if self.code is ResultCode.PUBLISHED and self.value is None:
            message = "a published result must carry its value"
            raise ValueError(message)
        return self


class ProductDeclaration(FrozenContract):
    """What a product module states about itself, before anything is fetched.

    Validated by the loader ahead of any network call, because a wrong declaration is a defect in
    this repository rather than a condition of the outside world.
    """

    key: str
    """The module's folder name, and how a run refers to it."""

    vendor: str
    """The vendor's display name, as it appears in the repository path."""

    application: str
    """The application's display name, as it appears in the repository path."""

    pdq_variable: str | None
    """The consumer's pin key, copied verbatim from its variable map.

    Never derived: several products spell the path and the pin key differently. ``None`` means
    the artifact registers nothing in Add/Remove Programs and cannot hold a pin.
    """

    artifact_class: ArtifactClass
    """Selects the shared identity reader."""

    architecture: str
    """The architecture token used in the published file name."""

    @model_validator(mode="after")
    def _pin_key_only_where_a_pin_is_possible(self) -> ProductDeclaration:
        """An archive has no Add/Remove Programs identity, so it cannot name a pin."""
        if self.artifact_class is ArtifactClass.ARCHIVE and self.pdq_variable is not None:
            message = f"{self.key}: an archive registers nothing, so it cannot declare a pin key"
            raise ValueError(message)
        return self


class UpstreamCandidate(FrozenContract):
    """What a module's ``check()`` returns: where the artifact is, and what upstream calls it."""

    advertised_version: str
    """The version the vendor publishes. Used to detect change, never to pin."""

    download_url: str
    file_name: str
    """The name the artifact is published under, carrying the version and architecture."""

    vendor_digest: str | None = None
    """A SHA-256 the vendor published, when it publishes one."""


class ArtifactIdentity(FrozenContract):
    """What an identity reader found inside the artifact."""

    display_name: str | None = None
    publisher: str | None = None
    display_version: str | None = None
    product_code: str | None = None


class VersionFacts(FrozenContract):
    """Both versions, and how the pin was arrived at."""

    advertised: str
    """What the vendor said."""

    pin: str | None
    """What Add/Remove Programs will report, and the only value a pin may be set from."""

    derivation: Derivation
    evidence: str
    """Which reader and which field produced the pin, e.g. ``msi:ProductVersion``."""

    pin_comparable: bool
    """Whether a collection can compare this pin against installed software.

    False for anything that registers nothing, even when it has a perfectly good path version.
    This is what stops a compliance collection that silently never matches.
    """

    @model_validator(mode="after")
    def _a_pin_must_be_a_fact_or_absent(self) -> VersionFacts:
        """Keep the vocabulary honest: minted and none never carry a pin."""
        if self.derivation in {Derivation.MINTED, Derivation.NONE} and self.pin is not None:
            message = f"a {self.derivation.value} version must not present a pin"
            raise ValueError(message)
        if self.derivation is Derivation.EXTRACTED and self.pin is None:
            message = "an extracted version must carry the value that was extracted"
            raise ValueError(message)
        if self.pin_comparable and self.pin is None:
            message = "a pin cannot be comparable when there is no pin"
            raise ValueError(message)
        return self


@runtime_checkable
class ProductModule(Protocol):
    """What every product module provides.

    Stated as a protocol rather than "a module object" because that is the whole dependency: the
    loader needs a declaration and a way to ask upstream, and nothing else. It also lets a test
    supply a stand-in without importing anything from disk.
    """

    DECLARATION: ProductDeclaration

    def check(self, fetch_json: Callable[[str], Any]) -> UpstreamCandidate:
        """Ask upstream what this product is at, using the fetcher it is handed."""
        ...
