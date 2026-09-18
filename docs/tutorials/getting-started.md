# Tutorial: adopt the Python QA template in a new repo

This tutorial takes a new Python repository from an empty quality-gate setup to
the same local and CI contract used by `NWarila/python-template`. Allow about 20
minutes.

## 1. Copy the starter files

From a clone of `NWarila/python-template`, copy the reference files into your
new repository:

```bash
cp reference/pyproject.toml ../your-repo/pyproject.toml
cp reference/pre-commit-config.yaml ../your-repo/.pre-commit-config.yaml
cp reference/markdownlint-cli2.jsonc ../your-repo/.markdownlint-cli2.jsonc
cp reference/repo-ci.yml ../your-repo/.github/workflows/ci.yml
cp reference/settings.json ../your-repo/.vscode/settings.json
cp reference/extensions.json ../your-repo/.vscode/extensions.json
cp reference/tasks.json ../your-repo/.vscode/tasks.json
cp reference/gitignore ../your-repo/.gitignore
cp reference/gitattributes ../your-repo/.gitattributes
```

Then customize `pyproject.toml` for the new project name, description, runtime
dependencies, and optional entry points.

## 2. Sync the managed scripts

Run the manifest-driven sync once from the template clone:

```bash
python scripts/sync.py . ../your-repo
```

This writes the managed QA scripts into `../your-repo/.github/scripts/` and
copies the managed config files listed in `sync-manifest.json`.

## 3. Add your Python package and tests

Create the normal Python project roots:

```text
src/
tests/
```

Keep importable code under `src/` and tests under `tests/`. The reference
`pyproject.toml` already points Ruff, mypy, pytest, and coverage at those paths.

## 4. Create a local environment

From the new repository root, run the setup script that was synced into
`.github/scripts/`:

```bash
bash .github/scripts/setup.sh
```

On Windows PowerShell:

```powershell
.\.github\scripts\setup.ps1
```

The setup script uses `uv` when `uv.lock` exists. Otherwise it creates `.venv`
with `pip` and installs the project with the `dev` extras from `pyproject.toml`.

## 5. Run the local quality gate

Activate the environment and run the orchestrator:

```bash
. .venv/bin/activate
python .github/scripts/qa.py
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python .github/scripts/qa.py
```

The orchestrator runs lint, packaging, security, spelling, tests, and type
checks in sequence. When all checks pass locally, open a pull request and let
the reusable workflow run the same synced scripts in CI.
