#!/usr/bin/env python3
# Managed by NWarila/python-template — do not edit manually.
# Source: https://github.com/NWarila/python-template
"""Local QA orchestrator. Discovers and runs all check_*.py scripts.

Usage:
    python path/to/qa.py [--fix] [--skip name ...]
"""

from __future__ import annotations

import argparse
import glob
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _find_project_root(start: Path | None = None) -> Path:
    """Walk up from *start* (default SCRIPT_DIR) to find pyproject.toml."""
    d = start or SCRIPT_DIR
    while d != d.parent:
        if (d / "pyproject.toml").exists():
            return d
        d = d.parent
    print(f"Error: could not find pyproject.toml above {d}", file=sys.stderr)
    sys.exit(1)


PROJECT_ROOT = _find_project_root()


# ---------------------------------------------------------------------------
# pyproject.toml helpers (stdlib only)
# ---------------------------------------------------------------------------


def _has_build_system() -> bool:
    """Return True if pyproject.toml contains a [build-system] section."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return False
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[build-system]":
            return True
    return False


# ---------------------------------------------------------------------------
# Check execution
# ---------------------------------------------------------------------------


def _short_name(script_path: Path) -> str:
    """Derive the short check name from a script filename.

    check_lint.py  -> lint
    check_types.py -> types
    """
    stem = script_path.stem  # e.g. "check_lint"
    if stem.startswith("check_"):
        return stem[len("check_") :]
    return stem


def _run_check(
    script: Path,
    extra_args: list[str] | None = None,
) -> tuple[int, float]:
    """Run a single check script and return (exit_code, duration_seconds)."""
    name = _short_name(script)
    print(f"\n{'=' * 60}")
    print(f"  Running: {name}")
    print(f"{'=' * 60}\n")

    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(script), *(extra_args or [])],
        cwd=PROJECT_ROOT,
    )
    duration = time.monotonic() - start
    return result.returncode, duration


# ---------------------------------------------------------------------------
# External tool helpers
# ---------------------------------------------------------------------------


def _run_external_tool(
    name: str,
    cmd: list[str],
) -> tuple[int, float]:
    """Run an external tool and return (exit_code, duration_seconds)."""
    print(f"\n{'=' * 60}")
    print(f"  Running: {name}")
    print(f"{'=' * 60}\n")

    start = time.monotonic()
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    duration = time.monotonic() - start
    return result.returncode, duration


def _find_files(pattern: str) -> list[str]:
    """Glob for files relative to PROJECT_ROOT."""
    return sorted(glob.glob(pattern, root_dir=str(PROJECT_ROOT), recursive=True))


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _print_summary(
    results: list[tuple[str, str, str]],
    section_title: str = "QA Summary",
) -> int:
    """Print a formatted summary table.

    *results* is a list of (name, status, duration_str) tuples.
    Returns the number of FAILed checks.
    """
    col_name = max(len(r[0]) for r in results) if results else 5
    col_name = max(col_name, 5)  # minimum width
    col_status = 6  # "RESULT" / "PASS" / "FAIL" / "SKIP"
    col_dur = 8

    bar = "=" * 40
    print(f"\n{bar}")
    print(f"  {section_title}")
    print(bar)
    header = f"  {'Check':<{col_name}}  {'Result':<{col_status}}  {'Duration':<{col_dur}}"
    sep = f"  {'-' * col_name}  {'-' * col_status}  {'-' * col_dur}"
    print(header)
    print(sep)
    for name, status, dur in results:
        print(f"  {name:<{col_name}}  {status:<{col_status}}  {dur:<{col_dur}}")

    failures = [r for r in results if r[1] == "FAIL"]
    ran = [r for r in results if r[1] != "SKIP"]
    print(bar)
    if failures:
        print(f"  Result: FAIL ({len(failures)} of {len(ran)} checks failed)")
    else:
        print(f"  Result: PASS ({len(ran)} of {len(ran)} checks passed)")
    print(bar)
    return len(failures)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all local QA checks.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Pass --fix to check_lint.py and check_spelling.py",
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="NAME",
        help="Skip a check by short name (e.g. --skip package). Can be repeated.",
    )
    args = parser.parse_args()

    skips: set[str] = {s.lower() for s in args.skip}

    # Auto-skip check_package when there is no [build-system]
    if not _has_build_system():
        skips.add("package")

    # -----------------------------------------------------------------
    # Discover check scripts
    # -----------------------------------------------------------------
    check_scripts = sorted(SCRIPT_DIR.glob("check_*.py"))

    check_results: list[tuple[str, str, str]] = []
    for script in check_scripts:
        name = _short_name(script)
        if name in skips:
            check_results.append((name, "SKIP", "-"))
            continue

        # Determine extra args
        extra: list[str] = []
        if args.fix and name in ("lint", "spelling"):
            extra.append("--fix")

        exit_code, duration = _run_check(script, extra)
        status = "PASS" if exit_code == 0 else "FAIL"
        check_results.append((name, status, f"{duration:.1f}s"))

    # -----------------------------------------------------------------
    # External tools
    # -----------------------------------------------------------------
    external_results: list[tuple[str, str, str]] = []

    externals: list[tuple[str, str, list[str] | None]] = []

    # shellcheck
    sh_files = _find_files("**/*.sh")
    if sh_files:
        externals.append(
            (
                "shellcheck",
                "shellcheck",
                ["shellcheck", *sh_files],
            )
        )
    else:
        externals.append(("shellcheck", "shellcheck", None))

    # markdownlint-cli2
    md_files = _find_files("**/*.md")
    if md_files:
        externals.append(
            (
                "markdownlint",
                "markdownlint-cli2",
                ["markdownlint-cli2", *md_files],
            )
        )
    else:
        externals.append(("markdownlint", "markdownlint-cli2", None))

    # actionlint
    yml_files = _find_files(".github/workflows/*.yml")
    if yml_files:
        externals.append(("actionlint", "actionlint", ["actionlint"]))
    else:
        externals.append(("actionlint", "actionlint", None))

    for name, binary, cmd in externals:
        if shutil.which(binary) is None:
            external_results.append((name, "SKIP", "-"))
            continue
        if cmd is None:
            # Tool exists but no matching files
            external_results.append((name, "SKIP", "-"))
            continue
        exit_code, duration = _run_external_tool(name, cmd)
        status = "PASS" if exit_code == 0 else "FAIL"
        external_results.append((name, status, f"{duration:.1f}s"))

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------
    failures = _print_summary(check_results, "QA Summary")

    if external_results:
        ext_failures = _print_summary(external_results, "External Tools")
        failures += ext_failures

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
