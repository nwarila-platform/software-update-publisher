# Python Template Plan

## Mission

Create `NWarila/python-template` and `NWarila/.github` as the two-layer
standard for every Python repository in the organization.

- `.github` owns organization-wide governance, repository policy, workflow
  templates, and non-language-specific automation.
- `python-template` owns the Python-specific developer experience, quality
  gates, reusable workflows, and reference configuration.
- Each downstream repository owns its domain logic, package metadata,
  product-specific workflows, and documentation.

This is also a portfolio asset. The consistency, polish, and rigor across the
organization should be visible to recruiters before they read any source code.

## Desired End State

- Any engineer can move between Python repos and find the same setup flow, the
  same QA commands, and the same CI contract.
- Local development, pre-commit, and CI all execute the same underlying checks.
- New repos can be brought to a "green" baseline quickly, with minimal custom
  glue.
- Shared standard changes arrive in downstream repos as reviewable PRs, not as
  hidden drift.
- Exceptions are explicit, versioned, and rare.
- Recruiters see stable checks, coverage visibility, clean READMEs, and
  intentional engineering standards everywhere.

## Guiding Principles

- `pyproject.toml` is the center of gravity for package metadata and tool
  configuration.
- Local must match CI. If the behavior differs, the template is wrong.
- Cross-platform support is a first-class requirement: Windows, macOS, and
  Linux must all be considered during design, not patched later.
- The standard should be opinionated by default, but have documented and
  auditable escape hatches.
- Template-owned files should stay small, generic, and stable. Repo-specific
  concerns stay in the repo.
- One stable required status check should represent "the Python bar was met."
- Visible quality is part of product quality.

## Standards Stack

| Layer | Owns | Examples |
| --- | --- | --- |
| `.github` | Org-wide governance and workflow entry points | Community health files, issue/PR templates, ruleset guidance, workflow templates, dependency-review enforcement, markdown/action lint, link checking |
| `python-template` | Python-specific standard | Reusable Python QA workflow, setup action, QA scripts, reference `pyproject.toml`, pre-commit config, VSCode defaults, packaging/security/type/test policy |
| Downstream repo | Product-specific behavior | Package metadata, runtime dependencies, README, release workflow, deploy workflow, repo-specific tasks, repo-specific ignore rules |

## Current Reality

The shared CI surface is now implemented: the reusable Python QA workflow
(`python-qa.yml`), `auto-release.yml`, `self-update.yml`, and `template-ci.yml`
ship under `.github/workflows/`, backed by the QA scripts (`qa.py`,
`check_*.py`) and the `setup-python` composite action. Remaining work is
convergence cleanup, not initial extraction:

- The QA script ownership is now settled: `scripts/` is the canonical source,
  and `.github/scripts/` is the released/synced copy used for self-dogfooding.
- Some scripts and reference files may still carry resume-specific package
  names, paths, build flows, or artifacts to scrub.
- The current plan assumes external composite actions will power CI, but that
  conflicts with the stated goal that local and CI should run the exact same
  downstream scripts.
- Ownership boundaries for syncable files versus repo-owned files are not yet
  crisp enough to prevent merge friction.

This revision tightens the architecture so the implementation backlog matches
the quality bar we are trying to set.

## Recommended Architecture

### Core decision

Use reusable workflows for centrally maintained CI orchestration, and keep
composite actions small and tactical.

Why this is the better fit:

- GitHub's current documentation distinguishes reusable workflows from
  composite actions: reusable workflows can contain multiple jobs, can use
  secrets, and preserve step-level logging.
- GitHub also documents that when a reusable workflow in another repository
  uses `actions/checkout`, it checks out the caller repository, not the called
  repository. That means a centrally maintained workflow can still execute the
  synced local scripts in the downstream repo.
- Composite actions still have value for small step bundles such as environment
  bootstrap, but they should not be the main abstraction for our full CI
  contract.

### Resulting model

1. `python-template` ships the canonical `scripts/` implementation.
2. Downstream repos sync the template-owned script/config files into their own
   repository.
3. Local development runs those synced scripts directly.
4. CI in downstream repos calls a reusable workflow from `python-template`.
5. That reusable workflow checks out the downstream repo and runs the same
   synced scripts that developers use locally.
6. Branch protection or rulesets target a single stable `ci-passed` check.

### Repository shape

```text
NWarila/python-template
├── .github/
│   ├── actions/
│   │   └── setup-python/
│   │       └── action.yml         # Small shared bootstrap action
│   ├── scripts/                   # Released script copies for self-dogfooding
│   │   ├── .version               # Release-copy metadata; only deliberate extra
│   │   └── (mirrors scripts/)
│   └── workflows/
│       ├── auto-release.yml       # Auto-creates a release when scripts/ changes
│       ├── python-qa.yml          # Reusable workflow for downstream repos
│       ├── self-update.yml        # Nightly: pulls released files from latest release
│       └── template-ci.yml        # This repo's own CI (uses .github/scripts/)
├── scripts/
│   ├── check_lint.py
│   ├── check_types.py
│   ├── check_tests.py
│   ├── check_security.py
│   ├── check_spelling.py
│   ├── check_package.py
│   ├── qa.py
│   ├── sync.py
│   ├── setup.sh
│   └── setup.ps1
├── reference/
│   ├── pyproject.toml
│   ├── pre-commit-config.yaml
│   ├── markdownlint-cli2.jsonc
│   ├── tasks.json
│   ├── settings.json
│   ├── extensions.json
│   ├── gitignore
│   ├── gitattributes
│   └── repo-ci.yml
├── sync-manifest.json                # Source→dest mappings read by downstream sync workflows
└── README.md
```

## Standard Contract For Downstream Repositories

### Required baseline

Every Python repo that adopts the standard should have:

