# ADR-0005: CI Excludes macOS

| Field            | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| ID               | ADR-0005                                                                     |
| Scope            | Template                                                                     |
| Status           | Accepted                                                                     |
| Decision-subject | CI test matrices exclude macOS; tests run on Ubuntu and Windows only.        |
| Date accepted    | 2026-06-04                                                                   |
| Date             | 2026-06-04                                                                   |
| Last reviewed    | 2026-06-04                                                                   |
| Authors          | Nick Warila (@NWarila)                                                       |
| Decision-makers  | Nick Warila (sole portfolio maintainer)                                      |
| Consulted        | GitHub Actions per-minute billing documentation.                            |
| Informed         | Downstream Python repositories.                                              |
| Reversibility    | High                                                                         |
| Review-by        | 2026-12-04                                                                   |

## TL;DR

This template's CI never tests on macOS. The `python-qa.yml` reusable workflow and the template's own `template-ci.yml` run their OS matrices on `ubuntu-latest` and `windows-latest` only. GitHub-hosted macOS runners bill at roughly ten times the Linux per-minute rate, and no repository in this portfolio runs on macOS at runtime, so macOS coverage is cost without benefit.

## Context and Problem Statement

The template ships a reusable CI workflow (`python-qa.yml`) that downstream repositories call, plus its own dogfooding workflow (`template-ci.yml`). Both previously ran their lint/type/test jobs across a three-OS matrix that included `macos-latest`.

GitHub bills macOS minutes at approximately 10x the Linux rate (Windows is approximately 2x). Every consumer that runs the full matrix therefore pays a large, recurring macOS premium. At the same time, the portfolio's runtime target is Linux: the autonomous porting loop in `the-hero-wars-guys/herowars-engine-porter` deploys to a read-only Linux container, and no NWarila project ships a macOS artifact or runs on macOS in production. macOS coverage was catching only macOS-runner-specific issues (for example, an async-timing flake on macOS-arm64) that have no bearing on where the code actually runs.

The maintainer develops on Windows, so Windows CI coverage remains valuable for catching path-separator and line-ending issues before they reach a teammate or a Windows contributor.

## Decision Drivers

1. macOS GitHub-hosted runners cost about 10x Linux minutes; the premium is recurring across every consumer.
2. The portfolio's deployment target is Linux containers; nothing runs on macOS at runtime.
3. Windows is the maintainer's development platform and still warrants CI coverage.
4. macOS-only test failures have no deployment relevance and add flake surface.
5. Keep the decision and its enforcement (the CI matrices) in one place that all consumers inherit.

## Considered Options

1. Keep the full three-OS matrix (Ubuntu + Windows + macOS).
2. Run Ubuntu + Windows only (drop macOS).
3. Run Ubuntu only (drop macOS and Windows).

## Decision Outcome

Chosen option: **Option 2, run Ubuntu + Windows only.**

Both `python-qa.yml` (the `full-os-matrix` "full" branch) and `template-ci.yml` use `["ubuntu-latest", "windows-latest"]`. The `full-os-matrix` input is retained: when true the matrix is Ubuntu + Windows, when false it is Ubuntu-only. macOS is never a matrix entry. Consumers inherit this through the reusable workflow.

## Pros and Cons of the Options

### Option 1: Keep the full three-OS matrix

- Good, because it would catch macOS-specific regressions.
- Bad, because macOS runners bill at roughly 10x Linux for coverage of a platform nothing in the portfolio runs on.
- Bad, because macOS-runner-specific flakes (timing, arm64) block CI without indicating a real deployment defect.

### Option 2: Ubuntu + Windows only

- Good, because it removes the 10x macOS premium entirely.
- Good, because it keeps Ubuntu (the deployment target) and Windows (the development platform) covered.
- Neutral, because genuine macOS-specific bugs would go uncaught, which is acceptable given no macOS runtime.

### Option 3: Ubuntu only

- Good, because it is the cheapest matrix.
- Bad, because it drops Windows coverage even though the maintainer develops on Windows and the QA scripts have Windows-specific paths.

## Confirmation

1. `.github/workflows/python-qa.yml` matrix `os` lists resolve to `["ubuntu-latest", "windows-latest"]` (full) or `["ubuntu-latest"]` (minimal); no entry contains `macos-latest`.
2. `.github/workflows/template-ci.yml` test job matrix is `[ubuntu-latest, windows-latest]`.
3. A repository-wide search for `macos-latest` in `.github/workflows/` returns nothing.

## Consequences

### Positive

- The recurring macOS billing premium is eliminated for the template and every consumer.
- CI no longer fails on macOS-runner-specific flakes that have no deployment relevance.
- The covered platforms match where the code is actually built (Linux) and developed (Windows).

### Negative

- Genuine macOS-specific defects would not be caught in CI.
- A future need to support macOS at runtime would require revisiting this decision and the matrices together.

### Neutral

- The `full-os-matrix` input keeps its name; "full" now means Ubuntu + Windows rather than three OSes.

## Assumptions

1. No repository in the portfolio ships a macOS artifact or runs on macOS in production.
2. The maintainer's local QA on Windows, plus Windows CI, is sufficient Windows-platform assurance.
3. GitHub's macOS-versus-Linux runner pricing differential persists.

## Supersedes

None.

## Superseded by

None (current).

## Implementing PRs

The PR that drops `macos-latest` from `python-qa.yml` and `template-ci.yml` and adds this ADR.

## Related ADRs

- [ADR-0002](0002-pull-based-manifest-driven-template-sync.md): Pull-based, manifest-driven template sync (how consumers inherit template CI changes).

## Compliance Notes

None.

## Changelog

| Date       | Change                                   | Reason                                                          | Author/Role                         | Body-diff? |
| ---------- | ---------------------------------------- | -------------------------------------------------------------- | ----------------------------------- | ---------- |
| 2026-06-04 | Accepted: CI excludes macOS.             | macOS runners bill ~10x and no portfolio code runs on macOS.    | Portfolio maintainer / template ADR | Yes        |
