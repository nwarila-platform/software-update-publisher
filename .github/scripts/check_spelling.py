#!/usr/bin/env python3
# Managed by NWarila/python-template — do not edit manually.
# Source: https://github.com/NWarila/python-template

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


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
    parser = argparse.ArgumentParser(description="Run codespell for typo detection.")
    parser.add_argument("--fix", action="store_true", help="Auto-fix spelling mistakes")
    args = parser.parse_args()

    cmd = [_tool("codespell")]
    if args.fix:
        cmd.append("--write-changes")

    return _run(cmd, "Codespell")


if __name__ == "__main__":
    sys.exit(main())
