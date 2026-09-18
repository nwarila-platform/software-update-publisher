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
    parser = argparse.ArgumentParser(description="Run mypy type checking.")
    parser.add_argument("--paths", nargs="+", help="Override source paths to check")
    args = parser.parse_args()

    pyproject = _load_pyproject()
    paths = args.paths or pyproject.get("tool", {}).get("ruff", {}).get("src", ["src"])

    return _run([_tool("mypy"), *paths], "Mypy")


if __name__ == "__main__":
    sys.exit(main())
