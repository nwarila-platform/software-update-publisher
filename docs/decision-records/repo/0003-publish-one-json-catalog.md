# ADR-0003: Publish One JSON Catalog

| Field            | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| ID               | ADR-0003                                                                     |
| Scope            | Repo                                                                         |
| Status           | Accepted                                                                     |
| Decision-subject | One catalog file, in JSON, is the interface every consumer depends on.       |
| Date accepted    | 2026-09-18                                                                   |
| Date             | 2026-09-18                                                                   |
| Last reviewed    | 2026-09-18                                                                   |
| Authors          | Nick Warila (@NWarila)                                                       |
| Decision-makers  | Nick Warila (sole portfolio maintainer)                                      |
| Consulted        | Native parser availability measured on the fleet's PowerShell; existing parser usage across the consuming repositories. |
| Informed         | Every repository that polls the catalog.                                     |
| Reversibility    | Hard                                                                         |
| Review-by        | 2027-09-18                                                                   |

## TL;DR

One catalog file, JSON, normative. Any other rendering is generated from it in the same run and is
explicitly not authoritative. JSON is chosen because it is the only format every consumer parses
with no added dependency.

## Context and Problem Statement

This repository publishes artifacts and announces what it published. Consumers poll that
announcement and reconcile themselves; nothing here reaches into them. The catalog is therefore
the entire interface, and it is consumed by workloads that share no runtime: a Windows deployment
system driving PowerShell on target machines, an Ansible controller, image builders managing
inputs on a hypervisor, and whatever arrives next.

A format that any one of them cannot read without installing something first is a format that
makes reading the catalog a deployment problem.

## Decision Drivers

1. Every consumer must parse it with nothing installed.
2. One file, so a consumer discovers everything from one fetch.
3. The schema is depended on by repositories this one does not control, so it must be versioned
   and changed deliberately.
4. Two artifacts that can disagree are worse than one that is merely inconvenient.

## Considered Options

1. JSON, normative, with optional generated renderings.
2. YAML.
3. XML.
4. A set of formats, each normative.

## Decision Outcome

Chosen option: **1, JSON, normative.**

Measured on the fleet's own runtime rather than assumed: PowerShell 7.6.5 has `ConvertFrom-Json`
natively and has no `ConvertFrom-Yaml` at all. Windows PowerShell 5.1 on target machines is the
same. Reading a YAML catalog would mean installing a parser module on every machine that reads it,
which turns the announcement into something that must itself be deployed.

The consuming fleet has already chosen: 56 uses of `ConvertFrom-Json` across its PowerShell, and
no YAML anywhere. Ansible (`from_json`), Terraform (`jsondecode`), `jq` and Python all parse JSON
natively as well.

XML is natively available in PowerShell via the `[xml]` accelerator, but it is the most awkward of
the three everywhere else, and its verbosity buys nothing here.

**On publishing several formats at once:** rejected as a set of normative documents, because
formats that can disagree eventually do, and a consumer cannot tell which one was right. A
human-readable rendering is still worth having — but it is generated from the same in-memory
structure in the same run, and it is labelled as a view. If a future consumer genuinely cannot
read JSON, a converted form can be published then, derived rather than authored.

## Pros and Cons of the Options

### Option 1: JSON, normative

- Good, because every current consumer parses it with nothing installed.
- Good, because it is already the fleet's idiom.
- Neutral, because it is unpleasant to read by eye, which the generated rendering answers.
- Bad, because it cannot carry comments, so anything explanatory must be a field.

### Option 2: YAML

- Good, because it is comfortable to read and write by hand.
- Bad, because the fleet's PowerShell cannot parse it without a module on every machine.
- Bad, because nothing authors this file by hand anyway.

### Option 3: XML

- Good, because PowerShell reads it natively.
- Bad, because it is awkward in every other consumer.

### Option 4: Several normative formats

- Good, because no consumer is ever inconvenienced.
- Bad, because they can disagree, and nothing says which is right.
- Bad, because every schema change must land in all of them at once.

## Confirmation

Parser availability was measured, not assumed: `Get-Command ConvertFrom-Yaml` on PowerShell 7.6.5
returns nothing. Existing usage was counted across the consuming repositories.

## Consequences

The catalog carries a schema version, and a consumer reading a version it does not recognise fails
loudly rather than interpreting the fields it happens to know. Changing the schema is a change to
an interface several repositories depend on, so it is a deliberate, versioned act.

Explanatory text lives in named fields rather than comments.

## Assumptions

Consumers can fetch one file over HTTPS or read it from the object store. Nothing assumes a shared
runtime, a shared library, or any coordination between consumers.

## Supersedes

None.

## Superseded by

None.

## Implementing PRs

- Pending: the catalog emitter.

## Related ADRs

- [ADR-0002](0002-extract-identity-from-the-artifact.md)

## Compliance Notes

None.

## Changelog

| Date | Version | Change | Author | Notes |
| ---- | ------- | ------ | ------ | ----- |
| 2026-09-18 | 1.0 | Accepted | Nick Warila | One catalog, JSON, with generated renderings non-normative. |
