"""Tests for the generic sample package skeleton."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from sample_app import (
    InputValidationError,
    ResultCode,
    Settings,
    TextRequest,
    build_message,
    load,
    main,
    save_defaults,
)
from sample_app.validators import validate_repeat, validate_text


def test_build_message_returns_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAMPLE_APP_GREETING", "Hi")

    result = build_message("Ada", repeat=2)

    assert result.code is ResultCode.OK
    assert result.value == "Hi, Ada! Hi, Ada!"
    assert result.error is None


def test_build_message_returns_invalid_result() -> None:
    result = build_message(" ", repeat=1)

    assert result.code is ResultCode.INVALID
    assert result.value is None
    assert result.error is not None
    assert "Input text is blank" in result.error


def test_build_message_rejects_invalid_repeat() -> None:
    result = build_message("Ada", repeat=0)

    assert result.code is ResultCode.INVALID
    assert result.value is None
    assert result.error is not None
    assert "Repeat count is not positive" in result.error


def test_validators_accept_valid_values() -> None:
    assert validate_text("template") == "template"
    assert validate_repeat(1) == 1


def test_validators_reject_invalid_values() -> None:
    with pytest.raises(InputValidationError) as text_error:
        validate_text("")
    assert text_error.value.fix == "Pass a non-blank text value."

    with pytest.raises(InputValidationError) as repeat_error:
        validate_repeat(0)
    assert repeat_error.value.why == "The sample message cannot be rendered zero or negative times."


def test_contract_models_are_frozen() -> None:
    request = TextRequest(text="fixed")
    field = "text"

    with pytest.raises(ValidationError):
        setattr(request, field, "changed")


def test_settings_are_frozen() -> None:
    settings = Settings()
    field = "greeting"

    with pytest.raises(ValidationError):
        setattr(settings, field, "Changed")


def test_typed_exception_fields() -> None:
    error = InputValidationError(what="What happened.", why="Why it happened.", fix="How to fix it.")

    assert error.what == "What happened."
    assert error.why == "Why it happened."
    assert error.fix == "How to fix it."
    assert "What happened" in str(error)


def test_load_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAMPLE_APP_DEFAULT_NAME", "env-user")

    assert load().default_name == "env-user"


def test_save_defaults_writes_env_file(tmp_path: Path) -> None:
    destination = save_defaults(tmp_path / "defaults.env")

    assert destination.read_text(encoding="utf-8") == "SAMPLE_APP_GREETING=Hello\nSAMPLE_APP_DEFAULT_NAME=template\n"


def test_main_prints_demo_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["Grace", "--repeat", "1"])

    assert exit_code == 0
    assert capsys.readouterr().out == "Hello, Grace!\n"


def test_main_returns_nonzero_for_invalid_input(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["", "--repeat", "1"])

    assert exit_code == 2
    assert "Input text is blank" in capsys.readouterr().err


def test_python_m_self_demo(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["sample_app"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("sample_app", run_name="__main__")

    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "Hello, template!\n"
