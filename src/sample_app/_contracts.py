"""Frozen Pydantic contracts used by the sample package."""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, Self, TypeVar

from pydantic import BaseModel, ConfigDict, model_validator

from .validators import validate_repeat, validate_text

T = TypeVar("T")


class ResultCode(StrEnum):
    """Stable result codes for sample operations."""

    OK = "ok"
    INVALID = "invalid"


class TextRequest(BaseModel):
    """Input contract for the worked sample function."""

    model_config = ConfigDict(frozen=True)

    text: str
    repeat: int = 1

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        """Validate the full request with pure validation helpers."""
        validate_text(self.text)
        validate_repeat(self.repeat)
        return self


class Result(BaseModel, Generic[T]):
    """Small Result-style response shape."""

    model_config = ConfigDict(frozen=True)

    code: ResultCode
    value: T | None = None
    error: str | None = None
