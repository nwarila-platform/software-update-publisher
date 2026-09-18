"""Tests for scripts/qa.py — QA orchestrator internals."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from scripts.qa import _find_project_root, _has_build_system, _print_summary, _short_name


class TestFindProjectRoot:
    """Tests for the pyproject.toml walk-up logic."""

    def test_finds_root_from_scripts_dir(self) -> None:
        """Walk-up works from the actual repo scripts/ directory."""
        root = _find_project_root()
        assert (root / "pyproject.toml").exists()

    def test_finds_root_one_level_up(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        scripts = tmp_path / "scripts"
        scripts.mkdir()

        root = _find_project_root(scripts)
        assert root == tmp_path

    def test_finds_root_two_levels_up(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        deep = tmp_path / ".github" / "scripts"
        deep.mkdir(parents=True)

        root = _find_project_root(deep)
        assert root == tmp_path

    def test_finds_root_many_levels_up(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        deep = tmp_path / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)

        root = _find_project_root(deep)
        assert root == tmp_path

    def test_exits_when_not_found(self, tmp_path: Path) -> None:
        import pytest

        no_pyproject = tmp_path / "empty" / "dir"
        no_pyproject.mkdir(parents=True)

        with pytest.raises(SystemExit):
            _find_project_root(no_pyproject)


class TestShortName:
    """Tests for check script name derivation."""

    def test_strips_check_prefix(self) -> None:
        assert _short_name(Path("check_lint.py")) == "lint"

    def test_strips_check_prefix_multiword(self) -> None:
        assert _short_name(Path("check_some_thing.py")) == "some_thing"

    def test_no_prefix(self) -> None:
        assert _short_name(Path("qa.py")) == "qa"

    def test_full_path(self) -> None:
        assert _short_name(Path("/foo/bar/check_types.py")) == "types"


class TestHasBuildSystem:
    """Tests for pyproject.toml [build-system] detection."""

    def test_returns_true_when_present(self, tmp_path: Path, monkeypatch: object) -> None:
        import scripts.qa as qa_mod

        (tmp_path / "pyproject.toml").write_text("[build-system]\nrequires = []\n")
        monkeypatch.setattr(qa_mod, "PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]

        assert _has_build_system() is True

    def test_returns_false_when_absent(self, tmp_path: Path, monkeypatch: object) -> None:
        import scripts.qa as qa_mod

        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'foo'\n")
        monkeypatch.setattr(qa_mod, "PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]

        assert _has_build_system() is False

    def test_returns_false_when_no_file(self, tmp_path: Path, monkeypatch: object) -> None:
        import scripts.qa as qa_mod

        monkeypatch.setattr(qa_mod, "PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]

        assert _has_build_system() is False


class TestPrintSummary:
    """Tests for the summary table formatter."""

    def test_all_pass(self) -> None:
        results = [
            ("lint", "PASS", "0.5s"),
            ("types", "PASS", "1.2s"),
        ]
        failures = _print_summary(results, "Test")

        assert failures == 0

    def test_counts_failures(self) -> None:
        results = [
            ("lint", "PASS", "0.5s"),
            ("types", "FAIL", "1.2s"),
            ("tests", "FAIL", "3.0s"),
        ]
        failures = _print_summary(results, "Test")

        assert failures == 2

    def test_skips_not_counted_as_failures(self) -> None:
        results = [
            ("lint", "PASS", "0.5s"),
            ("types", "SKIP", "-"),
        ]
        failures = _print_summary(results, "Test")

        assert failures == 0

    def test_empty_results(self) -> None:
        failures = _print_summary([], "Test")
        assert failures == 0


class TestQaMain:
    """Tests for qa.py main() with mocked subprocess calls."""

    def test_all_checks_skipped(self, monkeypatch: object, tmp_path: Path) -> None:
        import scripts.qa as qa_mod

        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        monkeypatch.setattr(qa_mod, "PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]

        # Create fake check scripts so SCRIPT_DIR.glob finds them
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "check_lint.py").write_text("")
        (scripts_dir / "check_types.py").write_text("")
        monkeypatch.setattr(qa_mod, "SCRIPT_DIR", scripts_dir)  # type: ignore[attr-defined]

        monkeypatch.setattr(  # type: ignore[attr-defined]
            "sys.argv", ["qa.py", "--skip", "lint", "--skip", "types"]
        )

        result = qa_mod.main()
        assert result == 0

    def test_auto_skips_package_without_build_system(self, monkeypatch: object, tmp_path: Path) -> None:
        import scripts.qa as qa_mod

        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        monkeypatch.setattr(qa_mod, "PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "check_package.py").write_text("")
        monkeypatch.setattr(qa_mod, "SCRIPT_DIR", scripts_dir)  # type: ignore[attr-defined]

        monkeypatch.setattr("sys.argv", ["qa.py"])  # type: ignore[attr-defined]

        # Mock _run_check so we don't actually run scripts
        monkeypatch.setattr(qa_mod, "_run_check", lambda script, extra_args=None: (0, 0.1))  # type: ignore[attr-defined]

        result = qa_mod.main()
        # package should be auto-skipped since no [build-system]
        assert result == 0

    def test_fix_flag_passed_to_lint_and_spelling(self, monkeypatch: object, tmp_path: Path) -> None:
        import scripts.qa as qa_mod

        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        monkeypatch.setattr(qa_mod, "PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "check_lint.py").write_text("")
        (scripts_dir / "check_spelling.py").write_text("")
        monkeypatch.setattr(qa_mod, "SCRIPT_DIR", scripts_dir)  # type: ignore[attr-defined]

        monkeypatch.setattr("sys.argv", ["qa.py", "--fix"])  # type: ignore[attr-defined]

        captured_extras: list[tuple[str, list[str] | None]] = []

        def mock_run_check(script: Path, extra_args: list[str] | None = None) -> tuple[int, float]:
            captured_extras.append((_short_name(script), extra_args))
            return (0, 0.1)

        monkeypatch.setattr(qa_mod, "_run_check", mock_run_check)  # type: ignore[attr-defined]
        qa_mod.main()

        lint_extras = next(e for name, e in captured_extras if name == "lint")
        spelling_extras = next(e for name, e in captured_extras if name == "spelling")
        assert lint_extras == ["--fix"]
        assert spelling_extras == ["--fix"]

    def test_returns_failure_when_check_fails(self, monkeypatch: object, tmp_path: Path) -> None:
        import scripts.qa as qa_mod

        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        monkeypatch.setattr(qa_mod, "PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "check_lint.py").write_text("")
        monkeypatch.setattr(qa_mod, "SCRIPT_DIR", scripts_dir)  # type: ignore[attr-defined]

        monkeypatch.setattr("sys.argv", ["qa.py"])  # type: ignore[attr-defined]
        monkeypatch.setattr(qa_mod, "_run_check", lambda script, extra_args=None: (1, 0.5))  # type: ignore[attr-defined]

        result = qa_mod.main()
        assert result == 1


class TestRunCheck:
    """Tests for _run_check subprocess wrapper."""

    def test_returns_exit_code_and_duration(self, monkeypatch: object) -> None:
        import scripts.qa as qa_mod

        mock_result = MagicMock(returncode=0)
        with patch("scripts.qa.subprocess.run", return_value=mock_result):
            code, duration = qa_mod._run_check(Path("check_lint.py"))

        assert code == 0
        assert duration >= 0

    def test_passes_extra_args(self, monkeypatch: object) -> None:
        import scripts.qa as qa_mod

        captured: list[Any] = []

        def mock_run(*args: Any, **kwargs: Any) -> MagicMock:
            captured.append(args[0])
            return MagicMock(returncode=0)

        with patch("scripts.qa.subprocess.run", side_effect=mock_run):
            qa_mod._run_check(Path("check_lint.py"), ["--fix"])

        assert "--fix" in captured[0]


class TestRunExternalTool:
    """Tests for _run_external_tool subprocess wrapper."""

    def test_returns_exit_code_and_duration(self) -> None:
        import scripts.qa as qa_mod

        mock_result = MagicMock(returncode=0)
        with patch("scripts.qa.subprocess.run", return_value=mock_result):
            code, duration = qa_mod._run_external_tool("shellcheck", ["shellcheck", "test.sh"])

        assert code == 0
        assert duration >= 0


class TestFindFiles:
    """Tests for _find_files glob helper."""

    def test_finds_matching_files(self, tmp_path: Path, monkeypatch: object) -> None:
        import scripts.qa as qa_mod

        monkeypatch.setattr(qa_mod, "PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]
        (tmp_path / "test.sh").write_text("")
        (tmp_path / "test.py").write_text("")

        result = qa_mod._find_files("*.sh")
        assert "test.sh" in result
        assert "test.py" not in result
