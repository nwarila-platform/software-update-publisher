"""The vocabulary the product-module contract is built from.

This file holds the enumerations and the result shape. The artifact and version models that
use them arrive with the orchestrator, because a model with no producer and no consumer is a
guess about an interface rather than a contract.

What the vocabulary already fixes is the distinction the repository exists to keep: a vendor
advertises one version and Windows Add/Remove Programs reports another, and only the second
may become a pin. ``Derivation`` is how an artifact will say which of the two it carries.
"""

from __future__ import annotations

from enum import StrEnum, auto
from typing import Generic, TypeVar

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
