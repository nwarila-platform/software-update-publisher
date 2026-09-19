# Python style guide

The rules this repository is written to. They are derived from what it does, not imposed on it:
every rule below has at least one instance in the tree, cited so a reviewer can see the shape
rather than infer it.

A rule is **in force** unless marked **Proposed**, which means it is followed here but has not
been applied to anything else and may not survive contact with a second repository.

Structure, tooling and CI are not here. They belong to the type-template, which this repository
inherits; see `docs/decision-records/template/` for what it already decides.

## Layout

1. Importable code lives under `src/<package>/`, tests under `tests/`. The template decides this.
2. A module's name says what it is, not what it exports. `cli.py`, not `main.py` — a package that
   exports a function called `main` shadows a module of that name and makes it unreachable by
   path.
3. A leading underscore marks a module whose contents are public but whose file is internal:
   `_contracts.py`, `_version.py`. Callers import them through `__init__.py`.
4. `__init__.py` is a curated export list with an explicit alphabetised `__all__`. Nothing is
   public by accident.
5. One capability per module, and the module docstring says which: `loader.py` finds modules,
   `identity.py` reads artifacts, `validators.py` refuses bad values.

## Comments and docstrings

6. **A module docstring opens with why the file exists, not what it contains.** Compare
   `loader.py` ("Discovery is a filesystem walk rather than installed entry points… they are read
   from distribution metadata, so a contributor who clones this repository would find no products
   at all") against a bare summary line. The reasoning is the part a reader cannot recover.
7. **A comment names the failure it prevents.** `identity.py` does not say "open the file here";
   it says the library's constructor opens and then parses, so a parse failure leaves a handle no
   `finally` can reach.
8. **A measured claim carries its date and its value.** `products/google_chrome/README.md`:
   "Measured 2026-09-18: the channel feed reported `152.0.7977.134` while the MSI it serves
   declared `152.0.7977.130`." An undated claim rots silently.
9. **A guard names the realistic path that produces the state it guards.** If no such path can be
   named, the guard is speculation and comes out.
10. Do not restate the code, the signature, or a default.

## Errors

11. Every typed failure carries **What, Why and Fix**, because the reader is an operator looking
    at a failed scheduled run with no other context. See `exceptions.py`.
12. A library's own exception is translated at the boundary where it would otherwise surface
    meaningless. A message about integer digit limits tells an operator nothing about which
    artifact failed.
13. A domain error also subclasses the built-in it stands for where one fits, so existing handlers
    keep working: `DeclarationError` is also a `ValueError`.

## Contracts and validation

14. Models are frozen and reject unknown fields — `FrozenContract` sets `frozen=True` and
    `extra="forbid"`. An unknown field is a typo, not an extension point.
15. **An invariant a docstring states is enforced by a validator, or the docstring is cut back.**
    `Result` says "a value or an error, never both, and never neither" and a `model_validator`
    makes that true.
16. Validators are pure functions, called from the models — not documented as called and wired to
    nothing.
17. A closed set is a `StrEnum`, so it appears as itself in logs and reports.

## Failure behaviour

18. Exit codes are a contract: **0** did what it set out to do, **1** ran and something failed,
    **2** could not run at all. Publishing nothing is a valid 0.
19. **Never report success for work that did not happen.** A build that cannot do its job says so
    and exits 2.
20. Preflight fails once, loudly, before any per-item work. A bad credential is one message naming
    it, not forty identical failures.
21. A batch contains per-item failures and continues, but each produces a report row, a logged
    traceback and a non-zero exit. No bare `except`, nothing absorbed.
22. `SystemExit` is contained where it means a defect in this repository rather than an intent to
    exit; `KeyboardInterrupt` always propagates.

## Dependencies

23. Everything is bounded. A runtime dependency carries a major ceiling.
24. A pre-release dependency is pinned exactly **and** guarded by a test asserting its output
    against a committed real input, because a change in what it returns would be wrong data rather
    than a crash.
25. Template-owned files are not edited here. A local fix is reverted by the next sync; the change
    goes upstream.

## Tests

26. **Verify in an environment the repository describes.** Run the gate in a clean clone built by
    the setup script, never only in a development environment that may hold a hand-installed
    package.
27. No network in the default test run. An upstream response is a recorded fixture.
28. A test name is a claim in tracked content. `test_a_configured_run_refuses_rather_than_reporting_false_success`
    says what is guaranteed; `test_main_works` says nothing.
29. A property that must hold for every module is asserted once, over all of them, not copied per
    module.
30. **Proposed.** Tests are grouped in `TestX` classes by behaviour, with sentence-style method
    names.

## Security

31. No account identifier, bucket name carrying one, credential or rendered IAM document in
    tracked content. Reference documents substitute `<account-id>`.
32. A value that becomes a path or a key is validated before it is used, even when it came from a
    vendor the run has already trusted.
33. **This tool publishes artifacts and nothing else.** It never writes anything the fleet
    executes -- helper scripts belong to the repository that deploys them. The publishing
    identity denies that prefix outright rather than relying on the code to stay well behaved.
34. **Proposed.** A module is handed the machinery it needs — an HTTP client, a hasher, a
    publisher — and opens nothing itself. Timeout and transport policy live in one place.
