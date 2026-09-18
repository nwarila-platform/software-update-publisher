#!/usr/bin/env python3
# Managed by NWarila/python-template — do not edit manually.
# Source: https://github.com/NWarila/python-template

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any


def _load_pyproject() -> dict[str, Any]:
    path = Path("pyproject.toml")
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _tool(name: str) -> str:
    exe_dir = Path(sys.executable).resolve().parent
    candidates = [exe_dir / name, exe_dir / f"{name}.exe"]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return name


def _run(cmd: list[str], label: str) -> int:
    print(f"\n--- {label} ---")
    result = subprocess.run(cmd)
    if result.returncode != 0 and os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::error::{label} failed with exit code {result.returncode}")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ruff lint and format checks.")
    parser.add_argument("--fix", action="store_true", help="Auto-fix lint issues and reformat")
    parser.add_argument("--paths", nargs="+", help="Override source paths to check")
    args = parser.parse_args()

    pyproject = _load_pyproject()
    paths = args.paths or pyproject.get("tool", {}).get("ruff", {}).get("src", ["src"])

    if args.fix:
        rc1 = _run([_tool("ruff"), "check", "--fix", *paths], "Ruff Fix")
        rc2 = _run([_tool("ruff"), "format", *paths], "Ruff Format")
    else:
        rc1 = _run([_tool("ruff"), "check", *paths], "Ruff Check")
        rc2 = _run([_tool("ruff"), "format", "--check", *paths], "Ruff Format Check")

    return 1 if (rc1 or rc2) else 0


if __name__ == "__main__":
    sys.exit(main())
