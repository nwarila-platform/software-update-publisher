# AWS IAM reference

The IAM this repository needs in order to publish. **Proposed, not yet applied** —
[`manifest.json`](manifest.json) records that, and carries a null `exported` date to say so. Once
an operator applies these, export the documents from the live account and record the policy
versions, rather than maintaining these by hand: the consuming repository has already had two
hand-maintained IAM copies drift apart, one scoped to a repository id that no longer existed.

The account id is the only substitution, written as `<account-id>`.

Terraform does not manage any of this. Nothing in this repository can apply it.

## Roles

| Role | Trusted by | Attached policies | Does |
|---|---|---|---|
| `nwarila-platform_software-update-publisher_publisher` | GitHub OIDC: `publish.yml` on `main` | `…_publisher_s3` | Publish verified artifacts and the catalogue to the application repository |

One role, one policy, no inline policies. The repository's other workflows — the quality gate, the
security scans, the template sync — reach no cloud account and get no identity.

## What the trust allows

Modelled on the consuming repository's runner trust, which is the ratified shape in this account.
It requires all of: the `sts.amazonaws.com` audience, this repository's id (`1376311697`), the
`refs/heads/main` ref, one of the two `sub` forms GitHub issues for it, and a `job_workflow_ref`
naming `publish.yml` specifically.

The `job_workflow_ref` condition is the one that matters most here. Without it, any workflow in
this repository could assume a role that writes to the artifact bucket — including one added by a
pull request. With it, a pull request's quality-gate run cannot acquire write authority no matter
what it contains.

## What the policy allows, and what it deliberately does not

The bucket has **versioning disabled** and no lifecycle rule, confirmed against the live account.
An overwrite is therefore final: there is no previous version to restore and no delete marker to
remove. The policy is built around that single fact.

| Sid | Grants | Bounded by |
|---|---|---|
| `CreateNewArtifactsOnlyNeverOverwrite` | `s3:PutObject` across the bucket | `Null: {"s3:if-none-match": "false"}` — the header must be present, so **every artifact write is create-only at the authorization layer** |
| `RewriteOnlyTheCatalogIndex` | `s3:PutObject` on exactly two keys | The catalogue index and its rendering, which carry no bytes anyone deploys |
| `ReadBackWhatWasJustWritten` | `s3:GetObject` | Verifying an upload against S3 rather than against a 200 response |
| `InventoryTheRepositoryToBuildTheCatalog` | `s3:ListBucket`, `s3:GetBucketLocation` | Knowing what the repository already holds |
| `AbortAStalledMultipartUpload` | `s3:AbortMultipartUpload` | Cleaning up after a failed transfer |

Every statement is `Allow`; none is `Deny`. Every one is conditioned on `aws:ResourceAccount`, so
none of it reaches a bucket in another account.

**No delete permission of any kind.** Not `s3:DeleteObject`, not `s3:DeleteObjectVersion`. A
superseded installer stays addressable for rollback, and the publisher cannot remove one even by
mistake. Deleting an artifact remains a deliberate human action outside this identity.

**No bucket configuration permission.** The publisher cannot change versioning, policy, encryption
or lifecycle.

### Two grants that are broader than they look, stated plainly

**`s3:PutObject` on `/*`** is a bucket-wide write grant. It is not avoidable while adding a tracked
product means adding a folder: a per-vendor resource list would turn every new product into an IAM
change and a separate approval. The `s3:if-none-match` condition removes the failure a wildcard
actually threatens — a bug that recomputes a key it already wrote gets `412 Precondition Failed`
rather than destroying a good installer on a bucket that cannot recover it. The condition key is
documented by AWS for exactly this purpose.

What it still permits is *adding* an object anywhere in the bucket. The controls on that are the
`job_workflow_ref` trust condition, branch protection on `main`, and the fact that a new object
changes nothing until a human pins it.

**`s3:ListBucket` is unprefixed**, which the account's ratified model otherwise withholds from
machine identities. The publisher's job is to know what the repository already holds, so it needs
the whole listing. The bucket carries no secret. This is a documented deviation, not an oversight.

### Single-part uploads, and why the policy says nothing about multipart

Artifacts are uploaded with a single `PutObject` carrying a SHA-256, so S3 stores a full-object
checksum that is comparable to what the consuming deployment verifies on the target. A multipart
upload would store a checksum of checksums instead, which is not the same value. The largest
tracked artifact is well inside the single-request limit.

If an artifact ever exceeds it, `s3:ObjectCreationOperation` becomes necessary to exempt the
multipart sub-operations from the `if-none-match` requirement, and the comparability of the stored
checksum has to be reconsidered at the same time.

## What is NOT here, and needs a decision elsewhere

- **Reading the catalogue through the console.** An operator browsing `_catalog/` would need two
  prefixes added to the existing `…_pdq-deploy-inventory_admin_s3` policy's `s3:prefix` list. That
  is a change to another repository's IAM and is not proposed here.
- **Nothing in this repository reads the deployment-material bucket.** Licences, secrets and
  certificates live elsewhere and the publisher has no reason to reach them.
