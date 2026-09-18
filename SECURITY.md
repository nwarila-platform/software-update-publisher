# Security Policy

## Reporting a vulnerability

**Do not file public issues for security vulnerabilities.**

### Preferred: GitHub private vulnerability reporting

Use [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) to report vulnerabilities directly through the affected repository's Security tab.

### Fallback contact

If private vulnerability reporting is not available on the affected repository, contact the maintainer through their [GitHub profile](https://github.com/NWarila).

## What to include

- Description of the vulnerability
- Steps to reproduce or proof of concept
- Affected repository and version (or "latest default branch" if unsure)
- Potential impact

## Response timeline

| Stage | Target |
|-------|--------|
| Initial acknowledgement | 7 business days |
| Validation | 14 days |
| Remediation or mitigation | 90 days when reasonable |

These are targets, not guarantees. Complex issues may take longer. You will be kept informed of progress.

## Supported versions

Only the latest release of `python-template` is supported. Downstream repositories that pin an older release tag should upgrade to receive fixes. The `v1` floating tag always resolves to the current supported release.

## Scope

### In scope

- Vulnerabilities in scripts, workflows, or reference configurations maintained in this repository
- Misconfigurations in GitHub Actions workflows that could lead to secret exposure or privilege escalation
- Supply-chain weaknesses introduced by synced files that propagate to downstream repositories

### Out of scope

- Vulnerabilities in third-party tools (`ruff`, `mypy`, `pytest`, `pip-audit`, etc.) — report those to the respective upstream projects
- Social engineering attacks
- Denial of service attacks
- Issues in archived repositories

## Coordinated disclosure

We follow coordinated disclosure practices. We ask that you:

- Give us reasonable time to investigate and address the issue before public disclosure
- Act in good faith and avoid accessing or modifying data that does not belong to you
- Do not exploit the vulnerability beyond what is necessary to demonstrate it

We will credit researchers who report valid vulnerabilities unless they prefer to remain anonymous.
