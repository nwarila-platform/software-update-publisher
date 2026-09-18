"""Tests for the package's public surface."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from software_update_publisher import (
    ArtifactClass,
    DeclarationError,
    Derivation,
    PublisherError,
    Result,
    ResultCode,
    Settings,
    load,
    main,
    save_defaults,
    validate_pin_key,
    validate_sha256,
    validate_version_component,
)
from software_update_publisher.validators import MUTABLE_VERSION_WORDS

_DIGEST = "856dbe3dd4544d4b9ae1f382ee51f2a5f25f41714c462fa4afcff9743cc85eb9"


class TestExceptions:
    def test_message_names_what_why_and_fix(self) -> None:
        error = DeclarationError(what="a", why="b", fix="c")
        assert str(error) == "What: a Why: b Fix: c"
        assert error.what == "a"

    def test_declaration_error_is_a_value_error(self) -> None:
        # Callers that already handle bad input keep working without knowing this hierarchy.
        assert issubclass(DeclarationError, ValueError)
        assert issubclass(DeclarationError, PublisherError)


class TestContracts:
    def test_result_is_immutable(self) -> None:
        result = Result[str](code=ResultCode.PUBLISHED, value="0.31.8.0")
        with pytest.raises(ValidationError):
            result.value = "other"

    def test_unknown_fields_are_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Result[str](code=ResultCode.UNCHANGED, unexpected=None)  # type: ignore[call-arg]

    def test_every_artifact_class_has_a_derivation_story(self) -> None:
        assert ArtifactClass.MSI in set(ArtifactClass)
        assert {"extracted", "declared", "minted", "none"} == {d.value for d in Derivation}


class TestValidators:
    def test_accepts_a_real_pinned_digest(self) -> None:
        assert validate_sha256(_DIGEST) == _DIGEST

    @pytest.mark.parametrize("bad", [_DIGEST.upper(), _DIGEST[:63], f"{_DIGEST}a", "", "zz"])
    def test_rejects_anything_the_consumer_could_not_verify(self, bad: str) -> None:
        with pytest.raises(ValueError, match="sha256"):
            validate_sha256(bad)

    @pytest.mark.parametrize("version", ["26.02.00.0", "3.13.15150.0", "0.31.8.0", "retrieved-2026-09-18"])
    def test_accepts_versions_that_name_one_build(self, version: str) -> None:
        assert validate_version_component(version) == version

    @pytest.mark.parametrize("word", sorted(MUTABLE_VERSION_WORDS))
    def test_rejects_a_moving_target_as_a_version(self, word: str) -> None:
        # A mutable directory changes the bytes under a pinned key, which defeats the digest.
        with pytest.raises(ValueError, match="moving target"):
            validate_version_component(word)

    @pytest.mark.parametrize("bad", ["", " 1.0", "1.0 ", "a/b", "a\\b"])
    def test_rejects_versions_that_would_break_a_deployment_path(self, bad: str) -> None:
        with pytest.raises(ValueError, match="non-empty and unpadded|path separator"):
            validate_version_component(bad)

    @pytest.mark.parametrize(
        "key",
        ["Igor-Pavlov_7-Zip", "Prometheus-Community_Windows-Exporter", "Node.js-Foundation_Node.js-24"],
    )
    def test_accepts_real_consumer_pin_keys(self, key: str) -> None:
        assert validate_pin_key(key) == key

    @pytest.mark.parametrize("bad", ["NoUnderscore", "a b_c", "", "_leading"])
    def test_rejects_keys_the_consumer_would_not_recognise(self, bad: str) -> None:
        with pytest.raises(ValueError, match="pin key"):
            validate_pin_key(bad)


class TestSettings:
    def test_bucket_has_no_default_because_it_names_an_account(self) -> None:
        assert Settings().repository_bucket == ""

    def test_reads_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SUP_REPOSITORY_BUCKET", "example-apprepo")
        assert load().repository_bucket == "example-apprepo"

    def test_settings_are_frozen(self) -> None:
        with pytest.raises(ValidationError):
            Settings().region = "eu-west-1"

    def test_save_defaults_names_every_setting(self, tmp_path: Path) -> None:
        written = save_defaults(tmp_path / "defaults.env")
        body = written.read_text(encoding="utf-8")
        assert "SUP_REPOSITORY_BUCKET=" in body
        assert "SUP_REGION=us-east-1" in body


class TestCli:
    def test_show_config_needs_no_bucket_and_no_network(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["--show-config"]) == 0
        assert "region: us-east-1" in capsys.readouterr().out

    def test_missing_bucket_fails_loudly_and_names_the_variable(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.delenv("SUP_REPOSITORY_BUCKET", raising=False)
        assert main([]) == 2
        assert "SUP_REPOSITORY_BUCKET" in capsys.readouterr().err

    def test_runs_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SUP_REPOSITORY_BUCKET", "example-apprepo")
        assert main([]) == 0

    def test_version_flag_reports_the_distribution_version(self) -> None:
        with pytest.raises(SystemExit) as exit_info:
            main(["--version"])
        assert exit_info.value.code == 0

    def test_module_is_runnable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["software_update_publisher", "--show-config"])
        with pytest.raises(SystemExit) as exit_info:
            runpy.run_module("software_update_publisher", run_name="__main__")
        assert exit_info.value.code == 0
