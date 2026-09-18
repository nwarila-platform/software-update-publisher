#!/usr/bin/env python3
"""Validate reference pre-commit hook revs against reference pyproject pins."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "reference" / "pyproject.toml"
PRE_COMMIT = ROOT / "reference" / "pre-commit-config.yaml"

HOOK_PACKAGE_BY_REPO = {
    "https://github.com/astral-sh/ruff-pre-commit": "ruff",
    "https://github.com/pre-commit/mirrors-mypy": "mypy",
    "https://github.com/codespell-project/codespell": "codespell",
    "https://github.com/abravalheri/validate-pyproject": "validate-pyproject",
}

DEPENDENCY_PIN_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)")
REPO_RE = re.compile(r"^\s*-\s+repo:\s+(.+?)\s*$")
REV_RE = re.compile(r"^\s+rev:\s+(.+?)\s*$")


def normalize_name(name: str) -> str:
    return name.replace("_", "-").lower()


def normalize_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.strip()


def normalize_rev(rev: str) -> str:
    value = normalize_value(rev)
    if value.startswith("v"):
        return value[1:]
    return value


def load_pyproject_pins() -> dict[str, str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = cast(dict[str, Any], data.get("project", {}))
    optional_dependencies = cast(dict[str, Any], project.get("optional-dependencies", {}))
    dev_dependencies = cast(list[str], optional_dependencies.get("dev", []))

    pins: dict[str, str] = {}
    for dependency in dev_dependencies:
        match = DEPENDENCY_PIN_RE.match(dependency)
        if match is None:
            continue
        pins[normalize_name(match.group(1))] = match.group(2)
    return pins


def load_pre_commit_revs() -> dict[str, str]:
    revs: dict[str, str] = {}
    current_repo = ""

    for line in PRE_COMMIT.read_text(encoding="utf-8").splitlines():
        repo_match = REPO_RE.match(line)
        if repo_match is not None:
            current_repo = normalize_value(repo_match.group(1))
            continue

        rev_match = REV_RE.match(line)
        if rev_match is None or current_repo not in HOOK_PACKAGE_BY_REPO:
            continue

        package = HOOK_PACKAGE_BY_REPO[current_repo]
        revs[package] = normalize_rev(rev_match.group(1))
        current_repo = ""

    return revs


def parity_errors(pyproject_pins: dict[str, str], pre_commit_revs: dict[str, str]) -> list[str]:
    errors: list[str] = []

    for package in sorted(HOOK_PACKAGE_BY_REPO.values()):
        pyproject_pin = pyproject_pins.get(package)
        pre_commit_rev = pre_commit_revs.get(package)

        if pyproject_pin is None:
            errors.append(f"reference/pyproject.toml dev dependency is missing an exact {package!r} pin")
            continue

        if pre_commit_rev is None:
            errors.append(f"reference/pre-commit-config.yaml is missing a tracked {package!r} hook rev")
            continue

        if pyproject_pin != pre_commit_rev:
            errors.append(
                f"{package}: reference/pyproject.toml pins {pyproject_pin}, "
                f"but reference/pre-commit-config.yaml uses {pre_commit_rev}"
            )

    return errors


def main() -> int:
    errors = parity_errors(load_pyproject_pins(), load_pre_commit_revs())
    if errors:
        sys.stderr.write("pin-parity check failed:\n")
        for error in errors:
            sys.stderr.write(f"  - {error}\n")
        return 1

    sys.stdout.write("pin-parity check passed\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
