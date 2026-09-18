"""Curated public API for the generic sample package."""

from __future__ import annotations

from ._contracts import Result, ResultCode, TextRequest
from .config import Settings, load, save_defaults
from .exceptions import InputValidationError, SampleAppError
from .main import build_message, main

__all__ = [
    "InputValidationError",
    "Result",
    "ResultCode",
    "SampleAppError",
    "Settings",
    "TextRequest",
    "build_message",
    "load",
    "main",
    "save_defaults",
]
