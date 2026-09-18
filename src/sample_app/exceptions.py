"""Typed exception hierarchy for the sample package."""

from __future__ import annotations


class SampleAppError(Exception):
    """Base exception carrying What, Why, and Fix details."""

    what: str
    why: str
    fix: str

    def __init__(self, *, what: str, why: str, fix: str) -> None:
        self.what = what
        self.why = why
        self.fix = fix
        super().__init__(f"What: {what} Why: {why} Fix: {fix}")


class InputValidationError(SampleAppError, ValueError):
    """Raised when a sample input contract is invalid."""
