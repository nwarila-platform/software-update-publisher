# How-to: add a QA check script

Goal: add a new `check_*.py` gate without breaking the local/CI contract.

1. **Create the source script.** Add a standalone file under `scripts/`:

   ```text
   scripts/check_example.py
   ```

   Keep it stdlib-only. Duplicate small helpers locally instead of importing
   from another check script.

2. **Give it a clear CLI.** Follow the existing shape:

   - parse arguments with `argparse`
   - read standard `pyproject.toml` sections when configuration is needed
   - shell out to the underlying tool with `subprocess`
   - return `0` on pass and nonzero on failure
   - print a GitHub Actions annotation when `GITHUB_ACTIONS=true`

3. **Add tests.** Cover the script in `tests/`, mocking subprocess calls so the
   tests exercise orchestration logic without requiring the external tool to
   fail on purpose.

4. **Wire local discovery.** `scripts/qa.py` discovers `check_*.py` files in its
   own directory. A new source script will be picked up automatically when
   `python scripts/qa.py` runs from this repository.

5. **Add sync metadata.** Add the source-to-destination mapping to
   `sync-manifest.json`:

   ```json
   { "src": "scripts/check_example.py", "dest": ".github/scripts/check_example.py", "mode": "overwrite" }
   ```

6. **Update CI intentionally.** If the check should be its own CI job, add that
   job to `.github/workflows/python-qa.yml` and include it in the `ci-passed`
   dependency list. For this template's self-dogfooding CI, keep the released
   copy in `.github/scripts/` byte-identical to `scripts/` when the workflow
   needs to execute the new check before the next release sync.

7. **Validate.**

   ```bash
   python scripts/qa.py
   ```

   Also run any org gate tools that cover the changed file type.

## Notes

- Do not add a shared helper module for check scripts; the template ADRs keep
  the scripts standalone.
- Prefer configuration already owned by common tools, such as `[tool.ruff]`,
  `[tool.mypy]`, or `[tool.pytest.ini_options]`, over a template-specific
  config namespace.
