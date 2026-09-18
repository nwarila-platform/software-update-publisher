# ADR-0002: Extract Identity From The Artifact

| Field            | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| ID               | ADR-0002                                                                     |
| Scope            | Repo                                                                         |
| Status           | Accepted                                                                     |
| Decision-subject | A published pin is read out of the artifact, never transformed from a vendor's version. |
| Date accepted    | 2026-09-18                                                                   |
| Date             | 2026-09-18                                                                   |
| Last reviewed    | 2026-09-18                                                                   |
| Authors          | Nick Warila (@NWarila)                                                       |
| Decision-makers  | Nick Warila (sole portfolio maintainer)                                      |
| Consulted        | Windows Installer `ProductVersion` and uninstall-registry-key documentation; measurements against tracked artifacts. |
| Informed         | Maintainers of the consuming deployment repository.                          |
| Reversibility    | Medium                                                                       |
| Review-by        | 2027-09-18                                                                   |

## TL;DR

The version this repository publishes is read out of the downloaded artifact, not derived from what the vendor advertises. A vendor's number is recorded for change detection and for the audit trail, and never becomes an object key or a pin.

## Context and Problem Statement

The consuming deployment repository pins each application to an exact version string. That string does two jobs: it is compared against what Add/Remove Programs reports on a machine, and it is interpolated into the path a deployment installs from. A wrong value does not raise; it produces a compliance collection that matches everything or nothing, and a package that fails only at deploy time.

Vendors advertise a version on a page or a feed. Windows reports a different one often enough that the relationship cannot be assumed.

## Decision Drivers

1. A pin must be the string a machine will actually report.
2. A wrong pin is silent, so the mechanism must not depend on a rule someone maintains.
3. The artifact is downloaded anyway, so reading it costs no extra fetch.
4. Where no honest version exists, the repository must say so rather than invent one.

## Considered Options

1. Extract the identity from the downloaded artifact.
2. Declare a per-product transform from the vendor's version.
3. Use the vendor's version directly.
4. Measure the version once on an installed machine and record it.

## Decision Outcome

Chosen option: **1, extract the identity from the downloaded artifact.**

An extracted version cannot drift from what the machine will report, because it is what the machine will report: for an MSI, Add/Remove Programs takes `DisplayVersion` from the `ProductVersion` property the package declares.

Measurement decided this rather than preference. The AWS command-line installer declares `2.36.31.0` while every vendor page advertises `2.36.29`, so the obvious transform is wrong and the artifact is ahead of its own documentation. Google Chrome's channel feed reported `152.0.7977.134` while the artifact that feed points at declared `152.0.7977.130`, so pinning the feed would have named a version no published file produces. The consuming repository already carries that defect for another product, where the pin names a version the repository does not hold.

Option 2 is retained only as a cross-check: where a transform is declared, it is asserted against the extracted value, which turns it from an assumption into a continuously tested claim. Option 3 is rejected outright. Option 4 remains the only route for artifacts whose registration cannot be read before installation, and such a product carries no generated pin until someone records a measurement.

## Pros and Cons of the Options

### Option 1: Extract from the artifact

- Good, because the value is a fact about the bytes that were published.
- Good, because it costs no fetch the run was not already making.
- Bad, because it requires a reader per artifact format.
- Bad, because formats that register nothing have no identity to read.

### Option 2: Declared transform

- Good, because the version is known before downloading.
- Bad, because it can look obvious and be wrong, silently.

### Option 3: Vendor version directly

- Good, because it is free.
- Bad, because it is a claim about a release, not about what Windows will report.

### Option 4: Measure on an installed machine

- Good, because it is ground truth.
- Bad, because it needs a machine and a human, per version.

## Confirmation

`tests/test_identity.py` asserts the exact identity fields a committed real artifact declares, so a change in the reader's output fails the build. `src/software_update_publisher/_contracts.py` records which derivation produced a value, and refuses a pin for anything minted.

## Consequences

Each artifact class needs a reader, and the set of classes is closed. An artifact that registers nothing carries no pin and is not eligible for a compliance collection. A vendor's version is still fetched and recorded, because it is what makes "something changed" cheap to notice.

## Assumptions

An artifact's declared registration is what Windows writes. That holds for a standard package and is documented; a package that rewrites its own registration at install time would defeat it, and would require a measurement on a real machine to detect.

## Supersedes

None.

## Superseded by

None.

## Implementing PRs

- `feat: load product modules dynamically, and track Google Chrome`

## Related ADRs

- [ADR-0001](0001-discover-product-modules-from-the-filesystem.md)

## Compliance Notes

None.

## Changelog

| Date | Version | Change | Author | Notes |
| ---- | ------- | ------ | ------ | ----- |
| 2026-09-18 | 1.0 | Accepted | Nick Warila | Recorded with the identity reader it describes. |
