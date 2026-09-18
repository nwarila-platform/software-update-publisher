"""Shared fixtures for script smoke tests."""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal Python project with passing quality gates."""
    # pyproject.toml — minimal, all checks enabled
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [build-system]
            requires = ["setuptools>=75.0"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "smoke-project"
            version = "0.1.0"
            description = "Minimal smoke-test project."
            readme = "README.md"
            requires-python = ">=3.11"
            license = "MIT"

            [project.optional-dependencies]
            dev = [
                "build",
                "codespell",
                "mypy>=1.16",
                "pip-audit",
                "pytest",
                "pytest-cov",
                "ruff>=0.11",
                "twine",
                "validate-pyproject",
            ]

            [project.scripts]
            smoke-cli = "smoke_project.cli:main"

            [tool.ruff]
            target-version = "py311"
            line-length = 120
            src = ["src"]

            [tool.ruff.lint]
            select = ["E", "F", "W", "I", "UP", "B", "S", "SIM", "C4", "PT", "T20", "RUF"]

            [tool.ruff.lint.per-file-ignores]
            "tests/**" = ["S101"]

            [tool.mypy]
            python_version = "3.11"
            strict = true

            [tool.pytest.ini_options]
            addopts = "-ra --import-mode=importlib --cov=src --cov-report=term-missing --cov-fail-under=90"
            testpaths = ["tests"]
            pythonpath = ["src"]

            [tool.codespell]
            skip = ".venv,dist,*.egg-info,.git"
        """)
    )

    # README (required for twine --strict)
    (tmp_path / "README.md").write_text("# Smoke Project\n\nMinimal test project.\n")

    # Source code
    src_dir = tmp_path / "src" / "smoke_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Smoke project."""\n')
    (src_dir / "cli.py").write_text(
        textwrap.dedent("""\
            \"\"\"CLI entry point.\"\"\"

            from __future__ import annotations

            import argparse


            def main(argv: list[str] | None = None) -> None:
                \"\"\"Run the CLI.\"\"\"
                parser = argparse.ArgumentParser(description="Smoke CLI")
                parser.parse_args(argv)
        """)
    )

    # Tests
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "__init__.py").write_text("")
    (test_dir / "test_cli.py").write_text(
        textwrap.dedent("""\
            \"\"\"Tests for the CLI module.\"\"\"

            from smoke_project.cli import main


            def test_main_runs() -> None:
                \"\"\"Verify main() runs without error.\"\"\"
                main([])
        """)
    )

    # Copy scripts into the temp project (simulating a synced downstream repo)
    scripts_src = Path(__file__).resolve().parent.parent / "scripts"
    scripts_dst = tmp_path / "scripts"
    shutil.copytree(scripts_src, scripts_dst)

    # Also copy to .github/scripts/ (simulating the synced path in downstream repos)
    gh_scripts_dst = tmp_path / ".github" / "scripts"
    shutil.copytree(scripts_src, gh_scripts_dst)

    return tmp_path
