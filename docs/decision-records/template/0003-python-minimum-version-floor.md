# ADR-0003: Python Minimum Version Floor

| Field            | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| ID               | ADR-0003                                                                     |
| Scope            | Template                                                                     |
| Status           | Accepted                                                                     |
| Decision-subject | The template requires Python 3.11 or newer.                                 |
| Date accepted    | 2026-06-03                                                                   |
| Date             | 2026-06-03                                                                   |
| Last reviewed    | 2026-06-03                                                                   |
| Authors          | Nick Warila (@NWarila)                                                       |
| Decision-makers  | Nick Warila (sole portfolio maintainer)                                      |
| Consulted        | Python packaging docs, CPython `tomllib` docs, Ruff configuration docs.      |
| Informed         | Downstream Python repositories.                                              |
| Reversibility    | Medium                                                                       |
| Review-by        | 2026-11-30                                                                   |

## TL;DR

This template requires Python 3.11 or newer. The floor is already encoded in `pyproject.toml` as `requires-python = ">=3.11"` and in Ruff as `target-version = "py311"`. It also makes the stdlib-only QA scripts in [ADR-0001](0001-scripts-are-standalone-and-stdlib-only.md) possible because they can use `tomllib` without a backport dependency.

## Context and Problem Statement

The template provides reusable quality-gate scripts, workflow files, and reference configuration for downstream Python repositories. Those scripts are intentionally standalone and stdlib-only per [ADR-0001](0001-scripts-are-standalone-and-stdlib-only.md), so they need a Python runtime whose standard library contains the parsing functionality they depend on.

`tomllib` entered the Python standard library in Python 3.11. The QA scripts read `pyproject.toml`, so supporting Python versions earlier than 3.11 would either require a non-stdlib TOML dependency, duplicate parser logic, or conditional compatibility code. Each option conflicts with the standalone script decision.

The repository already declares the same floor in `pyproject.toml`: `[project] requires-python = ">=3.11"`, `[tool.ruff] target-version = "py311"`, and `[tool.mypy] python_version = "3.11"`. The ADR records that those settings are intentional template policy, not accidental tool defaults.

## Decision Drivers

1. Keep the QA scripts stdlib-only and individually copyable.
2. Avoid compatibility shims or backport dependencies in template infrastructure.
3. Align package metadata, lint configuration, and type-checking configuration around one Python baseline.
4. Permit modern typing and standard-library APIs in future template code.
5. Keep downstream expectations explicit before they adopt or sync the template.

## Considered Options

1. Support Python 3.10 and newer with a TOML backport or compatibility path.
2. Require Python 3.11 and newer.
3. Require only the newest actively developed Python minor version.

## Decision Outcome

Chosen option: **Option 2, require Python 3.11 and newer.**

The template's Python floor is 3.11. `pyproject.toml` remains the machine-readable source for packaging and tool configuration, while this ADR records the rationale. The QA scripts may use `tomllib` directly and do not need a backport dependency or runtime fallback for older Python versions.

Future changes to the Python floor must update this ADR, `pyproject.toml`, and any affected QA-script assumptions together.

## Pros and Cons of the Options

### Option 1: Support Python 3.10 and newer

- Good, because it would let older downstream environments adopt the template without upgrading Python first.
- Bad, because `tomllib` is not available in the Python 3.10 standard library.
- Bad, because adding a TOML backport would violate the stdlib-only QA-script decision.
- Bad, because conditional compatibility code would make each standalone script harder to read and maintain.

### Option 2: Require Python 3.11 and newer

- Good, because it matches the existing `pyproject.toml` package metadata and Ruff target version.
- Good, because it allows direct `tomllib` use with no helper package.
- Good, because it supports modern typing and standard-library features without compatibility shims.
- Neutral, because downstream repositories must provide Python 3.11 or newer before adopting the template.
- Bad, because repositories pinned to older Python runtimes must upgrade or defer adoption.

### Option 3: Require only the newest actively developed Python minor version

- Good, because it would maximize access to current language and tooling features.
- Bad, because it would create unnecessary churn for downstream repositories.
- Bad, because the template does not currently need features beyond Python 3.11 to meet its QA-script contract.

## Confirmation

1. `pyproject.toml` declares `[project] requires-python = ">=3.11"`.
2. `pyproject.toml` declares `[tool.ruff] target-version = "py311"`.
3. `pyproject.toml` declares `[tool.mypy] python_version = "3.11"`.
4. QA scripts may import `tomllib` directly and must not add a TOML backport dependency for template-owned config reading.

## Consequences

### Positive

- The template has one clear Python baseline across packaging, linting, typing, and scripts.
- The stdlib-only script policy stays simple because `tomllib` is available.
- Future template code can use Python 3.11 typing and standard-library behavior without compatibility layers.

### Negative

- Downstream repositories on Python 3.10 or older cannot adopt the template unchanged.
- Lowering the floor later would require revisiting script imports, tool targets, and type syntax.

### Neutral

- The Python floor is a template-tier decision. Individual downstream repositories may choose a stricter floor, but they should not claim compatibility below the template floor while syncing these scripts unchanged.

## Assumptions

1. Downstream repositories that adopt this template can run CI and local QA with Python 3.11 or newer.
2. The template continues to value stdlib-only QA scripts over older runtime compatibility.
3. The template does not need to support Python interpreters outside the CPython-compatible packaging and tooling ecosystem.

## Supersedes

None.

## Superseded by

None (current).

## Implementing PRs

None yet. The policy is already reflected in `pyproject.toml`; future PRs that change the floor should be listed here.

## Related ADRs

- [ADR-0001](0001-scripts-are-standalone-and-stdlib-only.md): QA scripts are standalone and stdlib-only.

## Compliance Notes

None.

## Changelog

| Date       | Change                                      | Reason                                                   | Author/Role                         | Body-diff? |
| ---------- | ------------------------------------------- | -------------------------------------------------------- | ----------------------------------- | ---------- |
| 2026-06-03 | Accepted the template Python version floor. | Document the Python 3.11 policy already encoded in tools. | Portfolio maintainer / template ADR | Yes        |
