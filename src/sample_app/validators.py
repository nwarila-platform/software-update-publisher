"""Pure validation helpers for sample contracts."""

from __future__ import annotations

from .exceptions import InputValidationError


def validate_text(value: str) -> str:
    """Validate that text contains visible content."""
    if not value.strip():
        raise InputValidationError(
            what="Input text is blank.",
            why="The sample message needs visible text to render.",
            fix="Pass a non-blank text value.",
        )
    return value


def validate_repeat(value: int) -> int:
    """Validate that repeat is a positive count."""
    if value < 1:
        raise InputValidationError(
            what="Repeat count is not positive.",
            why="The sample message cannot be rendered zero or negative times.",
            fix="Pass a repeat value of 1 or greater.",
        )
    return value
