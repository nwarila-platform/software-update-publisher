#!/usr/bin/env python3
# Managed by NWarila/python-template — do not edit manually.
# Source: https://github.com/NWarila/python-template

from __future__ import annotations

import argparse
import json
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


def _write_coverage_summary() -> None:
    coverage_path = Path("coverage.json")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not coverage_path.exists() or not summary_path:
        return

    with open(coverage_path) as f:
        data = json.load(f)

    lines = [
        "## Coverage Summary",
        "",
        "| Module | Statements | Missed | Coverage |",
        "|--------|-----------|--------|----------|",
    ]

    files = data.get("files", {})
    for module, info in sorted(files.items()):
        summary = info.get("summary", {})
        stmts = summary.get("num_statements", 0)
        missed = summary.get("missing_lines", 0)
        covered = summary.get("percent_covered", 0.0)
        lines.append(f"| {module} | {stmts} | {missed} | {covered:.1f}% |")

    totals = data.get("totals", {})
    total_stmts = totals.get("num_statements", 0)
    total_missed = totals.get("missing_lines", 0)
    total_covered = totals.get("percent_covered", 0.0)
    lines.append(f"| **Total** | **{total_stmts}** | **{total_missed}** | **{total_covered:.1f}%** |")

    with open(summary_path, "a") as f:
        f.write("\n".join(lines) + "\n")

    coverage_path.unlink()


def main() -> int:
    argparse.ArgumentParser(description="Run pytest with coverage.").parse_args()

    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"

    cmd = [_tool("pytest")]
    if is_ci:
        cmd.append("--cov-report=json:coverage.json")

    rc = _run(cmd, "Pytest")

    if is_ci:
        _write_coverage_summary()

    return rc


if __name__ == "__main__":
    sys.exit(main())