- `pyproject.toml`
- A declared Python support range
- A clear source layout
- A test location
- An org-standard `.gitignore` that starts with `**` and explicitly allowlists tracked roots
- An org-standard `.gitattributes` baseline aligned with `.github`
- Synced `.github/scripts/` from `python-template`
- A `.pre-commit-config.yaml`
- A CI workflow that delegates to the shared reusable workflow or mirrors its
  contract exactly

### Preferred repository profile

V1 should optimize for repos that have importable Python code under `src/`.
This includes libraries, CLIs, internal apps, and most automation projects.

Script-only repos are still in scope, but should initially be supported via an
explicit opt-out of the packaging gate rather than through a separate script-
first architecture.

### Configuration philosophy

No custom config namespace. Scripts infer behavior from standard `pyproject.toml`
sections that repo admins already control:

| Script behavior | Inferred from | Default when absent |
| --- | --- | --- |
| Source paths for lint/types | `[tool.ruff] src` | `["src"]` |
| Test paths | `[tool.pytest.ini_options] testpaths` | `["tests"]` |
| Coverage threshold | `[tool.pytest.ini_options] --cov-fail-under` | 90 |
| Strict typing | `[tool.mypy] strict` | `true` |
| Run package check | `[build-system]` section exists | Skip if absent |
| Smoke entry points | `[project.scripts]` section exists | Skip if absent |
| Codespell ignore list | `[tool.codespell] ignore-words-list` | Empty |

CI matrix dimensions (Python versions, OS coverage) are controlled via
reusable workflow inputs — not pyproject.toml, since they are CI concerns.

Local overrides use CLI arguments: `qa.py --skip package` or
`check_lint.py --fix`. Repo admins control their quality bar through the
standard tool config sections they already maintain.

### Python support window policy

The template should align its defaults to CPython's upstream support policy,
not to habit.

- New repos should not launch on a minimum Python version with less than
  12 months of upstream support remaining.
- As of April 7, 2026, CPython 3.10 is already in security-fix-only support
  and reaches end-of-life in October 2026, so the default floor for new repos
  should remain `>=3.11`.
- Template defaults should be reviewed after each annual CPython feature
  release and ratcheted forward intentionally, not ad hoc.
- Scheduled or non-required CI may include prerelease interpreters, but the
  required branch-protection matrix should target supported stable versions.

## Python Quality Standard

| Concern | Standard direction | Notes |
| --- | --- | --- |
| Project metadata | `pyproject.toml` with `[build-system]`, `[project]`, and `[tool.*]` | Keep package metadata and QA config centralized |
| Source layout | Prefer `src/` for importable code | Reduces accidental imports from the repo root |
| Lint + format | Ruff owns both | Avoid parallel Black/isort/Flake8 duplication |
| Type checking | Mypy baseline, strict by default for new repos | Legacy repos may adopt in stages, but must ratchet upward |
| Tests | `pytest` with explicit `testpaths` and `--import-mode=importlib` for new repos | Keeps import behavior closer to installed reality |
| Coverage | Enforced threshold plus Actions job summary | New repos default to 90% |
| Security | `pip-audit` in CI plus GitHub dependency review on PRs | CodeQL belongs in `.github` policy, not a V1 blocker |
| Packaging | `validate-pyproject`, build wheel/sdist, `twine check`, optional entry-point smoke | Auto-enabled when `[build-system]` exists |
| Spelling | `codespell` | Repo-local `[tool.codespell]` controls ignore list |
| Hooks | `pre-commit` with `pre-commit` and `pre-push` installation | CI remains the source of truth |
| Editor DX | Shared VSCode settings/extensions/tasks where practical | Generic only; no repo-specific build logic in template-owned files |

### Ruff rule set

The org-standard ruff rule selection:

```toml
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "W",    # pycodestyle warnings
    "I",    # isort (import ordering)
    "UP",   # pyupgrade (modernize syntax)
    "B",    # flake8-bugbear (common bug patterns)
    "S",    # flake8-bandit (security)
    "SIM",  # flake8-simplify
    "C4",   # flake8-comprehensions (cleaner comprehensions)
    "PT",   # flake8-pytest-style (pytest best practices)
    "T20",  # flake8-print (no print statements in library code)
    "RUF",  # ruff-specific rules
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]       # assert is fine in tests
"scripts/**" = ["T20"]      # print is fine in QA scripts
```

**Rationale**: `E`/`F`/`W` are baseline correctness. `I` ensures consistent
imports (ruff replaces isort). `UP` keeps code modern. `B` catches real bugs.
`S` aligns with the security-first philosophy. `SIM`/`C4` enforce clean
idiomatic Python. `PT` standardizes pytest usage. `T20` prevents debug prints
from reaching library code (QA scripts are excluded). `RUF` catches
ruff-specific issues. `line-length = 120` balances readability with modern
wide displays.

### Coverage and typing policy

The standard distinguishes greenfield from legacy adoption:

- New repos: default to `strict = true` in `[tool.mypy]` and
  `--cov-fail-under=90` in `[tool.pytest.ini_options]`.
- Existing repos: start from their real baseline if needed, but never lower the
  threshold after adopting the standard.
- Any temporary waiver must be explicit, visible, and time-bounded.

### Inference from current sources

Official docs strongly support `pyproject.toml`, `src/` layout, Ruff, reusable
workflows, dependency review, and pre-commit. They also suggest that `uv` is
mature enough to pilot as the default developer toolchain, but not yet so
uniformly supported across the ecosystem that we should declare it final
without first validating it in pilot repos.

## Toolchain Recommendation To Ratify

### Proposed default for new repos

- Use `uv` as the primary environment and dependency workflow.
- Keep `pyproject.toml` as the metadata source of truth.
- Use `[dependency-groups]` for local development groups if `uv` is ratified.
- Commit `uv.lock` for deterministic installs.
- Use wrapper scripts and VSCode tasks so developers interact with a stable
  repo interface, not a moving tool CLI.

### Why this is attractive

- `uv` now has official guidance for GitHub Actions, lockfiles, dependency
  groups, and dependency-bot integration.
