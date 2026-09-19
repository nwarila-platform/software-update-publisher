# Security Policy

## Supported versions

The protected `main` branch is the only supported version. A report should identify the exact
commit, and the release document or object key involved where one is relevant.

## Reporting a vulnerability

Report privately through this repository's GitHub Security Advisories. Do not open a public issue.

Include what you observed, how to reproduce it, and what you assess the impact to be. Expect an
acknowledgement within a few days.

## What is in scope

This repository publishes software that a fleet then installs. The consequences of a defect here
land on machines, so the following are in scope even where they look like configuration rather
than code:

- Anything that would let an artifact be published under a version it does not declare, or a
  digest that does not match its bytes.
- Anything that widens what the publishing identity can write, particularly outside the artifact
  key shapes in [`docs/reference/aws-iam/`](docs/reference/aws-iam/).
- Anything that would cause a key to be written outside the artifact namespace, since the
  consuming repository mirrors the whole bucket to its deployment share and executes helper
  scripts from it by path.
- A product module that reaches the network, the filesystem or a credential directly, rather than
  through the shared machinery it is handed.
- Weaknesses in how an upstream response is trusted, including a feed that can influence a key.

## What is not in scope

- Vulnerabilities in the software this repository publishes. Report those to their vendors.
- The deployment behaviour of the consuming repository, which has its own policy.
- Anything requiring an attacker to already hold write access to this repository or to the AWS
  account.

## What must never appear in a report or an issue

An AWS account identifier, a bucket name carrying one, a rendered IAM document, or any
credential. The reference documents in this repository substitute `<account-id>` for exactly this
reason.
