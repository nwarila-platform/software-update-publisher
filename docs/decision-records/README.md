# Decision Records

This index separates inherited organization decisions, Python-template
decisions, and repository-local decisions. Org records are byte-identical
mirrors from `NWarila/.github`; template records are owned by this repository.

## Org-Mirrored ADRs

| ADR | Status | Summary |
| --- | --- | --- |
| [ADR-0001](org/0001-use-architecture-decision-records.md) | Accepted | Use ADRs to document design rationale. |
| [ADR-0002](org/0002-adopt-diataxis-documentation-framework.md) | Accepted | Organize non-ADR docs with Diataxis. |
| [ADR-0003](org/0003-use-deny-all-gitignore-strategy.md) | Accepted | Use deny-all `.gitignore` baselines. |
| [ADR-0004](org/0004-use-renovate-for-dependency-updates.md) | Accepted | Use Renovate for dependency updates. |
| [ADR-0005](org/0005-pin-terraform-and-provider-versions-exactly.md) | Accepted | Pin Terraform and provider versions exactly. |
| [ADR-0006](org/0006-keep-github-control-planes-namespace-local.md) | Accepted | Keep GitHub control planes namespace-local. |
| [ADR-0007](org/0007-centralize-universal-ci-reusables-within-each-namespace.md) | Accepted | Centralize universal CI reusables per namespace. |
| [ADR-0008](org/0008-enforce-repo-hygiene-by-repo-type.md) | Accepted | Enforce repo hygiene according to repository type. |
| [ADR-0009](org/0009-classify-baseline-manifest-byte-identity.md) | Accepted | Use byte identity only for true shared baselines. |
| [ADR-0010](org/0010-keep-ai-attribution-out-of-version-control.md) | Accepted | Keep tool attribution residue out of version control. |

## Template ADRs

| ADR | Status | Summary |
| --- | --- | --- |
| [ADR-0001](template/0001-scripts-are-standalone-and-stdlib-only.md) | Accepted | Keep QA scripts standalone and stdlib-only. |
| [ADR-0002](template/0002-pull-based-manifest-driven-template-sync.md) | Accepted | Sync template updates through pull-based manifest PRs. |

## Repo ADRs

No repository-specific ADRs yet.
