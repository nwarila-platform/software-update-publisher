# Template sync: two constraints that stop its pull requests merging

The `Template Sync` workflow calls the type-template's `self-update.yml`, which opens a pull
request carrying updated quality-gate scripts. Two properties of that reusable mean its pull
requests arrive in a state this repository's rules will not merge. Both need a human; neither is
a fault in the sync.

## Its pull requests trigger no checks

The reusable creates the pull request with the workflow's own `GITHUB_TOKEN`. GitHub does not
start workflow runs for events raised by that token, so a sync pull request shows no CI at all.
`main` requires passing checks, so it cannot merge as it stands.

**What to do:** close and reopen the pull request under your own account, or push an empty commit
to its branch. Either raises the event under a real identity and the checks run.

## Its commits are unsigned

The reusable commits on the runner with a plain `git commit` as the Actions bot. `main` requires
signed commits, so the branch is rejected even once checks pass.

**What to do:** check the branch out locally, re-commit the same tree with your signing key, and
force-push before merging.

## Why the sync is still worth having

It is the only mechanism that keeps `.github/scripts/` and `tools/` current with the type
template, and those files are not edited here — a local fix is silently reverted on the next
sync. The friction above is the cost of receiving those updates as a reviewable diff rather than
by hand.

A related constraint, recorded because it is silent rather than noisy: the sync runs `git add -A`
against a default-deny `.gitignore`. A new managed file that is not allowlisted is dropped with
no error. Every destination in the template's current manifest is allowlisted; a future one may
not be, and the symptom would be a file that never arrives.
