#!/usr/bin/env python3
# Managed by NWarila/python-template — do not edit manually.
# Source: https://github.com/NWarila/python-template

from __future__ import annotations

import argparse
import glob
import os
import shutil
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


def _cleanup() -> None:
    shutil.rmtree("dist", ignore_errors=True)
    for egg_dir in glob.glob("*.egg-info"):
        shutil.rmtree(egg_dir, ignore_errors=True)
    for egg_dir in glob.glob("src/*.egg-info"):
        shutil.rmtree(egg_dir, ignore_errors=True)


def main() -> int:
    argparse.ArgumentParser(description="Validate package build, metadata, and entry points.").parse_args()

    pyproject = _load_pyproject()

    if "build-system" not in pyproject:
        print("No [build-system] found, skipping package check")
        return 0

    entry_points = pyproject.get("project", {}).get("scripts", {})

    try:
        rc = _run([_tool("validate-pyproject"), "pyproject.toml"], "Validate pyproject.toml")
        if rc != 0:
            return rc

        rc = _run([sys.executable, "-m", "build"], "Build sdist+wheel")
        if rc != 0:
            return rc

        dist_files = glob.glob("dist/*")
        if not dist_files:
            is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
            print("::error::No dist files produced" if is_ci else "ERROR: No dist files produced")
            return 1

        rc = _run([_tool("twine"), "check", "--strict", *dist_files], "Twine Check")
        if rc != 0:
            return rc

        for name in entry_points:
            tool_path = shutil.which(name) or _tool(name)
            if shutil.which(name) is None and tool_path == name:
                print(f"  Entry point '{name}' not found on PATH, skipping smoke test")
                continue
            rc = _run([tool_path, "--help"], f"Entry point: {name} --help")
            if rc != 0:
                return rc

    finally:
        _cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
