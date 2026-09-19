# Technical debt

Known, deliberate, and not yet paid. Each entry records what is owed and what closing it looks
like, so the list is auditable rather than remembered.

The exemplar keeps its register at the documentation root. This repository cannot: its docs-layout
gate admits Markdown only inside the Diataxis subtrees, so the register is reference material here.

## TD-001 — The publishing workflow does not exist

**Recorded** 2026-09-18.
**Issue.** `docs/reference/aws-iam/` proposes a role whose trust pins
`.github/workflows/publish.yml`, and no such workflow exists.
**Why it is debt.** A trust whose consumer is absent is a silent lockout, and the hasty fix when
the first run fails is to edit the trust rather than the workflow.
**Correction.** Author `publish.yml` and apply the IAM in the same change.
**Exit criteria.** The workflow exists on `main`, the role is applied, and a dispatched run
assumes it successfully.

## TD-002 — Nothing is acquired, verified or published yet

**Recorded** 2026-09-18.
**Issue.** `--check` asks vendors what they are at. Acquiring the artifact, verifying its digest,
extracting its identity, writing it to the bucket and emitting the release document are all
unimplemented. `main` exits 2 rather than claiming otherwise.
**Why it is debt.** The repository's stated purpose is unmet until this lands, and the consuming
repository still carries pins naming versions the bucket does not hold.
**Correction.** Implement the acquire, verify, publish and report stages.
**Exit criteria.** A run publishes one artifact under a create-only key and emits a release
document describing it.

## TD-003 — The repository declaration has no required checks

**Recorded** 2026-09-18.
**Issue.** `github-terraform-runner/terraform/public/software-update-publisher.yml` omits
`required_checks`, with a comment saying they follow once a first run has reported each context.
Runs have now reported `ci-passed`, `Governance gates`, `repo-hygiene / verify`, `CodeQL` and the
Python QA matrix.
**Why it is debt.** The stated precondition is met, so the omission is now just an omission: the
branch ruleset requires nothing, and a red build does not block a merge.
**Correction.** Declare the contexts in that repository.
**Exit criteria.** A pull request with a failing check cannot be merged without an admin bypass.

## TD-004 — A version is extracted; nothing yet carries both versions

**Recorded** 2026-09-18.
**Issue.** `VersionFacts` — the model pairing the vendor's advertised version with the one Add and
Remove Programs will report, and recording which derivation produced the pin — was written and
then withdrawn, because nothing produces one until the orchestrator exists.
**Why it is debt.** The distinction is the repository's central idea and is currently enforced by
convention in `identity.py` rather than by a type.
**Correction.** Reintroduce it with the orchestrator that emits it, and test its validator.
**Exit criteria.** The release document is generated from that model rather than assembled by hand.

## TD-005 — The module template exists as five files, not as a document

**Recorded** 2026-09-18.
**Issue.** `.gitignore` allowlists "the files the module template defines" and no document defines
them. The only instance is `products/google_chrome/`.
**Why it is debt.** Adding the second product means copying the first and guessing which parts
were incidental.
**Correction.** Write the module template as a page under `docs/how-to/`, or generate it with a
scaffolding command once three products have proven the shape.
**Exit criteria.** A contributor can add a product without reading an existing module.

## TD-006 — The retention window is not yet stated in the release document

**Recorded** 2026-09-18.
**Issue.** Retention is a contract consumers depend on — the window is what they can rely on being
able to fetch — and the release document does not yet publish it.
**Why it is debt.** A consumer cannot tell how long it may go without reconciling. The window is
knowable only by reading this repository, which defeats the point of a document consumers poll.
**Correction.** Emit each product's `keep_versions` and `keep_days` in the release document.
**Exit criteria.** A consumer can determine the window from the document alone.

## TD-007 — No consumer has been told the window exists

**Recorded** 2026-09-18.
**Issue.** Several repositories will poll this document — the deployment repository for Windows
software, the image builders for the inputs they manage. None has been told that artifacts outside
the window are removed.
**Why it is debt.** Pruning is irreversible on this bucket, and a consumer that mirrors this
repository deterministically propagates the removal to its own machines. The first consumer to
discover the window by losing an artifact discovers it in the worst way, on every host at once.
**Correction.** State the window in the document and in this repository's README before the first
prune runs.
**Exit criteria.** Pruning is enabled only after the window is published and the consumers that
poll it have been told.