- It reduces tool sprawl while still allowing export to `requirements.txt`,
  `pylock.toml`, and CycloneDX when needed.
- It supports Windows, macOS, and Linux, which fits the org standard.

### Why this is not locked yet

- The `uv` docs explicitly note that dependency groups are standardized but not
  yet supported by all tools.
- Dependency-bot support exists (the repo uses Renovate per ADR-0004, which
  has documented `uv` integration), but Astral's own docs still call out
  incomplete scenarios.
- We should prove the workflow in at least two real repos before making it the
  mandatory baseline.

### Dependency graph and advisory visibility caveat

`uv` looks strong as a developer workflow, but GitHub's current dependency-
graph documentation still describes Python support primarily around
`requirements.txt`, `pipenv`, and Poetry-style manifests. Before `uv` becomes
mandatory, pilot repos need to prove that the GitHub-native security surface is
still good enough:

- Dependency graph visibility
- Dependabot security alerts (advisory visibility; version updates are handled
  by Renovate per ADR-0004)
- Dependency review on pull requests
- Any needed lockfile or dependency-submission compatibility workarounds

If the pilot exposes a gap, the standard should add a compensating mechanism
instead of hand-waving the gap away.

## Sync And Ownership Model

### Template-owned and synced

These should be auto-updated by release-triggered PRs:

- `scripts/**`
- `.pre-commit-config.yaml`
- `.markdownlint-cli2.jsonc`
- `.vscode/settings.json`
- `.vscode/extensions.json`

### Sync-managed with marker-preserving merge

These are synced by release-triggered PRs, but use region-delimited sections
to preserve repo-specific content:

- `.vscode/tasks.json` — template-owned QA regions are replaced; repo-specific
  task regions are preserved

### Reference-only starters

These define mandatory org-standard starting points for new repos, but are not
auto-overwritten after initial creation in V1 because repo-specific extensions
still need explicit review:

- `reference/pyproject.toml`
- `reference/repo-ci.yml`
- `reference/gitignore` - starts with `**` and uses an explicit allowlist model
- `reference/gitattributes` - comment-rich normalization and diff baseline aligned with `.github`

### Repo-owned

These always remain local to the downstream repository:

- `README.md`
- `LICENSE`
- Package name, description, runtime dependencies, and entry points
- Deployment and release workflows
- Product-specific VSCode tasks
- Repo-specific tracked-root allowlist additions in `.gitignore`
- Repo-specific binary or file-type additions in `.gitattributes`

### Sync policy

- Every sync PR must reference the source template release tag.
- Every sync PR must include migration notes when behavior changes.
- Every synced file should carry a lightweight "managed by template" header
  comment where the file format allows it.
- High-churn files should remain reference-only unless we build a safe
  marker-preserving merge strategy.
- Sync automation should read from a machine-readable manifest
  (for example `sync-manifest.json`) that defines source path, destination
  path, ownership mode, and merge strategy. The workflow should never rely on
  a hardcoded path list buried in implementation code.

## CI And Workflow Model

### `.github` responsibilities

The `.github` repository should provide:

- Workflow templates that new repos can select from the GitHub UI
- Workflow-template metadata files (`.properties.json`) and `$default-branch`
  placeholders where appropriate
- Issue and PR templates
- Community health files
- Ruleset guidance or enforcement for required workflows
- Shared non-language checks such as markdown lint, action lint, shell lint,
  and link checking
- Dependency review as an org-level required workflow where appropriate

### `python-template` responsibilities

`python-template` should provide:

- A reusable `python-qa.yml` workflow that runs against the caller repo
- A stable `ci-passed` aggregator job
- A small bootstrap action for Python environment setup if still useful
- The synced local scripts that implement the actual checks

### Self-dogfooding model

The template repo eats its own dog food by running CI against *released*
scripts rather than the development source. This ensures that new script
changes are validated by the same mechanism downstream repos use.

`scripts/` is the canonical development source. `.github/scripts/` is the
released copy and should differ only by `.github/scripts/.version`, which
records the release tag currently pulled into that tree. Source scripts remain
standalone files; `scripts/` is not an importable package.

**How it works:**

1. `scripts/` is the development source for all check scripts and setup
   scripts.
2. When changes to `scripts/` are merged to `main`, `auto-release.yml`
   automatically creates a new patch release (auto-incrementing from the
   latest tag).
3. A nightly scheduled workflow (`self-update.yml`) checks whether a new
   release exists. When it detects one, it pulls the released files via the
   same manifest-driven sync that downstream repos use, and opens a PR.
4. `template-ci.yml` runs all quality gates from `.github/scripts/` — the
   released copies — not from `scripts/` directly.

**Why this matters:**

- The template validates itself using the same artifacts and sync mechanism
  it ships to consumers.
- Script regressions are caught before downstream repos receive them.
- The release-and-pull pipeline is exercised continuously, not only at
  manually triggered milestones.

**Bootstrap:** `.github/scripts/` is initially seeded from the current
`scripts/` directory. After the first release and nightly cycle, it is kept
in sync automatically.

### Default CI policy

- PR workflow: required, comprehensive, and still expected to stay fast for
  this organization's current small repositories
- Main-branch or scheduled workflow: broader compatibility matrix when needed
- One required `ci-passed` check name across repos

### Default matrix policy

Current default:

- PRs: 3 operating systems x min/max supported Python versions
- Main or scheduled: keep the same baseline, and optionally add prerelease or
  extended compatibility jobs as non-required checks

This is intentionally stricter than a typical "Ubuntu-only on PRs" baseline.
For this portfolio, the repos are small enough that the matrix cost is
acceptable and the cross-platform signal is part of the value proposition.

### Security policy

- Pin third-party GitHub Actions to full-length commit SHAs.
- Internal `python-template` reusable workflow references may use `@v1` as the
  semver contract.
- Required job names must be unique across workflows to avoid ambiguous branch
  protection behavior.
