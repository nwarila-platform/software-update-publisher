# ADR-0002: Pull-Based, Manifest-Driven Template Sync

| Field            | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| ID               | ADR-0002                                                                     |
| Scope            | Template                                                                     |
| Status           | Accepted                                                                     |
| Decision-subject | Template updates are synced by downstream-owned pull requests and manifests. |
| Date accepted    | 2026-04-08                                                                   |
| Date             | 2026-06-03                                                                   |
| Last reviewed    | 2026-06-03                                                                   |
| Authors          | Nick Warila (@NWarila)                                                       |
| Decision-makers  | Nick Warila (sole portfolio maintainer)                                      |
| Consulted        | GitHub Actions reusable workflow docs, git submodule docs.                   |
| Informed         | Downstream Python repositories.                                              |
| Reversibility    | Medium                                                                       |
| Review-by        | 2026-11-30                                                                   |

## TL;DR

Template updates are delivered to downstream repositories as reviewable pull requests triggered by each repo on its own schedule, not pushed from the template. File mappings are defined in a machine-readable manifest (`sync-manifest.json`), not hardcoded in workflow YAML.

## Context and Problem Statement

A central Python QA template must deliver updated scripts, configs, and reference files to downstream repositories without requiring cross-repo credentials, without bypassing PR review, and without coupling downstream release cadences to the template.

Three distribution mechanisms were evaluated: git submodules, a versioned Python package, and a manifest-driven file-sync workflow.

An earlier prototype used a push-based `sync-downstream.yml` workflow that required a fine-grained PAT (`TEMPLATE_SYNC_PAT`) with write access to every downstream repo. That PAT was never configured, making the workflow inoperative, and the design is fundamentally incompatible with keeping each repo's update pace self-controlled.

## Decision Drivers

1. Downstream repos must be able to review and merge template updates at their own pace.
2. No cross-repo write credentials (PATs or push permissions) from the template side.
3. Both scripts and config files must be synced; package installs only handle code.
4. Some files need partial replacement (marker-preserving merge) rather than full overwrite.
5. Every sync PR must be attributable to a specific template release tag for audit.

## Considered Options

1. Push-based workflow with cross-repo PAT.
2. Git submodule pinned to a template commit.
3. Versioned Python package installed as a dev dependency.
4. Pull-based reusable workflow with `sync-manifest.json`.

## Decision Outcome

Chosen option: **Option 4, pull-based reusable workflow with `sync-manifest.json`.**

The template publishes a GitHub release whenever `scripts/` changes (via `auto-release.yml`). Each downstream repository owns a thin `template-sync.yml` wrapper that calls the reusable `self-update.yml` from a pinned template release. The reusable workflow checks for a newer release, reads `sync-manifest.json` for source-to-destination mappings, and opens a pull request using the downstream repo's own `GITHUB_TOKEN`. No cross-repo credentials are required.

`sync-manifest.json` declares per-file `mode`: `overwrite` for fully managed files (scripts, pre-commit config, VSCode settings) and `marker-preserve` for files where template-owned regions must be updated while repo-specific sections are retained (e.g., `tasks.json`).

## Pros and Cons of the Options

### Option 1: Push-based workflow with cross-repo PAT

- Good, because the template controls delivery timing.
- Bad, because it requires a PAT with write access to every downstream repo.
- Bad, because PATs are tied to a personal account and create a single point of failure.
- Bad, because downstream repos cannot defer or review updates before they land.

### Option 2: Git submodule

- Good, because it uses native git tooling.
- Bad, because submodules pin to a commit, not a release; there is no selective file mapping.
- Bad, because downstream repos get no PR with migration notes - the submodule bump is one diff line.
- Bad, because submodule workflows are brittle across clone contexts.

### Option 3: Versioned Python package

- Good, because version management is explicit via `pip install`.
- Bad, because package installs cannot deliver non-Python config files (`.gitignore`, VSCode JSON, pre-commit YAML).
- Bad, because it adds a template-infrastructure install to every downstream developer setup.

### Option 4: Pull-based reusable workflow with manifest

- Good, because downstream repos retain full review control.
- Good, because no cross-repo credentials are required from the template side.
- Good, because scripts and config files are both covered by the manifest.
- Good, because per-file merge strategies (`overwrite` vs `marker-preserve`) are explicit.
- Good, because every sync PR references the source release tag.
- Bad, because downstream repos must own a thin wrapper workflow and can fall behind if they skip updates.

## Confirmation

1. `sync-manifest.json` at the repository root defines all synced source-to-destination mappings.
2. `self-update.yml` supports `workflow_call` so downstream repos can call it as a reusable workflow.
3. The reusable workflow uses `GITHUB_TOKEN` (downstream repo's own token) for PR creation - no PAT.
4. `auto-release.yml` creates a new release when `scripts/` changes merge to `main`.
5. This repo dogfoods the sync mechanism via a nightly scheduled run of `self-update.yml`.

## Consequences

### Positive

- Each downstream repo controls its own update cadence.
- Template releases are reviewable and rollback-able.
- No cross-repo credentials are held by the template.

### Negative

- Downstream repos can drift from the template if they skip sync PRs.
- Workflow-created PRs do not trigger CI automatically (see `docs/GITHUB_TOKEN_LIMITATION.md`).

### Neutral

- The per-file manifest is the single source of truth for what the template owns; adding a new synced file requires a manifest entry and a `.gitignore` allowlist update in downstream repos.

## Assumptions

1. Downstream repos maintain their own `template-sync.yml` wrapper workflow.
2. The template maintains backward-compatible `self-update.yml` behavior within a major version.

## Supersedes

- Push-based `sync-downstream.yml` prototype (removed in PR #4).

## Superseded by

None (current).

## Implementing PRs

- PR #4: Replace push-based sync with pull-based reusable workflow.

## Related ADRs

- [ADR-0001](0001-scripts-are-standalone-and-stdlib-only.md): QA scripts are standalone and stdlib-only.
- [org ADR-0004 (Use Renovate for dependency updates)](../org/0004-use-renovate-for-dependency-updates.md): `.github/renovate.json5`.

## Compliance Notes

None.

## Changelog

| Date       | Change                                  | Reason                                             | Author/Role                         | Body-diff? |
| ---------- | --------------------------------------- | -------------------------------------------------- | ----------------------------------- | ---------- |
| 2026-06-03 | Reformatted to the living ADR schema.   | Satisfy the template ADR conformance gate.         | Portfolio maintainer / template ADR | Yes        |
