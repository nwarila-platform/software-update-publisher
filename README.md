# software-update-publisher

Watches upstream vendors for new releases of the Windows software this platform deploys,
verifies each artifact, publishes it to the application repository, and writes a release
document naming every published file with its product, version, size and SHA-256.

**Status: nothing is published yet.** What works is discovery and the upstream check: the
loader finds product modules, each one asks its vendor what the current version is, and the
MSI reader establishes what an artifact will register. Acquiring, verifying and publishing —
and the release document — are the next pieces.

## Why it exists

The software a fleet deploys has to be pinned to an exact version, and that pin has to be the
exact string Windows Add/Remove Programs reports — it is compared against installed software to
decide compliance, and interpolated into the path a deployment installs from. A pin that is
merely the vendor's marketing version does not fail loudly; it produces a collection that
matches every machine, or none.

Keeping that current by hand does not hold. The record it replaces had drifted several versions
behind on most of what it tracked, and the repository it feeds carries pins naming versions the
bucket does not contain.

## How it establishes a version

A vendor's published version and the version Windows will report are different strings, and for
most products they disagree. Rather than encode a transform per product and hope it holds, this
tool reads the identity out of the artifact it just downloaded:

| Artifact | Where the identity is declared |
| --- | --- |
| `.msi` | the `Property` table — `ProductVersion`, `ProductName`, `Manufacturer` |
| `.exe` built as a bundle | the `<Arp>` element in the bundle's own registration manifest |
| `.nupkg` | the `<version>` element in the `.nuspec` |
| `.zip`, `.cab` | nothing — these install no Add/Remove Programs entry and cannot be pinned |

Every version therefore carries how it was derived: **extracted** from the artifact, **declared**
by the vendor, or **minted** here because none exists. Only an extracted version may become a
pin automatically, because only it is a fact about the bytes that were published.

## Layout

```text
src/software_update_publisher/
├── __main__.py     python -m software_update_publisher
├── cli.py          the command line and the exit-code contract
├── loader.py       finds product modules and checks how they declare themselves
├── identity.py     reads what an artifact will register in Add/Remove Programs
├── config.py       settings, read from the environment
├── _contracts.py   the data contract between a product module and the orchestrator
├── exceptions.py   typed failures carrying What, Why and Fix
├── validators.py   the checks that protect a pin and an object key
└── products/       one folder per tracked application
```

Product modules live under `src/software_update_publisher/products/<product>/`. Adding a
tracked product means adding one of those folders; nothing outside it changes, including the
allowlist.

## Running it

```bash
bash .github/scripts/setup.sh
source .venv/bin/activate

software-update-publisher --list          # what this build tracks; contacts nothing
software-update-publisher --show-config   # resolved settings; contacts nothing
software-update-publisher --check         # ask every vendor what it is at; publishes nothing
```

A run that would publish needs `SUP_REPOSITORY_BUCKET`, which has no value in this repository
because it names an account.

A single product can be checked on its own:

```bash
python -m software_update_publisher.products.google_chrome
```

## Documentation

| Path | Holds |
|---|---|
| [`docs/reference/python-style-guide.md`](docs/reference/python-style-guide.md) | The rules this repository is written to |
| [`docs/reference/aws-iam/`](docs/reference/aws-iam/) | The identity the publisher needs, and why it is shaped that way |
| [`docs/reference/tech-debt.md`](docs/reference/tech-debt.md) | What is owed |
| [`docs/decision-records/repo/`](docs/decision-records/repo/) | Why discovery walks the filesystem, and why a version is extracted rather than transformed |

## Development

```bash
python .github/scripts/qa.py
```

That runs the same lint, type, test, security, spelling and packaging checks CI runs, from the
same scripts. Those scripts, and the tools under `tools/`, are synced from the type-template and
are not edited here — the template-sync workflow updates them by pull request.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | the run did what it set out to do; publishing nothing is a valid 0 |
| 1 | the run completed and one or more products failed |
| 2 | the run could not be performed at all |

## Licence

MIT. See [LICENSE](LICENSE).
