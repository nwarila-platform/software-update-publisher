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
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .validators import validate_pin_key, validate_version_component

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

    @field_validator("pdq_variable")
    @classmethod
    def _pin_key_has_the_consumer_shape(cls, value: str | None) -> str | None:
        """A typo here is a compliance key that silently matches nothing."""
        return None if value is None else validate_pin_key(value)

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
    """The version the vendor publishes.

    Used to notice that something changed, and recorded for the audit trail. Never used to
    build an object key or a pin: the key carries the version the artifact declares, which is
    not known until it has been downloaded and read.
    """

    download_url: str

    vendor_digest: str | None = None
    """A SHA-256 the vendor published, when it publishes one."""

    @field_validator("advertised_version")
    @classmethod
    def _version_is_usable_as_a_path_component(cls, value: str) -> str:
        """Refuse a vendor value that could not become a directory, at the boundary.

        A feed that returns 'latest' or a traversal sequence is not hypothetical: it is what a
        changed or hijacked endpoint looks like, and this is the last point before the value
        reaches a key.
        """
        return validate_version_component(value)


class ArtifactIdentity(FrozenContract):
    """What an identity reader found inside the artifact."""

    display_name: str | None = None
    publisher: str | None = None
    display_version: str | None = None
    product_code: str | None = None
    upgrade_code: str | None = None
    """The upgrade family, which is stable across versions where the product code is not."""


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
