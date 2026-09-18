# Explanation: why two-layer pull sync

This template is one layer in a larger organization standard. `NWarila/.github`
owns organization-wide governance, while `NWarila/python-template` owns the
Python-specific quality gate. Downstream repositories keep their own product
code, metadata, release workflows, and repo-specific docs.

## The two layers

The org layer provides baseline policy: community health files, org ADRs,
repo-hygiene checks, workflow templates, and non-language-specific automation.
Those files should be identical only when they are truly shared governance.

The Python-template layer provides the Python developer experience: QA scripts,
the reusable Python CI workflow, setup scripts, sync metadata, and starter
configuration. These are stack-specific, so they live in this repository rather
than in the org control plane.

## Why downstream repos pull

Push-based sync would require this template to hold write credentials for every
consumer repository. That makes the template a deployment authority and turns a
standards repo into a cross-repo control point.

Pull-based sync keeps ownership where it belongs. Each downstream repo owns a
thin workflow that calls this template's `self-update.yml`, receives a normal PR
with the synced files, reviews the change, and merges on its own cadence.

## Why the scripts are copied

Local development and CI should execute the same files. If CI called hidden
template logic while developers ran local copies, drift would be inevitable.
Copying `.github/scripts/` into each downstream repo makes the contract visible:
the local command, VSCode tasks, pre-commit hooks, and reusable workflow all
converge on the same script surface.

## Why the manifest matters

`sync-manifest.json` is the reviewable map of what the template owns. It keeps
source paths, destination paths, and merge modes out of workflow shell logic.
That makes sync changes auditable: adding a managed file, changing a target, or
switching a file from full overwrite to marker-preserving merge is a normal
diff in one machine-readable place.

## How this repo dogfoods the model

`scripts/` is the source implementation. `.github/scripts/` is the released
copy. This template's CI runs the released copy so the repo continuously tests
the same artifact shape downstream consumers receive.

The flow is recorded in
[docs/diagrams/qa-template-sync-flow.mmd](../diagrams/qa-template-sync-flow.mmd).
