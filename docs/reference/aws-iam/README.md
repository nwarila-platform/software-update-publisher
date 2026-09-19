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

The bucket has **versioning disabled** and no lifecycle rule, read from the live account on
2026-09-18. An overwrite is therefore final: no previous version to restore, no delete marker to
remove. Worse, **no identity in this account can delete from this bucket** — the runner, reaper,
admin and instance roles all evaluate to an implicit deny for `s3:DeleteObject`, confirmed by
policy simulation. Wrong bytes written to a right key are permanent short of a break-glass
administrator. Both facts shape everything below.

| Sid | Grants | Bounded by |
|---|---|---|
| `CreateNewArtifactsOnlyNeverOverwrite` | `s3:PutObject` | Create-only, `STANDARD` storage class, and a resource list that admits **only** an artifact-shaped key: at least three path segments and a known artifact extension |
| `CreateNewReleaseDocumentsOnlyNeverOverwrite` | `s3:PutObject` | The same, for the immutable per-run release documents |
| `RewriteOnlyTheCatalogIndex` | `s3:PutObject` on exactly two keys | The catalogue index and its rendering, which carry no bytes anyone deploys. Deliberately overwritable, deliberately outside the create-only rule |
| `RefuseTheDeploymentScriptPrefixWhateverElseIsAllowed` | **Deny** `s3:PutObject` on `~resources/*` | See below — this is the statement that matters most |
| `ReadBackWhatWasJustWritten` | `s3:GetObject` | The same artifact shapes, plus the catalogue. Not the whole bucket |
| `InventoryTheRepositoryToBuildTheCatalog` | `s3:ListBucket` | Knowing what the repository already holds |

Every statement is conditioned on `aws:ResourceAccount`, so none of it reaches another account.

### The deny, and why the first draft of this policy was dangerous

The first version of this policy granted `s3:PutObject` across the whole bucket, create-only, and
argued that was safe because "a new object changes nothing until a human pins it."

**That argument was false, and the counter-example is already merged in the consuming repository.**
Its package definitions execute helper scripts by path:

```xml
<Files>$(Repository)\~resources\Start-Uninstaller.ps1</Files>
```

`Set-RepositoryContent.ps1` mirrors the **entire** bucket to the repository volume with no prefix
filter and never deletes. Neither of those keys exists in the bucket yet. So a compromised
publishing run could create `~resources/Start-Uninstaller.ps1` — a new key, so create-only permits
it — the next sync would carry it to the share, and every subsequent deployment would execute it
on every target, under the deploy credential. No pin change, no pull request, no reviewer.

Two things close it. The resource list admits only keys three segments deep ending in an artifact
extension, so no script extension at any depth is writable. And the explicit `Deny` on
`~resources/*` survives any later widening of that list, which is the realistic way this would
come back.

This is the one `Deny` in the document. The ratified model elsewhere in this account is
Allow-only; the deviation is deliberate, because the prefix it protects is the one the fleet
executes from.

### Why a resource list rather than a bucket wildcard

Because the earlier argument — that narrowing the resource would make every new product an IAM
change — was a false choice. Vendors and products vary; **artifact kinds do not**. Bounding the
resource by path depth and extension keeps "adding a product is adding a folder" exactly as true
as a bucket wildcard did, and admits nothing else.

That is also the established idiom here: the live `…_admin_s3` policy publishes to
`PDQ.com/*/*.exe`, not to the bucket.

### What is deliberately absent

**No delete permission of any kind.** A superseded installer stays addressable for rollback.

**No bucket configuration permission.**

**No multipart permission, and none is needed.** The vendor's own enforcement documentation states
that `CreateMultipartUpload`, `UploadPart` and `UploadPartCopy` cannot carry a conditional header,
so a policy requiring `s3:if-none-match` denies them outright unless `s3:ObjectCreationOperation`
exempts them. It is not exempted, so multipart is closed and an abort grant would be dead. The
earlier draft carried one; it has been removed.

**This has a consequence the implementation must respect.** The client must call `put_object`
with `IfNoneMatch='*'`, never the transfer manager's `upload_file`, which switches to multipart
above 8 MB by default — and most tracked artifacts are far larger. A `403` on
`CreateMultipartUpload` is a defect in the client, not a policy that is too narrow. Widening the
policy to make that error go away would destroy the whole design.

**A storage-class bound**, because an artifact written to an archive tier makes the mirror throw
on every subsequent run, and no identity here can delete the object that causes it.

### Two honest notes on scope

`s3:ListBucket` is unprefixed. The publisher's job is to know what the repository holds, so it
needs the whole listing. The account's instance role `nwarila-apprepo-read` already lists this
bucket unprefixed, so this is consistent with the live model rather than a deviation from it — an
earlier draft of this file claimed otherwise and was wrong.

`s3:GetObject` is bounded to artifact shapes and the catalogue rather than the bucket. This bucket
has twice held a misfiled password file, recorded in the consuming repository's IAM derivation
log. None is present today; the grant should not depend on that staying true.

## What IAM cannot do here

The mirror trusts every key name it finds. A key containing characters Windows rejects in a path,
or one nested under an existing object's key, breaks the sync for the whole fleet — and cannot be
deleted. Product names come from vendors, so **the publisher must validate every composed key**
before writing it. No policy can express that.

Equally, the on-target digest check proves the artifact matches its pin; it does not prove the
vendor. Signature verification at publish time is the only independent check, and it is not IAM.

## Before this is applied

1. **`.github/workflows/publish.yml` does not exist yet.** The trust names it, and a trust whose
   consumer is absent is a silent lockout. Apply this in the same change that adds the workflow.
2. If that workflow ever delegates its job to a reusable workflow, `job_workflow_ref` becomes the
   *reusable*'s path and this trust stops matching. If it ever gains an `environment:`, the `sub`
   claim changes shape and stops matching too. Both are silent.
3. The consuming repository will need its own grant to publish helper scripts under `~resources/`.
   That grant and this policy's deny must be designed together, or two writers collide on a prefix
   no identity here can repair.
4. Decide which identity may remediate a bad object, because today none can.

## What is NOT here

- **Console access to the catalogue.** An operator can already read `_catalog/index.json` by exact
  key under the existing admin role; only *listing* that prefix is denied. Convenience, not a gap.
- **Nothing reads the deployment-material bucket.** Licences, secrets and certificates live there
  and the publisher has no reason to reach them.
