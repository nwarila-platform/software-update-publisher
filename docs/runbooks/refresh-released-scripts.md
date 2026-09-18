# Runbook: refresh released script copies

Use this runbook when `.github/scripts/` needs to be brought back in line with
the current `scripts/` source tree during template maintenance.

## Purpose

`scripts/` is the source implementation. `.github/scripts/` is the released copy
used by self-dogfooding CI. The normal path updates `.github/scripts/` through a
release and `self-update.yml`; this runbook covers manual verification or a
small repair before opening a PR.

## Prerequisites

- Work from a clean branch.
- Do not change toolchain pins as part of the refresh.
- Keep `.github/scripts/.version` as the only deliberate extra file in the
  released-copy tree.

## Procedure

1. Compare script names:

   ```powershell
   Compare-Object `
     (Get-ChildItem scripts -File | Sort-Object Name | ForEach-Object Name) `
     (Get-ChildItem .github/scripts -File |
       Where-Object Name -ne '.version' |
       Sort-Object Name |
       ForEach-Object Name)
   ```

2. Compare script content:

   ```powershell
   foreach ($file in Get-ChildItem scripts -File) {
       $copy = Join-Path '.github/scripts' $file.Name
       if ((Get-FileHash $file.FullName).Hash -ne (Get-FileHash $copy).Hash) {
           Write-Output "content drift: $($file.Name)"
       }
   }
   ```

3. If a copied script is stale, copy from `scripts/` to `.github/scripts/` and
   rerun the comparison.

4. Run validation:

   ```bash
   python scripts/qa.py
   ```

## Verification

- The comparison prints no missing files and no content drift.
- `.github/scripts/.version` still exists.
- `python scripts/qa.py` passes.

## Rollback

If the refresh copied the wrong source, restore `.github/scripts/` from the
branch base and rerun the comparison before continuing.
