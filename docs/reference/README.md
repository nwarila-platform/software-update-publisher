# Reference

What this repository depends on but does not create. The publisher writes artifacts and a
catalogue; it does not provision the identity it runs as. That is applied by an operator and must
exist before a publishing run can succeed, so it is recorded here.

| Path | Holds |
|---|---|
| [`aws-iam/`](aws-iam/) | The role and policy the publisher runs with |
| [`template-sync-constraints.md`](template-sync-constraints.md) | Why the template-sync workflow's pull requests need a human before they can merge |
