"""Frozen pydantic-settings configuration API."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_GREETING = "Hello"
_DEFAULT_NAME = "template"
_ENV_PREFIX = "SAMPLE_APP_"


class Settings(BaseSettings):
    """Runtime settings for the generic sample package."""

    model_config = SettingsConfigDict(env_prefix=_ENV_PREFIX, frozen=True)

    greeting: str = _DEFAULT_GREETING
    default_name: str = _DEFAULT_NAME


def load() -> Settings:
    """Load settings from the process environment."""
    return Settings()


def save_defaults(path: str | Path = "sample_app.defaults.env") -> Path:
    """Write a dotenv-style file containing the package defaults."""
    destination = Path(path)
    defaults = Settings(greeting=_DEFAULT_GREETING, default_name=_DEFAULT_NAME)
    destination.write_text(
        f"{_ENV_PREFIX}GREETING={defaults.greeting}\n{_ENV_PREFIX}DEFAULT_NAME={defaults.default_name}\n",
        encoding="utf-8",
    )
    return destination
