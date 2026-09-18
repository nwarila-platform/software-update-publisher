"""Direct-import tests for check_*.py scripts.

Mocks subprocess.run so tests don't require external tools (ruff, mypy, etc.).
This gives real coverage of the script logic: argument parsing, pyproject.toml
reading, tool discovery, CI error annotation, and exit code propagation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import scripts.check_lint as check_lint_mod
import scripts.check_package as check_package_mod
import scripts.check_security as check_security_mod
import scripts.check_spelling as check_spelling_mod
import scripts.check_tests as check_tests_mod
import scripts.check_types as check_types_mod
from scripts.check_lint import _load_pyproject, _run, _tool


def _capture_run(calls: list[Any]) -> Any:
    """Return a fake _run that captures commands and returns 0."""

    def fake(cmd: list[str], label: str) -> int:
        calls.append(cmd)
        return 0

    return fake


class TestTool:
    """Tests for the _tool() helper that locates CLI executables.

    _tool() is duplicated in every check script. We test each copy to get coverage.
    """

    def test_returns_name_when_not_in_exe_dir(self) -> None:
        assert _tool("nonexistent_tool_xyz") == "nonexistent_tool_xyz"

    def test_finds_tool_in_exe_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_exe = tmp_path / "python.exe"
        fake_exe.write_text("")
        fake_tool = tmp_path / "ruff.exe"
        fake_tool.write_text("")

        monkeypatch.setattr("sys.executable", str(fake_exe))
        from scripts.check_lint import _tool as fresh_tool

        result = fresh_tool("ruff")
        assert result == str(fake_tool)

    def test_fallback_in_check_types(self) -> None:
        from scripts.check_types import _tool as types_tool

        assert types_tool("nonexistent_xyz") == "nonexistent_xyz"

    def test_fallback_in_check_security(self) -> None:
        from scripts.check_security import _tool as sec_tool

        assert sec_tool("nonexistent_xyz") == "nonexistent_xyz"

    def test_fallback_in_check_spelling(self) -> None:
        from scripts.check_spelling import _tool as spell_tool

        assert spell_tool("nonexistent_xyz") == "nonexistent_xyz"

    def test_fallback_in_check_package(self) -> None:
        from scripts.check_package import _tool as pkg_tool

        assert pkg_tool("nonexistent_xyz") == "nonexistent_xyz"

    def test_fallback_in_check_tests(self) -> None:
        from scripts.check_tests import _tool as test_tool

        assert test_tool("nonexistent_xyz") == "nonexistent_xyz"


# ---------------------------------------------------------------------------
# _load_pyproject() — shared by check_lint, check_types, check_package
# ---------------------------------------------------------------------------


class TestLoadPyproject:
    """Tests for pyproject.toml loading. Duplicated in check_lint, check_types, check_package."""

    def test_returns_empty_when_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert _load_pyproject() == {}

    def test_loads_valid_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / "pyproject.toml").write_text('[tool.ruff]\nsrc = ["lib"]\n')
        monkeypatch.chdir(tmp_path)
        result = _load_pyproject()
        assert result["tool"]["ruff"]["src"] == ["lib"]

    def test_check_types_copy(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts.check_types import _load_pyproject as types_load

        monkeypatch.chdir(tmp_path)
        assert types_load() == {}

    def test_check_package_copy(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts.check_package import _load_pyproject as pkg_load

        monkeypatch.chdir(tmp_path)
        assert pkg_load() == {}

    def test_check_types_loads_data(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts.check_types import _load_pyproject as types_load

        (tmp_path / "pyproject.toml").write_text("[tool.mypy]\nstrict = true\n")
        monkeypatch.chdir(tmp_path)
        result = types_load()
        assert result["tool"]["mypy"]["strict"] is True

    def test_check_package_loads_data(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts.check_package import _load_pyproject as pkg_load

        (tmp_path / "pyproject.toml").write_text("[build-system]\nrequires = []\n")
        monkeypatch.chdir(tmp_path)
        result = pkg_load()
        assert "build-system" in result


# ---------------------------------------------------------------------------
# _run() — shared by all check scripts
# ---------------------------------------------------------------------------


class TestRun:
    """Tests for the _run() subprocess wrapper."""

    def test_returns_exit_code(self) -> None:
        mock = MagicMock(returncode=0)
        with patch("scripts.check_lint.subprocess.run", return_value=mock):
            assert _run(["fake"], "Test") == 0

    def test_returns_nonzero_exit_code(self) -> None:
        mock = MagicMock(returncode=1)
        with patch("scripts.check_lint.subprocess.run", return_value=mock):
            assert _run(["fake"], "Test") == 1

    def test_prints_ci_error_on_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        mock = MagicMock(returncode=1)
        with patch("scripts.check_lint.subprocess.run", return_value=mock):
            _run(["fake"], "Lint")
        assert "::error::Lint failed" in capsys.readouterr().out

    def test_no_ci_error_outside_github(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        mock = MagicMock(returncode=1)
        with patch("scripts.check_lint.subprocess.run", return_value=mock):
            _run(["fake"], "Lint")
        assert "::error::" not in capsys.readouterr().out

    def test_check_types_run(self) -> None:
        from scripts.check_types import _run as types_run

        mock = MagicMock(returncode=0)
        with patch("scripts.check_types.subprocess.run", return_value=mock):
            assert types_run(["fake"], "Test") == 0

    def test_check_security_run(self) -> None:
        from scripts.check_security import _run as sec_run

        mock = MagicMock(returncode=0)
        with patch("scripts.check_security.subprocess.run", return_value=mock):
            assert sec_run(["fake"], "Test") == 0

    def test_check_spelling_run(self) -> None:
        from scripts.check_spelling import _run as spell_run

        mock = MagicMock(returncode=0)
        with patch("scripts.check_spelling.subprocess.run", return_value=mock):
            assert spell_run(["fake"], "Test") == 0

    def test_check_package_run(self) -> None:
        from scripts.check_package import _run as pkg_run

        mock = MagicMock(returncode=0)
        with patch("scripts.check_package.subprocess.run", return_value=mock):
            assert pkg_run(["fake"], "Test") == 0

    def test_check_tests_run(self) -> None:
        from scripts.check_tests import _run as test_run

        mock = MagicMock(returncode=0)
        with patch("scripts.check_tests.subprocess.run", return_value=mock):
            assert test_run(["fake"], "Test") == 0


# ---------------------------------------------------------------------------
# check_lint.py main()
# ---------------------------------------------------------------------------


class TestCheckLintMain:
    """Tests for check_lint.py main() logic."""

    def test_passes_src_paths_from_pyproject(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_lint.py"])
        monkeypatch.setattr(check_lint_mod, "_load_pyproject", lambda: {"tool": {"ruff": {"src": ["mylib"]}}})

        calls: list[Any] = []

        def fake_run(cmd: list[str], label: str) -> int:
            calls.append(cmd)
            return 0

        monkeypatch.setattr(check_lint_mod, "_run", fake_run)
        check_lint_mod.main()

        assert "mylib" in calls[0]

    def test_fix_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_lint.py", "--fix"])
        monkeypatch.setattr(check_lint_mod, "_load_pyproject", lambda: {})

        calls: list[Any] = []

        def fake_run(cmd: list[str], label: str) -> int:
            calls.append((cmd, label))
            return 0

        monkeypatch.setattr(check_lint_mod, "_run", fake_run)
        check_lint_mod.main()

        assert "--fix" in calls[0][0]
        assert "Fix" in calls[0][1]

    def test_returns_failure_on_any_nonzero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_lint.py"])
        monkeypatch.setattr(check_lint_mod, "_load_pyproject", lambda: {})

        call_count = 0

        def fake_run(cmd: list[str], label: str) -> int:
            nonlocal call_count
            call_count += 1
            return 1 if call_count == 1 else 0  # First call fails

        monkeypatch.setattr(check_lint_mod, "_run", fake_run)
        assert check_lint_mod.main() == 1


# ---------------------------------------------------------------------------
# check_types.py main()
# ---------------------------------------------------------------------------


class TestCheckTypesMain:
    def test_uses_pyproject_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_types.py"])
        monkeypatch.setattr(check_types_mod, "_load_pyproject", lambda: {"tool": {"ruff": {"src": ["src"]}}})

        calls: list[Any] = []
        monkeypatch.setattr(check_types_mod, "_run", _capture_run(calls))
        check_types_mod.main()

        assert "src" in calls[0]

    def test_override_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_types.py", "--paths", "custom/"])
        monkeypatch.setattr(check_types_mod, "_load_pyproject", lambda: {})

        calls: list[Any] = []
        monkeypatch.setattr(check_types_mod, "_run", _capture_run(calls))
        check_types_mod.main()

        assert "custom/" in calls[0]


# ---------------------------------------------------------------------------
# check_security.py main()
# ---------------------------------------------------------------------------


class TestCheckSecurityMain:
    def test_runs_pip_audit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_security.py"])

        calls: list[Any] = []
        monkeypatch.setattr(check_security_mod, "_run", _capture_run(calls))
        check_security_mod.main()

        assert "--skip-editable" in calls[0]


# ---------------------------------------------------------------------------
# check_spelling.py main()
# ---------------------------------------------------------------------------


class TestCheckSpellingMain:
    def test_runs_codespell(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_spelling.py"])

        calls: list[Any] = []
        monkeypatch.setattr(check_spelling_mod, "_run", _capture_run(calls))
        check_spelling_mod.main()

        assert len(calls) == 1

    def test_fix_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_spelling.py", "--fix"])

        calls: list[Any] = []
        monkeypatch.setattr(check_spelling_mod, "_run", _capture_run(calls))
        check_spelling_mod.main()

        assert "--write-changes" in calls[0]


# ---------------------------------------------------------------------------
# check_package.py main() and _cleanup()
# ---------------------------------------------------------------------------


class TestCheckPackageMain:
    def test_skips_when_no_build_system(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_package.py"])
        monkeypatch.setattr(check_package_mod, "_load_pyproject", lambda: {"project": {"name": "foo"}})

        assert check_package_mod.main() == 0

    def test_runs_validate_build_twine(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr("sys.argv", ["check_package.py"])
        monkeypatch.setattr(
            check_package_mod,
            "_load_pyproject",
            lambda: {"build-system": {"requires": []}, "project": {}},
        )
        monkeypatch.chdir(tmp_path)

        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "foo-1.0.tar.gz").write_text("")

        labels: list[str] = []

        def fake_run(cmd: list[str], label: str) -> int:
            labels.append(label)
            return 0

        monkeypatch.setattr(check_package_mod, "_run", fake_run)
        check_package_mod.main()

        assert "Validate pyproject.toml" in labels
        assert "Build sdist+wheel" in labels
        assert "Twine Check" in labels

    def test_validate_failure_stops_early(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr("sys.argv", ["check_package.py"])
        monkeypatch.setattr(
            check_package_mod,
            "_load_pyproject",
            lambda: {"build-system": {"requires": []}, "project": {}},
        )
        monkeypatch.chdir(tmp_path)

        monkeypatch.setattr(check_package_mod, "_run", lambda cmd, label: 1)
        assert check_package_mod.main() == 1

    def test_build_failure_stops_early(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr("sys.argv", ["check_package.py"])
        monkeypatch.setattr(
            check_package_mod,
            "_load_pyproject",
            lambda: {"build-system": {"requires": []}, "project": {}},
        )
        monkeypatch.chdir(tmp_path)

        call_count = 0

        def fake_run(cmd: list[str], label: str) -> int:
            nonlocal call_count
            call_count += 1
            return 0 if call_count == 1 else 1  # validate passes, build fails

        monkeypatch.setattr(check_package_mod, "_run", fake_run)
        assert check_package_mod.main() == 1

    def test_no_dist_files_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr("sys.argv", ["check_package.py"])
        monkeypatch.setattr(
            check_package_mod,
            "_load_pyproject",
            lambda: {"build-system": {"requires": []}, "project": {}},
        )
        monkeypatch.chdir(tmp_path)

        # Build "succeeds" but produces no dist files
        monkeypatch.setattr(check_package_mod, "_run", lambda cmd, label: 0)
        assert check_package_mod.main() == 1

    def test_twine_failure(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr("sys.argv", ["check_package.py"])
        monkeypatch.setattr(
            check_package_mod,
            "_load_pyproject",
            lambda: {"build-system": {"requires": []}, "project": {}},
        )
        monkeypatch.chdir(tmp_path)

        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "foo-1.0.tar.gz").write_text("")

        call_count = 0

        def fake_run(cmd: list[str], label: str) -> int:
            nonlocal call_count
            call_count += 1
            return 1 if call_count == 3 else 0  # validate ok, build ok, twine fails

        monkeypatch.setattr(check_package_mod, "_run", fake_run)
        assert check_package_mod.main() == 1

    def test_entry_point_smoke_test(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr("sys.argv", ["check_package.py"])
        monkeypatch.setattr(
            check_package_mod,
            "_load_pyproject",
            lambda: {
                "build-system": {"requires": []},
                "project": {"scripts": {"mycli": "pkg:main"}},
            },
        )
        monkeypatch.chdir(tmp_path)

        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "foo-1.0.tar.gz").write_text("")

        labels: list[str] = []

        def fake_run(cmd: list[str], label: str) -> int:
            labels.append(label)
            return 0

        monkeypatch.setattr(check_package_mod, "_run", fake_run)
        # Mock shutil.which to find the entry point
        monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
        check_package_mod.main()

        assert any("mycli" in label for label in labels)


class TestCleanup:
    def test_removes_dist_and_egg_info(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "file.tar.gz").write_text("")
        (tmp_path / "foo.egg-info").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "bar.egg-info").mkdir()

        check_package_mod._cleanup()

        assert not (tmp_path / "dist").exists()
        assert not (tmp_path / "foo.egg-info").exists()
        assert not (tmp_path / "src" / "bar.egg-info").exists()


# ---------------------------------------------------------------------------
# check_tests.py main() and _write_coverage_summary()
# ---------------------------------------------------------------------------


class TestCheckTestsMain:
    def test_runs_pytest(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_tests.py"])
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

        calls: list[Any] = []
        monkeypatch.setattr(check_tests_mod, "_run", _capture_run(calls))
        check_tests_mod.main()

        assert len(calls) == 1

    def test_adds_cov_report_in_ci(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_tests.py"])
        monkeypatch.setenv("GITHUB_ACTIONS", "true")

        calls: list[Any] = []
        monkeypatch.setattr(check_tests_mod, "_run", _capture_run(calls))
        monkeypatch.setattr(check_tests_mod, "_write_coverage_summary", lambda: None)
        check_tests_mod.main()

        assert "--cov-report=json:coverage.json" in calls[0]


class TestWriteCoverageSummary:
    def test_writes_markdown_table(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        summary_file = tmp_path / "summary.md"
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

        coverage_data = {
            "files": {
                "src/module.py": {"summary": {"num_statements": 100, "missing_lines": 10, "percent_covered": 90.0}}
            },
            "totals": {"num_statements": 100, "missing_lines": 10, "percent_covered": 90.0},
        }
        (tmp_path / "coverage.json").write_text(json.dumps(coverage_data))

        check_tests_mod._write_coverage_summary()

        content = summary_file.read_text()
        assert "## Coverage Summary" in content
        assert "src/module.py" in content
        assert "90.0%" in content
        assert not (tmp_path / "coverage.json").exists()  # Should be cleaned up

    def test_noop_when_no_coverage_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))

        # Should not raise
        check_tests_mod._write_coverage_summary()

    def test_noop_when_no_summary_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        (tmp_path / "coverage.json").write_text("{}")

        # Should not raise
        check_tests_mod._write_coverage_summary()
