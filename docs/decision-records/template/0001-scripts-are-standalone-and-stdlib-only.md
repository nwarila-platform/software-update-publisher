# ADR-0001: QA Scripts Are Standalone and Stdlib-Only

| Field            | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| ID               | ADR-0001                                                                     |
| Scope            | Template                                                                     |
| Status           | Accepted                                                                     |
| Decision-subject | QA scripts are standalone, stdlib-only, and independently syncable.          |
| Date accepted    | 2026-04-08                                                                   |
| Date             | 2026-06-03                                                                   |
| Last reviewed    | 2026-06-03                                                                   |
| Authors          | Nick Warila (@NWarila)                                                       |
| Decision-makers  | Nick Warila (sole portfolio maintainer)                                      |
| Consulted        | Python packaging and tooling docs.                                           |
| Informed         | Downstream Python repositories.                                              |
| Reversibility    | Medium                                                                       |
| Review-by        | 2026-11-30                                                                   |

## TL;DR

Each QA script (`check_*.py`, `qa.py`) is a fully self-contained Python file with no shared helper module and no imports beyond the standard library. Cross-script logic duplication is acceptable.

## Context and Problem Statement

The template ships QA scripts that downstream repositories sync into `.github/scripts/`. Those scripts must be runnable on any OS (Linux, macOS, Windows) from a plain activated venv, regardless of whether the repo uses `pip`+`venv` or `uv`. They must also be readable and debuggable in isolation without needing to understand the whole template.

Two design paths were considered:

1. A shared helper module (`_common.py`) imported by each script, reducing duplication.
2. Each script as a self-contained file, duplicating small helpers (config reading, path resolution) independently.

## Decision Drivers

1. Downstream repos sync only the files they need, not the whole template. A shared module would require every consumer to also sync `_common.py` and keep it aligned.
2. Scripts must run from two different depths (`scripts/` and `.github/scripts/`) without path assumptions breaking.
3. Each script should be independently readable without tracing imports.
4. No third-party install overhead from template infrastructure should land in downstream dev dependencies.

## Considered Options

1. Standalone, stdlib-only scripts - no shared module, no third-party deps.
2. Shared helper module (`_common.py`) imported by each check script.
3. Template Python package installed as a dev dependency.

## Decision Outcome

Chosen option: **Option 1, standalone stdlib-only scripts.**

Each `check_*.py` file reads `pyproject.toml` via `tomllib` (stdlib since 3.11), resolves paths, invokes the tool via `subprocess`, and reports results - all inline. The `~10-line` config-reading pattern is duplicated across scripts rather than shared.

Scripts shell out to the actual tools (`ruff`, `mypy`, `pytest`, `pip-audit`, `codespell`, `build`, `twine`) and do not import them. This means the scripts carry zero non-stdlib import dependencies of their own.

## Pros and Cons of the Options

### Option 1: Standalone stdlib-only scripts

- Good, because each file can be read, copied, and debugged in isolation.
- Good, because downstream repos need no extra sync target beyond the scripts themselves.
- Good, because no third-party imports pollute downstream dev-dependency graphs.
- Bad, because `~10-line` patterns (config reading, path resolution) are duplicated.

### Option 2: Shared helper module

- Good, because it reduces duplication.
- Bad, because downstream sync must include `_common.py` and version it carefully.
- Bad, because a change to `_common.py` affects every script simultaneously, widening the blast radius.

### Option 3: Template as installable package

- Good, because version management is explicit via `pip install`.
- Bad, because it adds a template-infrastructure install step to every downstream developer setup.
- Bad, because it conflates template tooling with project dependencies.

## Confirmation

1. No `check_*.py` or `qa.py` file contains a cross-script import.
2. The only stdlib module used for config reading is `tomllib` (Python 3.11+), consistent with this template's minimum supported Python version ([ADR-0003](0003-python-minimum-version-floor.md)).
3. `mypy` and `ruff` pass on all scripts in CI (`template-ci.yml`).

## Consequences

### Positive

- Any script can be extracted, read, or replaced independently.
- Downstream repos remain decoupled from template internals.

### Negative

- Config-reading code is duplicated across scripts; a structural change to how `pyproject.toml` sections are read must be made in each file.

### Neutral

- The duplication is bounded: the pattern is ~10 lines and changes rarely.

## Assumptions

1. Python 3.11 remains the minimum version for this template (see PLAN.md Resolved Decision 15).
2. The set of check scripts stays small enough that per-file duplication is manageable.

## Supersedes

None.

## Superseded by

None (current).

## Implementing PRs

- Initial implementation: standalone `check_*.py` scripts in `scripts/`.
- Confirmed in Phase 1 cleanup: every `PROJECT_ROOT` resolution was migrated to walk-up-to-`pyproject.toml` (PR #5) after the `SCRIPT_DIR.parent` assumption broke at `.github/scripts/` depth.

## Related ADRs

- [ADR-0002](0002-pull-based-manifest-driven-template-sync.md): Pull-based manifest-driven template sync.
- [ADR-0003](0003-python-minimum-version-floor.md): Python minimum version floor.

## Compliance Notes

None.

## Changelog

| Date       | Change                                  | Reason                                             | Author/Role                         | Body-diff? |
| ---------- | --------------------------------------- | -------------------------------------------------- | ----------------------------------- | ---------- |
| 2026-06-03 | Reformatted to the living ADR schema.   | Satisfy the template ADR conformance gate.         | Portfolio maintainer / template ADR | Yes        |
