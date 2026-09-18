"""Publishes verified vendor software to the application repository."""

from __future__ import annotations

from importlib.metadata import version

from ._contracts import ArtifactClass, Derivation, FrozenContract, Result, ResultCode
from .config import Settings, load, save_defaults
from .exceptions import DeclarationError, IdentityError, PublisherError
from .main import main
from .validators import validate_pin_key, validate_sha256, validate_version_component

__version__ = version("software-update-publisher")

__all__ = [
    "ArtifactClass",
    "DeclarationError",
    "Derivation",
    "FrozenContract",
    "IdentityError",
    "PublisherError",
    "Result",
    "ResultCode",
    "Settings",
    "__version__",
    "load",
    "main",
    "save_defaults",
    "validate_pin_key",
    "validate_sha256",
    "validate_version_component",
]
