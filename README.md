# python-template

[![CI](https://github.com/NWarila/python-template/actions/workflows/template-ci.yml/badge.svg)](https://github.com/NWarila/python-template/actions/workflows/template-ci.yml)
[![Coverage](https://codecov.io/gh/NWarila/python-template/graph/badge.svg)](https://codecov.io/gh/NWarila/python-template)
[![Python](https://img.shields.io/badge/python-%E2%89%A53.11-3776ab?logo=python&logoColor=white)](https://www.python.org)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)](https://github.com/NWarila/python-template)
[![Security Policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![License](https://img.shields.io/github/license/NWarila/python-template)](LICENSE)

Reusable Python quality-gate scripts, a reusable CI workflow, and reference configurations that define a consistent developer experience across all Python repositories in the **NWarila** GitHub account.

This repo is the Python-specific layer of a two-layer governance model. For org-wide community health files, issue templates, and baseline CI, see [NWarila/.github](https://github.com/NWarila/.github).

## Architecture

| Layer | Repo | Responsibility |
| --- | --- | --- |
| Org governance | `NWarila/.github` | Community health files, issue and PR templates, baseline CI, workflow templates |
| Python QA | `NWarila/python-template` | Check scripts, reusable workflow, setup action, sync manifest, reference configs |

Downstream Python repos consume both layers through different mechanisms. The `.github` repo provides defaults through GitHub's built-in inheritance; this repo ships Python-specific scripts and configs through tagged releases that downstream repos pull on their own schedule.

## What This Repo Provides

- **Canonical QA scripts** in `scripts/` — thin Python wrappers around standard tools (ruff, mypy, pytest, pip-audit, codespell, build/twine). Each script is the source implementation for its check.
- **Local orchestrator** (`qa.py`) — runs all checks in sequence with `--fix` and `--skip` flags, so developers get the same quality bar locally that CI enforces remotely.
- **Generic package skeleton** in `src/sample_app/` with typed contracts, settings, validation, exceptions, and a self-demo CLI.
- **Sync manifest** (`sync-manifest.json`) defining source-to-destination file mappings for downstream repos.
- **Reusable sync workflow** (`self-update.yml`) that downstream repos call via `uses:` to pull updates automatically.
- **Composite setup action** in `.github/actions/setup-python/` for Python plus dependency bootstrap.
- **Reusable CI workflow** in `.github/workflows/python-qa.yml` for downstream repositories.
- **Reference baselines** in `reference/`, including `pyproject.toml`, `.pre-commit-config.yaml`, VSCode settings, `gitignore`, `gitattributes`, and `repo-ci.yml`.
- **Release automation** through `auto-release.yml` (creates releases when `scripts/` changes) and `self-update.yml` (this repo's own pull from its releases for dogfooding).

## Quality Gates

| Check | Tool | Config Source |
| --- | --- | --- |
| Lint + Format | ruff | `[tool.ruff]` in `pyproject.toml` |
| Type Checking | mypy | `[tool.mypy]` in `pyproject.toml` |
| Tests + Coverage | pytest + pytest-cov | `[tool.pytest.ini_options]` in `pyproject.toml` |
| Security | pip-audit | Environment and dependency metadata |
| Spelling | codespell | `[tool.codespell]` in `pyproject.toml` |
| Packaging | build + twine | `[build-system]` in `pyproject.toml` |

## Use This Template

The starter package is intentionally generic. Rename `sample_app` before adding product-specific code:

```powershell
$env:NEW_PKG = "your_pkg"
git mv src/sample_app "src/$env:NEW_PKG"
git mv tests/test_sample_app.py "tests/test_$($env:NEW_PKG).py"
@'
import os
from pathlib import Path

old = "sample_app"
new = os.environ["NEW_PKG"]
dist = new.replace("_", "-")
paths = [
    Path("pyproject.toml"),
    Path("README.md"),
    Path(f"tests/test_{new}.py"),
    *sorted((Path("src") / new).rglob("*.py")),
]

for path in paths:
    text = path.read_text(encoding="utf-8")
    text = text.replace(old, new)
    text = text.replace('name = "python-template"', f'name = "{dist}"')
    path.write_text(text, encoding="utf-8")
'@ | Set-Content -Encoding UTF8 rename_template_package.py
python rename_template_package.py
Remove-Item rename_template_package.py
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python scripts/qa.py
```

That flow performs the required `git mv src/sample_app src/<your_pkg>` rename, updates imports and module strings, changes `[tool.setuptools.packages.find].include` to the new package name, changes `[project].name` to the hyphenated distribution name, refreshes the editable install, and runs the QA gates. If a consumer adds `[project.scripts]`, point each entry at `<your_pkg>.main:main` or another consumer-owned entry point.

The self-demo remains available after the rename:

```bash
python -m your_pkg
```

## Repository Structure

```text
python-template/
|-- .github/
|   |-- actions/
|   |   `-- setup-python/
|   |       `-- action.yml         # Composite action for Python + dependency setup
|   |-- scripts/
|   |   |-- .version               # Deliberate release-copy metadata
|   |   `-- ...                    # Released copies synced from scripts/
|   `-- workflows/
|       |-- auto-release.yml       # Creates a release when scripts/ changes land on main
|       |-- python-qa.yml          # Reusable CI workflow for downstream repos
|       |-- self-update.yml        # Pulls released files via manifest (dogfood)
|       `-- template-ci.yml        # CI for this repo, running released scripts
|-- reference/
|   |-- pyproject.toml             # Reference project config
|   |-- pre-commit-config.yaml     # Pre-commit hook definitions
|   |-- settings.json              # VSCode editor settings
|   |-- tasks.json                 # VSCode task definitions
|   |-- extensions.json            # VSCode recommended extensions
|   |-- gitignore                  # Reference .gitignore
|   |-- gitattributes              # Reference .gitattributes
|   |-- markdownlint-cli2.jsonc    # Markdown lint config
|   `-- repo-ci.yml                # Starter CI workflow for downstream repos
|-- scripts/
|   |-- check_lint.py              # ruff lint + format
|   |-- check_types.py             # mypy
|   |-- check_tests.py             # pytest + coverage
|   |-- check_security.py          # pip-audit
|   |-- check_spelling.py          # codespell
|   |-- check_package.py           # build + twine check
|   |-- qa.py                      # Local orchestrator
|   |-- sync.py                    # Manifest-driven file sync for template updates
|   |-- setup.sh                   # Unix venv bootstrap
|   `-- setup.ps1                  # Windows venv bootstrap
|-- src/
|   `-- sample_app/
|       |-- __init__.py            # Curated public API and __all__
|       |-- __main__.py            # python -m sample_app self-demo
|       |-- py.typed               # PEP 561 typing marker
|       |-- config.py              # Frozen pydantic-settings API
|       |-- exceptions.py          # Typed What/Why/Fix exceptions
|       |-- _contracts.py          # Frozen Pydantic contracts and Result shape
|       |-- validators.py          # Pure validation helpers
|       `-- main.py                # CLI entry point and worked sample function
|-- sync-manifest.json             # Source-to-dest file mappings for downstream sync
|-- pyproject.toml                 # Config for this repo
`-- README.md
```

## How Downstream Repos Use It

### Script Ownership

`scripts/` is the canonical source tree for QA scripts, setup scripts, and the sync helper. Edit scripts there first.
`.github/scripts/` is the released copy used by this template's self-dogfooding CI and by downstream repositories after sync.

The two trees should contain byte-identical copies of every script listed in `sync-manifest.json`. The only deliberate
extra file is `.github/scripts/.version`, which records the release tag currently pulled into the released-copy tree.
There is no `scripts/__init__.py`; scripts are standalone files, not an importable package.

### CI

Downstream repos copy `reference/repo-ci.yml` into `.github/workflows/ci.yml` and call the reusable workflow from a tagged release:

```yaml
jobs:
  python-qa:
    uses: NWarila/python-template/.github/workflows/python-qa.yml@v1
```

The reusable workflow runs each quality gate as a separate job and publishes a single stable `ci-passed` aggregator result.

### Local Development

Downstream repos run the synced `.github/scripts/` directly:

```bash
.venv/bin/python .github/scripts/qa.py
.venv/bin/python .github/scripts/qa.py --fix
.venv/bin/python .github/scripts/qa.py --skip tests security
```

VSCode tasks in `reference/tasks.json` expose the same checks in the editor.

### Pre-commit Hooks

The synced `.pre-commit-config.yaml` calls the same tools with the same `pyproject.toml` configuration so issues are caught before code leaves the developer's machine.

### Template Sync

Downstream repos call the reusable `self-update.yml` workflow from a thin wrapper:

```yaml
# .github/workflows/template-sync.yml
name: Template Sync
on:
  schedule:
    - cron: "0 6 * * 1" # Weekly Monday 06:00 UTC
  workflow_dispatch:
permissions:
  contents: write
  pull-requests: write
jobs:
  sync:
    uses: NWarila/python-template/.github/workflows/self-update.yml@v1
```

The workflow checks for new releases, reads `sync-manifest.json` to know which files to copy and where, and opens a PR using the repo's own `GITHUB_TOKEN`. No PAT required.

Supported sync modes:

- **`overwrite`** — full replacement (scripts, pre-commit config, VSCode settings)
- **`marker-preserve`** — replaces template-owned `// #region` sections while preserving repo-specific content (e.g. `tasks.json`)

## Update Flow

1. `scripts/` is the canonical source of truth for the QA scripts.
2. When `scripts/` changes merge to `main`, `auto-release.yml` creates the next patch release.
3. Downstream repos call `self-update.yml` as a reusable workflow — it checks for new releases, clones at the tag, reads `sync-manifest.json`, and opens a PR.
4. This repo dogfoods the same workflow directly (nightly schedule).
5. `template-ci.yml` runs the checks from `.github/scripts/`, validating the released artifacts.

Floating `vX` / `vX.Y` advancement and `.github/scripts/.version` stamping are manual maintainer tasks: an admin re-points the floating tag and bumps `.version` through a normal PR. The drift guard in `template-ci.yml` fails CI when the latest release, floating tag, or marker drifts, prompting that manual fix. Full automation is blocked until the shelved GitHub App path in [github-token-limitation.md](docs/reference/github-token-limitation.md) exists, because `GITHUB_TOKEN` cannot push to main or force-update protected tags.

Each repo controls its own update cadence — the template publishes releases, consumers pull when ready. No cross-repo credentials, no push permissions, no coupling.

## Git Hygiene Standard

The org-standard `.gitignore` uses an explicit allowlist model and starts with `**`, matching the control-plane style used in `NWarila/.github`. Repos intentionally allow tracked roots and keep generated artifacts ignored even inside allowed paths.

The org-standard `.gitattributes` is comment-rich and standardized, defining LF normalization and markdown diff behavior in a format aligned with `NWarila/.github`.

## Quick Start For A New Repo

1. Copy the reference configs from `reference/` into your repo, including `reference/repo-ci.yml` as the starting CI workflow.
2. Add a `template-sync.yml` wrapper workflow that calls `self-update.yml` via `uses:` (see Template Sync above).
3. Extend `.gitignore` by allowlisting any repo-specific tracked roots beyond the standard baseline.
4. Customize `pyproject.toml` for your project metadata, dependencies, and entry points.
5. Call the reusable workflow from your repo's CI and install the dev tooling locally.

## Design Principles

- **Local must match CI.** Every quality check is a Python script. CI workflows and VSCode tasks both call the same script with the same flags — there is no separate "CI version" of any check. This eliminates drift between what passes locally and what passes in CI.
- **Scripts are standalone and stdlib-only.** Each check script is self-contained with no shared helper modules and no dependencies beyond the standard library. This means any script can be copied, read, or debugged in isolation.
- **Wrappers exist for consistency, not complexity.** Some scripts are thin (e.g., `check_security.py` just runs `pip-audit`). The wrapper isn't about adding logic — it's about ensuring the invocation is identical everywhere. Without them, check logic would split between workflow YAML and VSCode task definitions and inevitably diverge.
- **`pyproject.toml` is the center of gravity.** Tool configuration stays centralized instead of spreading across dotfiles.
- **Cross-platform first.** Setup scripts and QA scripts are designed for Linux, macOS, and Windows.
- **Git hygiene is standardized.** `.gitignore` and `.gitattributes` align with the org baseline.
- **Each repo owns its own updates.** Sync is pull-based — no cross-repo credentials, no push permissions, no coupling.
- **Manifest-driven sync over submodules or packages.** Git submodules pin to a commit with no selective file mapping, no merge strategies, and no PR review of incoming changes. Package dependencies require a runtime install and don't handle config files. The manifest approach syncs both scripts and configs with per-file merge strategies (`overwrite` vs `marker-preserve`) and delivers changes as reviewable PRs.
- **Visible quality matters.** Separate jobs, clear logs, and consistent configs make the standard easy to review and trust.

## License

See [LICENSE](LICENSE).
