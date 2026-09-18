# Test fixtures

`7-zip-26.02.00.0-x64.msi` is a real tracked artifact, taken from the application repository. It
is committed, at 2 MB, for one reason: the MSI identity reader depends on a library pinned at a
pre-release version, and a silent change in what that library returns would produce a wrong pin
rather than a crash. The conformance test asserts the exact identity fields this file
declares, so such a change fails the build instead of reaching a console.

It is the smallest real MSI among the tracked products. Its declared identity is:

| Property | Value |
| --- | --- |
| `ProductVersion` | `26.02.00.0` |
| `ProductName` | `7-Zip 26.02 (x64 edition)` |
| `Manufacturer` | `Igor Pavlov` |
| `ProductCode` | `{23170F69-40C1-2702-2602-000001000000}` |
| `UpgradeCode` | `{23170F69-40C1-2702-0000-000004000000}` |

Note that `ProductName` is not the product's pin key: the consumer spells it `Igor-Pavlov_7-Zip`.
The version is extractable; the name is not, which is why a module declares its own identity and
only extracts its version.