- Use Renovate version updates (`.github/renovate.json5`, per ADR-0004) for
  GitHub Actions and reusable workflow references so SHA-pinned dependencies
  still move forward deliberately.
- Do not rely on GitHub security alerts alone for SHA-pinned actions; GitHub's
  dependency-graph docs explicitly scope action alerts to semantic-versioned
  refs rather than SHA pins.

### Ruleset baseline

Rulesets should be treated as the governance primitive for the organization.

- Use repository-level rulesets everywhere they are available.
- Use organization-wide rulesets when the GitHub plan supports them; otherwise
  document a repo-level baseline in `.github` and apply it consistently.
- The default protected-branch baseline should include:
  - Require a pull request before merging
  - Require status checks to pass before merging
  - Require linear history
  - Block force pushes
  - Require code scanning results where CodeQL is enabled
  - Require dependency review where the workflow exists
- Evaluate required signed commits separately after confirming bot, release,
  and sync-automation compatibility.

### Supply chain and release integrity

For published artifacts, the standard should leave room for stronger supply-
chain signals than pass/fail CI alone.

- Release workflows should be designed so SBOM export and provenance
  attestations can be added cleanly.
- GitHub's attestation guidance makes reusable workflows especially valuable:
  attestations alone provide SLSA Build Level 2, and shared reusable build
  workflows help move toward Build Level 3.
- This does not need to block V1 for every repo, but the architecture should
  not paint us into a corner.

## Release And Compatibility Policy

`python-template` is itself a product and needs a stable upgrade contract.

- The template follows semantic versioning.
- Breaking changes ship only in major releases.
- Tightening a default quality gate, changing a managed file's shape, removing
  a synced file, or changing script/workflow interfaces counts as a breaking
  change unless explicitly backward-compatible.
- Deprecations must be announced at least one minor release before removal.
- Every release must include migration notes, managed-file impact, and any
  required downstream action.
- Downstream repos may use `@v1` for normal consumption, but exact release tags
  should remain easy to reference for investigations and rollback.

## Implementation Plan

### Phase 0: Ratify the contract

- [ ] Finalize the architecture shift to reusable workflows for CI
- [ ] Codify `uv` as the pilot default and document the `pip` + `venv`
      fallback path
- [ ] Document the inference rules: how scripts derive behavior from standard
      `pyproject.toml` sections (no custom config namespace)
- [ ] Define the Python support policy relative to the CPython lifecycle
- [ ] Decide which files are sync-managed versus reference-only
- [ ] Decide the ruleset baseline and repo-level fallback if org-wide rulesets
      are not available on the current GitHub plan
- [ ] Codify the default PR matrix and 90% greenfield coverage floor in the
      reference config and docs

Exit criteria:

- The plan is internally consistent
- The repo contract is documented
- No major ownership ambiguity remains

### Phase 1: Generic script foundation

- [ ] Establish the inline config-reading pattern (stdlib `tomllib`, read
      `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`, and
      `[build-system]` sections) that each script will duplicate independently
      — no shared module
- [ ] Remove every `.github/scripts` path assumption from the scripts
- [x] Remove every resume-specific path, package name, and CLI assumption
- [ ] Standardize script CLI contracts (`--fix`, `--paths`, `--skip`, config
      lookup, clean exit codes)
- [ ] Make `qa.py` auto-discover `check_*.py` scripts and honor repo profile
      opt-outs
- [ ] Teach `check_package.py` to discover `[project.scripts]` and only run
      entry-point smoke tests when appropriate
- [ ] Add coverage summary output to `$GITHUB_STEP_SUMMARY`

Exit criteria:

- A minimal smoke project can run the scripts locally on Windows, macOS, and
  Linux
- No checked-in script contains resume-specific references
- The script interface is documented and stable

### Phase 2: Workflow architecture

- [ ] Add `.github/workflows/python-qa.yml` as the reusable downstream QA
      workflow
- [ ] Add `.github/workflows/template-ci.yml` to dogfood the template itself
- [ ] Decide whether `actions/setup-python` remains the bootstrap action or is
      replaced by a more general `setup-project`
- [ ] Add the machine-readable sync manifest and the reference template-sync
      workflow for downstream repos
- [ ] Add `qa-gate` behavior as a stable aggregator job
- [ ] Pin all third-party actions to full-length commit SHAs
- [ ] Add dependency review to the template repo's own PR workflow
- [x] Add automated version updates for GitHub Actions and reusable workflow
      references (done via Renovate `.github/renovate.json5`, per ADR-0004;
      not Dependabot)
- [ ] Decide whether SBOM export and provenance attestations land in V1 or
      immediately after V1

Exit criteria:

- A downstream repo can call the reusable workflow and still execute its own
  synced scripts
- The template repo enforces the same standards it asks others to adopt

### Phase 3: Reference assets

- [ ] Replace `reference/pyproject.toml` with a generic baseline
- [ ] Restructure `reference/tasks.json` with region-delimited template-owned
      sections (setup, QA) and a clearly marked repo-specific region
- [ ] Replace `reference/settings.json` and `reference/extensions.json` with
      Python-generic defaults
- [x] Strip resume-specific content from `.gitignore`, `.gitattributes`, and
      workflow examples
- [ ] Remove `reference/build-resume.yml`,
      `reference/build-resumes-action.yml`, and `reference/release.yml`
- [ ] Ensure `reference/pre-commit-config.yaml` matches the chosen toolchain
- [ ] Ensure `reference/pyproject.toml` includes `--import-mode=importlib` in
      pytest config and `testpaths = ["tests"]` as recommended defaults

Exit criteria:

- The reference directory can seed a new Python repo without leaking unrelated
  project assumptions
- Every file in `reference/` is either generic or intentionally marked as
  future work

### Phase 4: Template self-validation

- [ ] Lint and format all Python scripts
- [ ] Type-check all Python scripts
- [ ] Validate reusable workflow YAML and action metadata
- [ ] Markdown-lint the documentation
- [ ] Smoke-test the scripts against a generated minimal project
- [ ] Integration-test the reusable workflow against a sample caller workflow

