#!/usr/bin/env bash
# Managed by NWarila/python-template — do not edit manually.
# Source: https://github.com/NWarila/python-template
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Walk up from SCRIPT_DIR to find the repo root (where pyproject.toml lives).
# This works whether the script is at scripts/ or .github/scripts/.
if [ -n "${PROJECT_ROOT:-}" ]; then
    : # Already set via env var
else
    _dir="$SCRIPT_DIR"
    while [ "$_dir" != "/" ]; do
        if [ -f "$_dir/pyproject.toml" ]; then
            PROJECT_ROOT="$_dir"
            break
        fi
        _dir="$(dirname "$_dir")"
    done
    if [ -z "${PROJECT_ROOT:-}" ]; then
        echo "Error: could not find pyproject.toml above $SCRIPT_DIR" >&2
        exit 1
    fi
fi

echo "Project root: ${PROJECT_ROOT}"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Detect toolchain
# ---------------------------------------------------------------------------
if [ -f "uv.lock" ]; then
    echo ""
    echo "Detected uv.lock — using uv toolchain."
    echo ""

    uv venv .venv
    uv sync

    echo ""
    echo "Setup complete (uv)."
    echo "  Activate: source .venv/bin/activate"
else
    echo ""
    echo "No uv.lock found — using pip + venv toolchain."
    echo ""

    python3 -m venv .venv

    .venv/bin/python -m pip install --upgrade pip

    # Check for [project.optional-dependencies] dev in pyproject.toml
    HAS_DEV_EXTRAS=false
    if [ -f "pyproject.toml" ]; then
        if grep -qE '^\[project\.optional-dependencies\]' pyproject.toml; then
            # Look for a "dev" key after the section header
            if awk '
                /^\[project\.optional-dependencies\]/ { in_section=1; next }
                /^\[/                                  { in_section=0 }
                in_section && /^[[:space:]]*dev[[:space:]]*=/ { found=1; exit }
                END { exit !found }
            ' pyproject.toml 2>/dev/null; then
                HAS_DEV_EXTRAS=true
            fi
        fi
    fi

    if [ "$HAS_DEV_EXTRAS" = true ]; then
        echo "Installing package with dev extras..."
        .venv/bin/python -m pip install -e ".[dev]"
    else
        echo "Installing package (no dev extras detected)..."
        .venv/bin/python -m pip install -e .
    fi

    echo ""
    echo "Setup complete (pip + venv)."
    echo "  Activate: source .venv/bin/activate"
fi
