"""The stable data contract between a product module and the orchestrator.

The types here exist to keep one distinction impossible to lose: the version a vendor
advertises and the version Windows Add/Remove Programs will report are different strings, and
only the second may become a pin. Carrying them in one field is what allowed a live pin to name
a version no artifact in the repository can produce.
"""

from __future__ import annotations

from enum import StrEnum, auto
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

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
    """A value or an error, never both silently."""

    code: ResultCode
    value: T | None = None
    error: str | None = None
