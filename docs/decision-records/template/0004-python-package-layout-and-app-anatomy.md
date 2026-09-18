# ADR-0004: Python Package Layout and App Anatomy

| Field            | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| ID               | ADR-0004                                                                     |
| Scope            | Template                                                                     |
| Status           | Accepted                                                                     |
| Decision-subject | The template ships a generic `src/<sample_pkg>` package anatomy.             |
| Date accepted    | 2026-06-03                                                                   |
| Date             | 2026-06-03                                                                   |
| Last reviewed    | 2026-06-03                                                                   |
| Authors          | Nick Warila (@NWarila)                                                       |
| Decision-makers  | Nick Warila (sole portfolio maintainer)                                      |
| Consulted        | Python packaging docs, PyPA typing marker docs, Pydantic docs.              |
| Informed         | Downstream Python repositories.                                              |
| Reversibility    | Medium                                                                       |
| Review-by        | 2026-11-30                                                                   |

## TL;DR

The template will ship a generic package skeleton under `src/<sample_pkg>` rather than only QA scripts. The package contains `__init__.py`, `__main__.py`, `py.typed`, `config.py`, `exceptions.py`, `_contracts.py`, `validators.py`, and `main.py`. This layout gives downstream repositories a typed, testable, app-shaped starting point without choosing a product domain or framework for them.

## Context and Problem Statement

The template already standardizes quality gates and sync behavior. Downstream Python repositories also benefit from a small, consistent package anatomy that demonstrates how application code should be organized once a project moves beyond scripts and configuration.

The skeleton needs to be useful as a starting point, but it must stay generic. Template-tier code should establish packaging, typing, validation, configuration, exception, contract, and CLI boundaries. It should not encode consumer-side product architecture, deployment assumptions, service frameworks, persistence models, or domain workflows.

The package should also be compatible with the template's Python 3.11 floor in [ADR-0003](0003-python-minimum-version-floor.md), so it can use modern standard-library and typing features while remaining approachable.

## Decision Drivers

1. Give new repositories a real package shape instead of leaving every consumer to invent its own first module layout.
2. Keep the skeleton generic enough for libraries, CLIs, and small applications.
3. Make the public API explicit and typed from the start.
4. Separate configuration, contracts, validation, exceptions, and CLI wiring into predictable files.
5. Keep domain-specific framework choices outside the template.
6. Align the skeleton with the Python 3.11 floor and modern typing expectations.

## Considered Options

1. Keep the template script-only and provide no package skeleton.
2. Ship a minimal generic `src/<sample_pkg>` package anatomy.
3. Ship a richer application framework skeleton with domain-specific layers.

## Decision Outcome

Chosen option: **Option 2, ship a minimal generic `src/<sample_pkg>` package anatomy.**

The template package anatomy is:

- `src/<sample_pkg>/__init__.py` defines the curated public API and `__all__`.
- `src/<sample_pkg>/__main__.py` provides a self-demo entry point for `python -m <sample_pkg>`.
- `src/<sample_pkg>/py.typed` marks the package as typed and is shipped as package data.
- `src/<sample_pkg>/config.py` owns the frozen `pydantic-settings` configuration API: `BaseSettings`, env-prefix handling, and `load()` / `save_defaults()`.
- `src/<sample_pkg>/exceptions.py` defines typed exceptions with What, Why, and Fix fields.
- `src/<sample_pkg>/_contracts.py` defines frozen Pydantic models, Result shapes, and `StrEnum`-based codes.
- `src/<sample_pkg>/validators.py` contains pure validation functions called from `model_validator` methods.
- `src/<sample_pkg>/main.py` owns the CLI entry point.

The package skeleton is intentionally small. Consumer repositories may add domain packages, integrations, persistence, orchestration, or service layers in their own ADRs, but those choices are not template-tier decisions.

## Pros and Cons of the Options

### Option 1: Keep the template script-only

- Good, because it avoids adding any application-code opinion to the template.
- Good, because downstream repositories have maximum freedom.
- Bad, because every new Python repository must invent its first package layout independently.
- Bad, because typing markers, public API boundaries, configuration, and validation patterns can drift immediately.

### Option 2: Ship a minimal generic package anatomy

- Good, because it gives consumers a concrete, typed starting point.
- Good, because the file boundaries are conventional and easy to replace.
- Good, because the skeleton demonstrates package data, CLI entry points, contracts, validation, and exceptions without choosing a domain.
- Good, because public API exports are curated from the beginning through `__init__.py` and `__all__`.
- Neutral, because consumers may delete or rename the sample package when they specialize the template.
- Bad, because the template now carries a small amount of application-code surface area to maintain.

### Option 3: Ship a richer application framework skeleton

- Good, because a specific framework skeleton could be immediately runnable for one style of application.
- Bad, because it would force consumer repositories toward a product architecture they may not need.
- Bad, because framework-specific choices belong in consumer repositories or more specialized templates, not in this generic Python template.
- Bad, because richer scaffolding would increase maintenance and sync churn.

## Confirmation

1. The package skeleton lives under `src/<sample_pkg>`.
2. `__init__.py` exposes only the curated public API and defines `__all__`.
3. `__main__.py` runs a self-demo through `python -m <sample_pkg>`.
4. `py.typed` is included as package data so type information is visible to downstream type checkers.
5. `config.py` exposes the frozen `pydantic-settings` configuration API: `BaseSettings`, env-prefix handling, and `load()` / `save_defaults()`.
6. `exceptions.py` exposes typed What, Why, and Fix exception details.
7. `_contracts.py` owns frozen Pydantic models, Result shapes, and `StrEnum`-based codes.
8. `validators.py` contains pure validation functions that are called from `model_validator` methods.
9. `main.py` owns the CLI entry point.

## Consequences

### Positive

- New Python repositories start with a typed package layout instead of a blank source tree.
- Public API, runtime entry points, package typing, settings, contracts, validation, exceptions, and CLI wiring have predictable homes.
- The skeleton remains generic enough for downstream repositories to specialize without undoing framework-specific assumptions.

### Negative

- The template must maintain sample package files in addition to QA scripts and workflow assets.
- Consumers that want a different layout must consciously replace the skeleton rather than starting from an empty package.

### Neutral

- The skeleton is a template starting point, not an organization-wide application architecture. Consumer repositories can add local ADRs when they choose domain-specific layers or frameworks.

## Assumptions

1. Downstream repositories benefit from an example package shape that is more concrete than documentation alone.
2. The template continues to target Python 3.11 or newer.
3. Consumer repositories remain responsible for domain-specific architecture beyond this generic package anatomy.

## Supersedes

None.

## Superseded by

None (current).

## Implementing PRs

- PT-M3: Ship the minimal generic `src/sample_app` package skeleton matching this ADR's eight-file anatomy.

## Related ADRs

- [ADR-0003](0003-python-minimum-version-floor.md): Python minimum version floor.

## Compliance Notes

None.

## Changelog

| Date       | Change                                     | Reason                                            | Author/Role                         | Body-diff? |
| ---------- | ------------------------------------------ | ------------------------------------------------- | ----------------------------------- | ---------- |
| 2026-06-03 | Accepted the template package layout ADR.  | Document the package anatomy before implementation. | Portfolio maintainer / template ADR | Yes        |
| 2026-06-03 | Landed the minimal generic package skeleton. | Record the implementing package anatomy landing.  | Implementation agent / template PR  | Yes        |