Exit criteria:

- `python-template` is fully dogfooding itself
- The test suite validates both local and CI execution paths

### Phase 5: Documentation and rollout

- [ ] Write a polished `README.md` with quick start, architecture, adoption
      guide, and migration guide
- [ ] Publish release notes that clearly distinguish breaking versus non-
      breaking changes
- [ ] Add workflow templates in `.github` that call the shared reusable
      workflow, including the required `.properties.json` metadata files
- [ ] Pilot the standard in `NWarila/resume`
- [ ] Pilot the standard in at least one additional Python repo with a
      different profile
- [ ] Cut `v1.0.0` and maintain the floating `v1` tag

Exit criteria:

- Two real repos have adopted the standard successfully
- The docs are good enough that a future repo can onboard without tribal
  knowledge
- The release and upgrade contract is proven

## Definition Of Done For V1

V1 is complete when all of the following are true:

- No template-owned file contains resume-specific logic or naming
- The script contract is stable and documented
- The reusable workflow runs the same downstream scripts that local developers
  run
- The template repo passes its own full QA suite
- At least two pilot repos have adopted the standard successfully
- The org has a clear rule for required checks, dependency review, and workflow
  templates
- The Python support policy is documented and avoids near-EOL interpreter
  defaults
- Sync automation is manifest-driven and reviewable
- The release contract (`v1.0.0` plus floating `v1`) is documented and used

## Risks And Mitigations

- `uv` adoption risk
  Mitigation: treat `uv` as a pilot default until two repos prove the workflow.

- `uv` plus GitHub dependency-graph visibility gap
  Mitigation: validate alerts, dependency review, and graph visibility during
  pilot; add dependency submission or compatibility artifacts if needed.

- Template drift versus repo customization
  Mitigation: keep high-conflict files reference-only until we have a safe
  merge strategy.

- CI cost and slowness
  Mitigation: separate required PR coverage from broader scheduled or
  main-branch compatibility testing.

- Strict typing friction in legacy repos
  Mitigation: allow staged adoption, but require ratcheting and visible waivers.

- Ambiguous required checks in GitHub
  Mitigation: keep job names unique and route branch protection through one
  stable `ci-passed` check.

- Ruleset capability differs by GitHub plan
  Mitigation: standardize the baseline behavior first, then implement it via
  org-wide rulesets where available and repo-level rulesets where necessary.

- Standards becoming performative instead of useful
  Mitigation: keep local setup simple, logs readable, and failure messages
  actionable.

## Design Details

### Script architecture

Each `check_*.py` and `qa.py` must be:

- **Fully standalone** — no shared module, no cross-script imports. Each script
  is independently runnable. Duplicating small helper logic (config reading,
  path resolution) across scripts is acceptable.
- **Stdlib-only** — scripts use only the Python standard library. They shell
  out to tools (`ruff`, `mypy`, `pytest`, etc.) via `subprocess`. This avoids
  polluting downstream dev dependencies with template infrastructure.

Python was chosen because a single `.py` file runs on any OS. The scripts are
thin wrappers that read config from `pyproject.toml` (via `tomllib`, stdlib
since Python 3.11), resolve paths, invoke the tool, and report results. Each
script that reads pyproject.toml does so inline — the pattern is ~10 lines
and repeating it is cleaner than importing it.

### Check dispatch in `qa.py`

`qa.py` is the local orchestrator (for VSCode tasks and command-line use). It
auto-discovers `check_*.py` scripts in its directory and runs them
sequentially. It infers which checks to run from `pyproject.toml`:

- If `[build-system]` is absent, `check_package.py` is skipped
- If `[project.scripts]` is absent, entry-point smoke tests are skipped
- CLI `--skip=<check>` overrides for ad-hoc local runs (e.g., `--skip package`)

`qa.py` is **not used in CI**. The reusable workflow runs each check as a
separate job for better Actions UI presentation.

### Coverage summary generation

`check_tests.py` needs to write a coverage table to `$GITHUB_STEP_SUMMARY`.
Since scripts are stdlib-only, the approach is:

- Run pytest with `--cov-report=json:coverage.json --cov-report=term`
- Parse `coverage.json` with stdlib `json` module
- Write a markdown summary table to `$GITHUB_STEP_SUMMARY` (only when
  `GITHUB_ACTIONS=true`)
- Clean up `coverage.json` after processing

### Pre-commit convergence model

Pre-commit hooks call tools directly (not wrapper scripts) because pre-commit
manages its own venvs per hook. `pyproject.toml` is the convergence point —
both hooks and scripts read the same `[tool.ruff]`, `[tool.mypy]`, and
`[tool.codespell]` config sections. The scripts add orchestration, summary
reporting, annotations, and `$GITHUB_STEP_SUMMARY` output that hooks don't
need.

### `ci-passed` aggregator

The `ci-passed` job lives inside the reusable `python-qa.yml` workflow, not as
a separate action. The reusable workflow owns the full contract: it runs all
check jobs and includes a final `ci-passed` job that `if: always()` evaluates
all upstream results. Downstream branch protection targets this single job name.

### Reusable workflow structure

The `python-qa.yml` reusable workflow runs each check as an **independent job**
so that every gate gets its own status icon, collapsible log section, and
pass/fail indicator in the PR checks UI. This maximizes reviewer clarity.

**Jobs in the reusable workflow:**

1. `lint` — runs `check_lint.py` across the matrix
2. `types` — runs `check_types.py` across the matrix
3. `tests` — runs `check_tests.py` across the matrix (writes coverage summary)
4. `security` — runs `check_security.py` (single OS is sufficient)
5. `spelling` — runs `check_spelling.py` (single OS is sufficient)
6. `package` — runs `check_package.py` (conditional, single OS)
7. `ci-passed` — aggregator, `if: always()`, evaluates all upstream results

