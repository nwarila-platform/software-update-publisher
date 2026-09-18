"""Tests for the package's public surface."""

from __future__ import annotations

import importlib
import runpy
import sys
from importlib import metadata
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
from software_update_publisher.validators import MUTABLE_VERSION_LABELS

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

    def test_the_vocabulary_matches_the_design(self) -> None:
        assert {"msi", "burn_exe", "exe", "archive", "nupkg"} == {c.value for c in ArtifactClass}
        assert {"extracted", "declared", "minted", "none"} == {d.value for d in Derivation}

    @pytest.mark.parametrize(
        ("code", "value", "error"),
        [
            (ResultCode.PUBLISHED, "v", "boom"),
            (ResultCode.PUBLISHED, None, None),
            (ResultCode.FAILED, None, None),
            (ResultCode.UNCHANGED, None, "boom"),
        ],
    )
    def test_a_result_cannot_claim_two_outcomes_at_once(
        self, code: ResultCode, value: str | None, error: str | None
    ) -> None:
        with pytest.raises(ValidationError):
            Result[str](code=code, value=value, error=error)


class TestValidators:
    def test_accepts_a_real_pinned_digest(self) -> None:
        assert validate_sha256(_DIGEST) == _DIGEST

    @pytest.mark.parametrize(
        "bad",
        [
            _DIGEST.upper(),
            _DIGEST[:63],
            f"{_DIGEST}a",
            "",
            "zz",
            # A digest read from a vendor checksum file arrives with a trailing newline, and
            # regex "$" matches before one. Returning it would produce a pin that never matches.
            f"{_DIGEST}\n",
            f"{_DIGEST} ",
            f" {_DIGEST}",
            f"{_DIGEST}\r\n",
        ],
    )
    def test_rejects_anything_the_consumer_could_not_verify(self, bad: str) -> None:
        with pytest.raises(ValueError, match="sha256"):
            validate_sha256(bad)

    @pytest.mark.parametrize("version", ["26.02.00.0", "3.13.15150.0", "0.31.8.0", "retrieved-2026-09-18"])
    def test_accepts_versions_that_name_one_build(self, version: str) -> None:
        assert validate_version_component(version) == version

    @pytest.mark.parametrize("word", sorted(MUTABLE_VERSION_LABELS))
    def test_rejects_a_moving_target_as_a_version(self, word: str) -> None:
        # A mutable directory changes the bytes under a pinned key, which defeats the digest.
        with pytest.raises(ValueError, match="moving target"):
            validate_version_component(word)

    @pytest.mark.parametrize("embedded", ["latest-v22.x", "current-2026", "v1_stable", "edge.3"])
    def test_rejects_a_moving_label_embedded_in_a_version(self, embedded: str) -> None:
        with pytest.raises(ValueError, match="moving target"):
            validate_version_component(embedded)

    @pytest.mark.parametrize("traversal", [".", ".."])
    def test_rejects_relative_path_components(self, traversal: str) -> None:
        # "/" is already rejected, so ".." would collapse a level using the separators the key
        # is built from: <vendor>/<application>/<version>/.
        with pytest.raises(ValueError, match="relative path component"):
            validate_version_component(traversal)

    @pytest.mark.parametrize("reserved", ["CON", "NUL", "CON.1", "lpt9.0"])
    def test_rejects_reserved_windows_device_names(self, reserved: str) -> None:
        # The artifact lands on a Windows repository volume; these are not legal there.
        with pytest.raises(ValueError, match="reserved Windows device name"):
            validate_version_component(reserved)

    @pytest.mark.parametrize(
        "bad", ["", " 1.0", "1.0 ", "a/b", "a\\b", "ver*1", "v1:beta", "a\nb", "1.0.", "a?b", "a|b"]
    )
    def test_rejects_versions_that_would_break_a_deployment_path(self, bad: str) -> None:
        # Every rejection message names the offending value, so one pattern covers the set.
        with pytest.raises(ValueError, match="version"):
            validate_version_component(bad)

    @pytest.mark.parametrize(
        "key",
        ["Igor-Pavlov_7-Zip", "Prometheus-Community_Windows-Exporter", "Node.js-Foundation_Node.js-24"],
    )
    def test_accepts_real_consumer_pin_keys(self, key: str) -> None:
        assert validate_pin_key(key) == key

    @pytest.mark.parametrize("bad", ["NoUnderscore", "a b_c", "", "_leading", "Igor-Pavlov_7-Zip\n"])
    def test_rejects_keys_the_consumer_would_not_recognise(self, bad: str) -> None:
        with pytest.raises(ValueError, match="pin key"):
            validate_pin_key(bad)


class TestSettings:
    def test_bucket_defaults_empty_so_no_account_appears_in_this_repository(self) -> None:
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
        # Every field, not a hand-kept list that silently omits the next one added.
        for name in Settings.model_fields:
            assert f"SUP_{name.upper()}=" in body


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

    def test_a_configured_run_refuses_rather_than_reporting_false_success(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv("SUP_REPOSITORY_BUCKET", "example-apprepo")
        assert main([]) == 2
        assert "orchestrator is not implemented" in capsys.readouterr().err

    def test_version_flag_prints_the_package_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        from software_update_publisher import __version__

        with pytest.raises(SystemExit) as exit_info:
            main(["--version"])
        assert exit_info.value.code == 0
        assert __version__ in capsys.readouterr().out

    def test_module_is_runnable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["software_update_publisher", "--show-config"])
        with pytest.raises(SystemExit) as exit_info:
            runpy.run_module("software_update_publisher", run_name="__main__")
        assert exit_info.value.code == 0


class TestVersionResolution:
    def test_reports_the_installed_distribution_version(self) -> None:
        from software_update_publisher import _version

        assert _version.__version__ == metadata.version("software-update-publisher")

    def test_falls_back_when_the_tree_was_never_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # A container that copies src/ without installing, or any PYTHONPATH=src invocation, has
        # no distribution metadata. Importing must still work rather than raising at import time.
        def _missing(name: str) -> str:
            raise metadata.PackageNotFoundError(name)

        monkeypatch.setattr(metadata, "version", _missing)
        module = importlib.reload(importlib.import_module("software_update_publisher._version"))
        try:
            assert module.__version__ == "0.0.0+source"
        finally:
            monkeypatch.undo()
            importlib.reload(module)
