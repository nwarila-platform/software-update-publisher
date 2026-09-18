"""Frozen pydantic-settings configuration API."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PREFIX = "SUP_"
_DEFAULT_REGION = "us-east-1"


class Settings(BaseSettings):
    """Runtime settings, read from the process environment.

    The bucket carries an account identifier, so it has no default and no value in this
    repository: it arrives from the environment at run time, the same way every other consumer
    of that bucket receives it.
    """

    model_config = SettingsConfigDict(env_prefix=_ENV_PREFIX, frozen=True)

    repository_bucket: str = ""
    region: str = _DEFAULT_REGION


def load() -> Settings:
    """Load settings from the process environment."""
    return Settings()


def save_defaults(path: str | Path = "software-update-publisher.defaults.env") -> Path:
    """Write a dotenv-style file naming every setting and its default."""
    destination = Path(path)
    defaults = Settings()
    lines = [f"{_ENV_PREFIX}{name.upper()}={getattr(defaults, name)}" for name in Settings.model_fields]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
