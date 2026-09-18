# Reference: QA contract

This template provides a Python quality gate that runs the same script surface
locally and in CI. The scripts are source-controlled, synced into downstream
repositories, and configured through ordinary `pyproject.toml` tool sections.

## Script locations

| Location | Role |
| --- | --- |
| `scripts/` | Canonical source for this template's QA scripts and sync helper. |
| `.github/scripts/` | Released copy used by this template's self-dogfooding CI and by downstream sync. |
| Downstream `.github/scripts/` | Synced copy that local developers and CI both execute. |

The two script trees in this repository should contain byte-identical copies of
every script listed in `sync-manifest.json`. The deliberate extra file in
`.github/scripts/` is `.version`, which records the release tag currently
pulled into the released-copy tree.

## Checks

| Check | Script | Primary tool | Configuration source |
| --- | --- | --- | --- |
| Lint and format | `check_lint.py` | Ruff | `[tool.ruff]` |
| Type checking | `check_types.py` | mypy | `[tool.mypy]` and `[tool.ruff].src` |
| Tests and coverage | `check_tests.py` | pytest, pytest-cov | `[tool.pytest.ini_options]` |
| Security | `check_security.py` | pip-audit | Installed environment |
| Spelling | `check_spelling.py` | codespell | `[tool.codespell]` |
| Packaging | `check_package.py` | validate-pyproject, build, twine | `[build-system]`, `[project.scripts]` |
| Orchestration | `qa.py` | Check scripts above | CLI flags and project metadata |

## Pyproject inference

| Script behavior | Inferred from | Default when absent |
| --- | --- | --- |
| Source paths for lint and types | `[tool.ruff] src` | `["src"]` |
| Test paths | `[tool.pytest.ini_options] testpaths` | `["tests"]` |
| Coverage threshold | `--cov-fail-under` in pytest addopts | 90 in the reference config |
| Strict typing | `[tool.mypy] strict` | `true` in the reference config |
| Package check | `[build-system]` exists | Skip when absent |
| Entry-point smoke tests | `[project.scripts]` | Skip when absent |
| Codespell ignores | `[tool.codespell]` | No template-specific ignore list |

## Local command

Run all checks:

```bash
python .github/scripts/qa.py
```

Run auto-fixable checks:

```bash
python .github/scripts/qa.py --fix
```

Skip one or more checks for a local diagnostic run:

```bash
python .github/scripts/qa.py --skip package --skip security
```

CI remains the source of truth; local skips are for diagnosis, not for lowering
the repository bar.

## CI contract

Downstream repositories call
`NWarila/python-template/.github/workflows/python-qa.yml@v1`. The reusable
workflow checks out the caller repository and runs the caller's synced
`.github/scripts/` files. The stable aggregate status is `ci-passed`.