Each matrix job runs setup-python independently (jobs don't share state). For
small repos this overhead is negligible and the UI benefit is worth it.

**Workflow inputs:**

| Input | Default | Purpose |
| --- | --- | --- |
| `python-min` | `"3.11"` | Minimum Python version for matrix |
| `python-max` | `"3.14"` | Maximum Python version for matrix |
| `full-os-matrix` | `true` | Whether to run all 3 OS or Ubuntu-only |
| `run-package-check` | `true` | Whether to run the packaging gate |

All quality-gate configuration (coverage threshold, strict typing, codespell
ignores) is read from the caller repo's `pyproject.toml` by the scripts at
runtime. The workflow interface stays stable even as the check contract evolves.

### Setup script and `uv` compatibility

`setup.sh` and `setup.ps1` need to handle both toolchains. The decision logic:

1. If `uv.lock` exists in the project root, use `uv`
2. Otherwise, fall back to `python -m venv` + `pip`

This is file-presence detection, not configuration — a repo that commits
`uv.lock` opts into `uv` automatically. The check scripts don't care which
path was taken; they run against the activated venv regardless.

### Sync mechanism

Sync is **pull-based**. Each downstream repo owns a `template-sync.yml`
workflow that pulls released files from `NWarila/python-template`. The template
publishes releases; downstream repos pull when ready. No cross-repo credentials,
no push permissions, no coupling.

Each downstream repo's sync workflow:

1. Checks for the latest release on `NWarila/python-template` (or accepts a
   manual tag input)
2. Clones the template at the release tag
3. Runs `scripts/sync.py` from the template clone, which reads
   `sync-manifest.json` for file mappings, copies fully-managed files, and
   runs marker-preserving merge for files like `tasks.json` (`// #region`
   markers delimit template-owned vs repo-owned sections)
4. Opens a PR via `gh pr create` using the repo's own `GITHUB_TOKEN`

`self-update.yml` supports `workflow_call`, so downstream repos call it as a
reusable workflow via `uses: NWarila/python-template/.github/workflows/self-update.yml@v1`
from a thin wrapper with their own schedule trigger.

**`sync-manifest.json` schema:**

```json
{
  "files": [
    { "src": "scripts/check_lint.py",              "dest": ".github/scripts/check_lint.py",       "mode": "overwrite" },
    { "src": "reference/pre-commit-config.yaml",   "dest": ".pre-commit-config.yaml",             "mode": "overwrite" },
    { "src": "reference/tasks.json",               "dest": ".vscode/tasks.json",                  "mode": "marker-preserve" }
  ]
}
```

### Managed-by-template file headers

Synced files carry a header comment identifying their source:

```python
# Managed by NWarila/python-template — do not edit manually.
# Source: https://github.com/NWarila/python-template
# Version: v1.2.3
```

For JSONC files (`.vscode/settings.json`, etc.), use a JSONC comment at the
top of the file in the same format.

### VSCode settings standard

The org-standard `reference/settings.json` includes only universal settings:

```jsonc
// Managed by NWarila/python-template — do not edit manually.
{
  // Python formatting
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.tabSize": 4,
    "editor.rulers": [120]
  },
  "[yaml]": { "editor.tabSize": 2 },
  "[toml]": { "editor.tabSize": 2 },

  // File hygiene
  "files.eol": "\n",
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true,

  // Search and explorer noise reduction
  "search.exclude": { "**/__pycache__": true, "**/.venv": true, "**/dist": true, "**/*.egg-info": true },
  "files.exclude": { "**/__pycache__": true, "**/*.pyc": true },

  // Python environment
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",

  // Explicit folding regions
  "explicitFolding.rules": { /* #region / //region patterns */ }
}
```

**Changes from current reference**: rulers move from 96/98 to 120 (matching
`line-length`). Resume-specific exclusions (`output/`, `data/`, etc.) are
removed — those belong in the downstream repo's own settings if needed.

### Dependency review ownership

`.github` enforces dependency review org-wide via rulesets or required
workflows. `python-template` also includes dependency review in its own
`template-ci.yml` for self-validation. These are complementary, not
conflicting — the template dogfoods what the org requires.

## Resolved Decisions

1. **`uv` becomes mandatory after pilot.** Scripts are venv-agnostic — they run
   against an activated environment regardless of how it was created. Only
   `setup.sh`/`setup.ps1` and the lock mechanism change. After two repos
   prove the `uv` workflow, it becomes the default for new repos. A documented
   fallback to `pip`+`venv` remains available.

2. **Greenfield repos default to 90% coverage.** Achievable when tests are
   written alongside code from day one, especially for the low-complexity,
   single-function repos in this portfolio. Legacy repos adopt via ratchet-up,
   never lowering the threshold after adoption.

3. **`tasks.json` uses marker-preserving sync.** Template-owned regions
   (delimited by `// #region` comments) are replaced by the sync PR.
   Repo-specific tasks live in their own regions outside the managed blocks.
   This preserves the "identical QA experience" promise while allowing
   repo-specific build tasks.

4. **Full 3-OS × min/max Python matrix on every PR.** Cross-platform-first is
   a stated principle, the repos are small enough that 6 jobs are fast, and
   the green matrix grid is a visible quality signal. Controlled by the
   reusable workflow's `full-os-matrix` input (default `true`) so repos can
   opt into a leaner matrix if needed.

5. **Renovate, not Dependabot.** Superseded by ADR-0004: Renovate is the
   org-wide standard, configured per-repo via `.github/renovate.json5`
   (`config:recommended`, `github-actions` + `pep621` managers, digest
   pinning). The earlier plan to use Dependabot — chosen for being GitHub-
   native with zero extra setup — was reversed because Renovate gives
   consistent dependency management across every repo, broader manager
   coverage, and better lockfile support. `.github/dependabot.yml` was removed
   in PR #27.

6. **CodeQL lands now, owned by `.github`.** Independent of `python-template`
   V1 — it's a workflow template in `.github`, not a python-template concern.
   Adds security tab visibility and the "Code scanning" badge immediately.

7. **`qa.py` runs checks sequentially.** Simpler output, easier to debug.

8. **Reference configs live in `reference/` directory on main branch.** A
   separate branch would be harder to discover and maintain.

9. **No `Makefile`.** `qa.py` is cross-platform, VSCode tasks cover the IDE.

10. **`.gitignore` and `.gitattributes` follow org-standard baselines aligned
    with `.github`.** In V1 they remain reference-managed rather than
    auto-synced, but every repo starts from the shared templates. The baseline
    `.gitignore` begins with `**`, and repo-specific tracked roots are added
    explicitly.

11. **Coverage summary renders in `$GITHUB_STEP_SUMMARY`.** Visible quality
    signal on every workflow run — not just pass/fail, but concrete numbers.

12. **Mypy uses `strict = true` with pinned version.** Behavior stability
    comes from the pinned mypy version in dev dependencies, not from
    enumerating individual strict flags.

13. **Pre-commit hooks call tools directly, not wrapper scripts.** `pyproject.toml`
    is the convergence point for consistent flags. Scripts add orchestration,
    annotations, and summary output that hooks don't need.

14. **Scripts are standalone and stdlib-only.** No `_common.py`, no cross-script
    imports, no third-party dependencies. Each `.py` file runs independently
    with just the Python standard library. Python was chosen because one file
    runs on any OS.

15. **The default minimum Python version for new repos is 3.11.** As of
    April 7, 2026, Python 3.10 reaches end-of-life in October 2026, so it is
    too close to retirement to be the default floor for newly created repos.

16. **Rulesets are the governance primitive.** Use organization-wide rulesets
    when the GitHub plan supports them; otherwise apply the same baseline with
    repository-level rulesets and document the fallback in `.github`.

17. **Sync automation is manifest-driven.** Source-to-destination mappings,
    ownership mode, and merge strategy live in a machine-readable manifest, not
    in workflow code.

18. **No custom `[tool.nwarila.template]` config.** Scripts infer behavior from
    standard pyproject.toml sections (`[build-system]`, `[project.scripts]`,
    `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.ruff]`). Repo admins
    control their quality bar through the tool configs they already maintain.

19. **Reusable workflow runs each check as a separate job.** `qa.py` is the
    local orchestrator only (for VSCode tasks). CI uses independent jobs per
    check for better PR reviewer experience — each gate gets its own status
    icon and collapsible log.

20. **Ruff rule set: `E`/`F`/`W`/`I`/`UP`/`B`/`S`/`SIM`/`C4`/`PT`/`T20`/`RUF`
    with `line-length = 120`.** Curated for correctness, security, modern
    idioms, and clean pytest style. `T20` prevents debug prints in library code
    (scripts are excluded). 120-char lines balance readability with modern
    displays.

21. **VSCode rulers at 120.** Matching ruff `line-length`. The previous 96/98
    rulers were resume-specific and are removed from the org standard.
22. **Sync is pull-based, not push-based.** Each downstream repo owns a thin
    workflow that calls `self-update.yml` as a reusable workflow. The template
    publishes releases; consumers pull when ready. No cross-repo credentials,
    no PATs, no push permissions. The original `sync-downstream.yml` required a
    fine-grained PAT (`TEMPLATE_SYNC_PAT`) to clone and push to private
    downstream repos, which was never configured and is bad practice for a
    personal org.
23. **PROJECT_ROOT is resolved by walking up to `pyproject.toml`, not by
    assuming `SCRIPT_DIR.parent`.** Scripts can live at `scripts/` (one level
    deep) or `.github/scripts/` (two levels deep). The old `SCRIPT_DIR.parent`
    assumption resolved to `.github/` when running from the synced location,
    breaking tool discovery and `cwd` for every subprocess call. The walk-up
    pattern traverses parent directories until it finds `pyproject.toml`,
    working from any depth. Applied to `qa.py`, `setup.sh`, and `setup.ps1`.

## Pilot Migration: `NWarila/resume`

The resume repo is the first adopter and the original motivation for this
template. Here is the concrete migration path:

### Files to delete from resume

- Repo-specific `.github/scripts/` contents — replaced by synced template-managed `.github/scripts/`
- `.github/actions/setup-python/` — replaced by the template's action or
  reusable workflow's built-in setup
- Local copies of `check_lint.py`, `check_types.py`, etc. under `.github/`

### Files to replace (via first sync PR)

| Resume file | Replaced by |
| --- | --- |
| `.github/scripts/*.py` | Synced `.github/scripts/*.py` from template |
| `.pre-commit-config.yaml` | Synced from template (generic, no `python-docx` mypy dep) |
| `.vscode/settings.json` | Synced from template (rulers at 120, no resume-specific exclusions) |
| `.vscode/extensions.json` | Synced from template |
| `.vscode/tasks.json` | Synced with marker-preserve (QA regions from template, build regions kept) |
| `.markdownlint-cli2.jsonc` | Synced from template |

### Files to rewrite

- **`.github/workflows/repo-ci.yml`** — rewrite to call the reusable
  `python-qa.yml` workflow from `python-template`. The resume-specific
  `build-resumes` job stays as a repo-owned job. Structure:

  ```yaml
  jobs:
    python-qa:
      uses: NWarila/python-template/.github/workflows/python-qa.yml@v1
      with:
        python-min: "3.11"
        python-max: "3.12"

    build-resumes:
      needs: [python-qa]
      # ... resume-specific build logic stays here ...

    # release job stays repo-owned
  ```

- **`pyproject.toml`** — update tool config sections to match org standard:
  - Ruff: add `C4`, `PT`, `T20` to `select`; update `src` paths to
    `["src", "tests"]` (remove `.github/scripts`)
  - Pytest: add `--import-mode=importlib`, update `--cov-fail-under=90`
  - Mypy: already `strict = true`, just verify `python_version`
  - Codespell: keep repo-specific `ignore-words-list`
  - Remove resume-specific `python-docx` from mypy deps (it's a runtime dep,
    not a mypy plugin)

### Files that stay unchanged (repo-owned)

- `README.md`, `LICENSE`
- `src/`, `tests/`, `data/`, `maps/`, `templates/`
- `.gitignore`, `.gitattributes` remain repo-local files after initial
  adoption, but should preserve the org-standard structure and extend only in
  repo-specific sections
- Release and build workflows (resume-specific)
- `pyproject.toml` `[project]` section (package metadata, runtime deps)

### Migration checklist

- [ ] Template V1 is released and tagged
- [ ] First sync PR is opened against resume
- [ ] Resume CI workflow is rewritten to call reusable workflow
- [ ] Resume pyproject.toml tool configs are aligned to org standard
- [ ] Resume passes the full quality gate via the reusable workflow
- [ ] Old `.github/scripts/` and `.github/actions/` are deleted
- [ ] Resume README is updated if it references old script paths

## Research Anchors

These sources directly informed the plan revision.

- PyPA `pyproject.toml` guide
  https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
  Key takeaways: keep `[build-system]` present, use `[project]` for new
  projects, and centralize tool config in `[tool.*]`.

- PyPA `src` layout discussion
  https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
  Key takeaway: `src/` helps avoid accidental imports from the repo root and
  better matches installed behavior.

- PyPA dependency groups specification
  https://packaging.python.org/en/latest/specifications/dependency-groups/
  Key takeaway: dependency groups are meant for local development needs and are
  not included in built package metadata.

- Python Developer's Guide: status of Python versions
  https://devguide.python.org/versions/
  Key takeaways: as of April 7, 2026, Python 3.10 is in security-only support
  and reaches end-of-life in October 2026; Python 3.11 remains supported until
  October 2027, making `>=3.11` the more durable floor for new repos.

- uv project and integration docs
  https://docs.astral.sh/uv/
  https://docs.astral.sh/uv/concepts/projects/dependencies/
  https://docs.astral.sh/uv/concepts/projects/sync/
  https://docs.astral.sh/uv/guides/integration/github/
  https://docs.astral.sh/uv/guides/integration/dependabot/
  https://docs.astral.sh/uv/guides/integration/renovate/
  Key takeaways: `uv` now covers project management, lockfiles, GitHub Actions,
  dependency groups, and dependency-bot integration; however, dependency-group
  ecosystem support is still uneven enough to justify a pilot before making it
  mandatory.

- Ruff formatter docs
  https://docs.astral.sh/ruff/formatter/
  Key takeaway: Ruff is intentionally a unified formatter and linter toolchain,
  which supports the goal of reducing duplicated Python tooling.

- pytest good practices
  https://docs.pytest.org/en/stable/explanation/goodpractices.html
  Key takeaways: use `pyproject.toml`, prefer `src/` layout, and use
  `--import-mode=importlib` for new projects.

- mypy command line docs
  https://mypy.readthedocs.io/en/stable/command_line.html
  Key takeaway: `--strict` enables a changing subset of optional checks, so if
  we want long-term stability we may eventually prefer explicit strict flags
  over a bare `strict = true`.

- pre-commit docs
  https://pre-commit.com/
  Key takeaways: `pre-commit run --all-files` is suitable for CI, and
  `default_install_hook_types` supports installing both `pre-commit` and
  `pre-push` hooks by default.

- GitHub Actions reusable workflow docs
  https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations
  https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
  Key takeaways: reusable workflows are centrally maintainable, preserve
  step-level logs, support multiple jobs and secrets, and run actions in the
  caller context.

- GitHub workflow-template docs
  https://docs.github.com/en/actions/how-tos/reuse-automations/create-workflow-templates
  https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations
  Key takeaways: organization workflow templates belong in the `.github`
  repository, require matching `.properties.json` metadata files, and support
  `$default-branch` placeholders.

- GitHub secure use guidance
  https://docs.github.com/en/actions/reference/security/secure-use
  Key takeaway: third-party actions should be pinned to full-length commit SHAs.

- GitHub rulesets docs
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
  Key takeaways: rulesets are available for public repositories on GitHub Free,
  organization-wide rulesets depend on plan level, and rulesets can require
  pull requests, required checks, linear history, signed commits, and code
  scanning results.

- GitHub protected-branch and dependency-review docs
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
  https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks
  https://docs.github.com/en/code-security/concepts/supply-chain-security/about-dependency-review
  Key takeaways: required job names must be unique, required checks must be
  healthy recently enough to remain selectable, and dependency review can be
  enforced at scale via rulesets.

- GitHub dependency-graph and dependency-submission docs
  https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/dependency-graph-supported-package-ecosystems
  https://docs.github.com/en/code-security/reference/supply-chain-security/automatic-dependency-submission
  Key takeaways: GitHub's dependency graph has explicit supported-ecosystem
  rules, currently lists Python support around pip and Poetry manifests rather
  than `uv.lock`, only generates GitHub Actions alerts for semantic-versioned
  refs, and can be supplemented with automatic or manual dependency submission
  when static analysis is incomplete.

- GitHub Dependabot for Actions docs
  https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot
  Key takeaway: Dependabot version updates can keep GitHub Actions and reusable
  workflow references current even when the workflow files pin specific refs.

- GitHub code-scanning and attestation docs
  https://docs.github.com/en/enterprise-cloud@latest/code-security/concepts/code-scanning/setup-types
  https://docs.github.com/en/actions/concepts/security/artifact-attestations
  Key takeaways: GitHub recommends default CodeQL setup for eligible repos, and
  reusable workflows combine well with artifact attestations for stronger
  supply-chain posture.

- pip-audit project docs
  https://github.com/pypa/pip-audit
  Key takeaways: `pip-audit` can scan local environments and lock-style inputs,
  supports machine-readable output, and remains a good baseline dependency
  vulnerability gate for Python repos.
