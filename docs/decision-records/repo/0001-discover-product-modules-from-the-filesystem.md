# ADR-0001: Discover Product Modules From The Filesystem

| Field            | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| ID               | ADR-0001                                                                     |
| Scope            | Repo                                                                         |
| Status           | Accepted                                                                     |
| Decision-subject | Product modules are discovered by walking a package, not by entry points.    |
| Date accepted    | 2026-09-18                                                                   |
| Date             | 2026-09-18                                                                   |
| Last reviewed    | 2026-09-18                                                                   |
| Authors          | Nick Warila (@NWarila)                                                       |
| Decision-makers  | Nick Warila (sole portfolio maintainer)                                      |
| Consulted        | CPython `importlib.metadata` and `pkgutil` documentation; packaging entry-points specification. |
| Informed         | Contributors adding tracked products.                                        |
| Reversibility    | Medium                                                                       |
| Review-by        | 2027-09-18                                                                   |

## TL;DR

Product modules are found by walking `src/software_update_publisher/products/` with `pkgutil.iter_modules`, filtered on `ispkg`, sorted, and imported one at a time. Declared entry points were rejected because they are read from installed distribution metadata, so a fresh clone would discover nothing.

## Context and Problem Statement

The repository tracks a growing set of applications, each with its own upstream. The stated architecture is that adding a tracked product means adding a folder and changing nothing outside it. Something has to turn that folder into a loaded module, and the choice determines whether the promise is true.

## Decision Drivers

1. A clone of this repository must work without an install step.
2. Discovery order must be deterministic, because a run's report is read by a human.
3. One broken product must not prevent the other products from running.
4. A reader should be able to tell what will run without executing anything.

## Considered Options

1. `pkgutil.iter_modules` over the `products` package.
2. Declared entry points in `pyproject.toml`.
3. A manifest file per product folder, parsed before any import.
4. A hand-maintained registry listing every module.

## Decision Outcome

Chosen option: **1, `pkgutil.iter_modules` over the `products` package.**

`importlib.metadata` resolves entry points from a distribution's installed metadata. A contributor who clones this repository and runs it would therefore find zero products until they ran an install, which is the wrong failure for a repository whose premise is that adding a folder is enough. A manifest is a second source of truth and a second parser for a safety margin this repository does not need, and a hand-maintained registry makes every new product a change to a shared file.

Two consequences are accepted deliberately. A module must be imported before its declaration can be read, so imports are contained per product and reported rather than raised. And `iter_modules` reports a directory as a package only when it contains `__init__.py`, so a folder carrying `product.py` without one is detected separately and reported, rather than silently not tracked.

## Pros and Cons of the Options

### Option 1: Walk the package

- Good, because a clone works with no install step.
- Good, because ordering is explicit and stable.
- Good, because static analysis sees every module.
- Bad, because a declaration cannot be read without importing its module.

### Option 2: Entry points

- Good, because per-module dependencies could be declared.
- Bad, because discovery returns nothing from a source checkout.
- Bad, because order is declaration order, so sorting is needed anyway.
- Neutral, because no product module may declare its own dependency in this design.

### Option 3: Per-folder manifest

- Good, because a declaration is readable without importing anything.
- Bad, because it is a second source of truth beside the module itself.

### Option 4: Hand-maintained registry

- Good, because what runs is visible in one file.
- Bad, because it makes adding a product a change to shared code, which is the thing this design removes.

## Confirmation

`tests/test_loader.py` asserts ordering, that a loose module beside the packages is ignored, that a directory without `product.py` is ignored, that a folder with `product.py` and no `__init__.py` is reported, and that one failing import does not hide the others.

## Consequences

Adding a product is adding a folder; no allowlist entry, registry line, or packaging metadata changes. A product module can never ship from a separate distribution without revisiting this decision. Entry points could be layered on top later without changing the module contract.

## Assumptions

Every product module lives in this repository. If externally distributed products ever become a requirement, this ADR is superseded rather than amended.

## Supersedes

None.

## Superseded by

None.

## Implementing PRs

- `feat: load product modules dynamically, and track Google Chrome`

## Related ADRs

- [ADR-0002](0002-extract-identity-from-the-artifact.md)

## Compliance Notes

None.

## Changelog

| Date | Version | Change | Author | Notes |
| ---- | ------- | ------ | ------ | ----- |
| 2026-09-18 | 1.0 | Accepted | Nick Warila | Recorded with the loader it describes. |
