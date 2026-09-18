# Google Chrome

| | |
| --- | --- |
| Pin key | `Google-LLC_Google-Chrome` |
| Channel | **Extended Stable** |
| Artifact | `.msi`, x64 |
| Version feed | `versionhistory.googleapis.com` — `channels/extended` |
| Download | `dl.google.com/dl/chrome/install/extended/…enterprise64.msi` |
| Vendor digest | none published for this URL |

## Traps

**The channel is a decision, not an observation.** The consumer's pin `152.0.7977.76` was
released on *both* the Stable and Extended Stable trains, and no artifact distinguishes them:
the Stable, Extended and pinned MSIs share one `UpgradeCode`. Extended Stable is chosen here
deliberately — fewer version changes, at roughly eight weeks behind Stable on non-security
fixes. Stable's feed is on 154 and its download URL currently serves 153; the URL without its
`extended` segment answers 200 just the same, so getting this wrong is silent until someone
reads the version out of the file.

**The feed and the artifact disagree.** Measured 2026-09-18: the channel feed reported
`152.0.7977.134` while the MSI it serves declared `152.0.7977.130`. The feed is used to notice
change; the published pin comes from the artifact. Pinning the feed's number would name a version
no published file produces — which is exactly the defect the Firefox pin currently has.

**The MSI is not a trap, despite expectations.** Windows Installer compares only three version
fields, which led to a prediction that Chrome's four-field version could not survive in an MSI.
Measured on the artifact the fleet pins, `ProductVersion` is `152.0.7977.76` — all four fields,
byte-identical to the pin. Chrome extracts like any other MSI.

**No vendor digest.** Google publishes no checksum for this URL, so the digest is computed from
the bytes fetched and the release document records it as such rather than as vendor-attested.
