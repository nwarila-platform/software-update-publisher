"""Validate ADR structure and living-update guardrails."""

from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADR_ROOT = ROOT / "docs" / "decision-records"
TODAY = dt.date.today()

ADR_PATTERNS = (
    "docs/decision-records/[0-9][0-9][0-9][0-9]-*.md",
    "docs/decision-records/org/[0-9][0-9][0-9][0-9]-*.md",
    "docs/decision-records/template/[0-9][0-9][0-9][0-9]-*.md",
    "docs/decision-records/repo/[0-9][0-9][0-9][0-9]-*.md",
)

LEGACY_HEADINGS = (
    "## TL;DR",
    "## Context and Problem Statement",
    "## Decision Drivers",
    "## Considered Options",
    "## Decision Outcome",
    "## Pros and Cons of the Options",
    "## Confirmation",
    "## Consequences",
    "## Assumptions",
    "## Supersedes",
    "## Superseded by",
    "## Implementing PRs",
    "## Related ADRs",
    "## Compliance Notes",
)

LIVING_FIELDS = (
    "id",
    "scope",
    "status",
    "decision-subject",
    "date accepted",
    "date",
    "last reviewed",
    "authors",
    "decision-makers",
    "consulted",
    "informed",
    "reversibility",
    "review-by",
)

VALID_STATUSES = {"proposed", "accepted", "superseded", "obsolete", "deprecated"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ADR_ID_RE = re.compile(r"ADR-(\d{4})")


def run_git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None


def fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT).as_posix()}: {message}")


def adr_files() -> list[Path]:
    files: list[Path] = []
    for pattern in ADR_PATTERNS:
        files.extend(ROOT.glob(pattern))
    return sorted(files)


def parse_metadata(text: str) -> dict[str, str]:
    lines = text.splitlines()
    table: dict[str, str] = {}
    in_table = False
    for line in lines:
        if not line.startswith("|"):
            if in_table:
                break
            continue
        in_table = True
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2 or set(cells[0]) <= {"-", " "}:
            continue
        if cells[0].lower() == "field":
            continue
        table[cells[0].lower()] = cells[1]
    return table


def section_body(text: str, heading: str) -> str:
    marker = f"\n{heading}\n"
    if marker not in f"\n{text}":
        return ""
    after = f"\n{text}".split(marker, 1)[1]
    next_heading = re.search(r"\n## ", after)
    if next_heading:
        return after[: next_heading.start()].strip()
    return after.strip()


def body_without_changelog(text: str) -> str:
    marker = "\n## Changelog\n"
    if marker not in f"\n{text}":
        return text.strip()
    return f"\n{text}".split(marker, 1)[0].strip()


def changelog_rows(text: str) -> list[str]:
    body = section_body(text, "## Changelog")
    rows: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0].lower()
        if first == "date" or set(cells[0]) <= {"-", " "}:
            continue
        rows.append(stripped)
    return rows


def changed_adr_paths() -> set[str]:
    paths: set[str] = set()
    base_ref = os.environ.get("ADR_SCHEMA_BASE_REF", "").strip()
    diff_args = []
    if base_ref and run_git(["rev-parse", "--verify", base_ref]) is not None:
        diff_args.append(
            [
                "diff",
                "--name-only",
                "--diff-filter=AM",
                f"{base_ref}...HEAD",
                "--",
                "docs/decision-records",
            ]
        )
    diff_args.extend(
        [
            ["diff", "--name-only", "--diff-filter=AM", "--", "docs/decision-records"],
            ["diff", "--cached", "--name-only", "--diff-filter=AM", "--", "docs/decision-records"],
        ]
    )
    for args in diff_args:
        diff = run_git(args)
        if not diff:
            continue
        paths.update(
            line.strip().replace("\\", "/")
            for line in diff.splitlines()
            if line.strip().endswith(".md") and not line.strip().endswith("/README.md")
        )
    return paths


def old_text(base_ref: str, rel_path: str) -> str | None:
    return run_git(["show", f"{base_ref}:{rel_path}"])


def validate_required_shape(path: Path, text: str, errors: list[str]) -> None:
    for heading in LEGACY_HEADINGS:
        if f"\n{heading}\n" not in f"\n{text}\n":
            fail(errors, path, f"missing required heading {heading!r}")


def validate_living_shape(path: Path, text: str, errors: list[str]) -> None:
    metadata = parse_metadata(text)
    for field in LIVING_FIELDS:
        if field not in metadata or not metadata[field].strip():
            fail(errors, path, f"missing living metadata field {field!r}")

    status = metadata.get("status", "").lower().split()[0]
    if status and status not in VALID_STATUSES:
        fail(errors, path, f"unsupported status {metadata['status']!r}")

    for field in ("date accepted", "date", "last reviewed"):
        value = metadata.get(field, "")
        if value and not DATE_RE.match(value):
            fail(errors, path, f"{field!r} must use YYYY-MM-DD")

    if "decision-maker" in metadata:
        fail(errors, path, "use 'Decision-makers', not 'Decision-maker'")

    if "\n## Changelog\n" not in f"\n{text}\n":
        fail(errors, path, "missing required heading '## Changelog'")
    rows = changelog_rows(text)
    if not rows:
        fail(errors, path, "Changelog must contain at least one data row")
    for row in rows:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) != 5 or any(not cell for cell in cells):
            fail(errors, path, f"Changelog row must have five non-empty cells: {row!r}")

    last_reviewed = metadata.get("last reviewed", "")
    if DATE_RE.match(last_reviewed):
        reviewed = dt.date.fromisoformat(last_reviewed)
        cadence_days = 365 if "/repo/" in path.as_posix() else 180
        if TODAY - reviewed > dt.timedelta(days=cadence_days):
            fail(errors, path, f"Last reviewed is older than {cadence_days} days")


def validate_terminal_links(path: Path, text: str, files_by_number: dict[str, Path], errors: list[str]) -> None:
    metadata = parse_metadata(text)
    status = metadata.get("status", "").lower()
    if not status.startswith("superseded"):
        return

    successor_body = section_body(text, "## Superseded by")
    match = ADR_ID_RE.search(successor_body)
    if not match:
        fail(errors, path, "Superseded ADR must name a successor in '## Superseded by'")
        return

    successor = files_by_number.get(match.group(1))
    if successor is None:
        fail(errors, path, f"successor ADR-{match.group(1)} does not exist")
        return

    successor_text = successor.read_text(encoding="utf-8")
    current_id = f"ADR-{path.name[:4]}"
    if current_id not in section_body(successor_text, "## Supersedes"):
        fail(errors, path, f"successor {successor.name} does not reciprocate Supersedes link")


def validate_changed_adr(path: Path, rel_path: str, text: str, errors: list[str]) -> None:
    base_ref = os.environ.get("ADR_SCHEMA_BASE_REF", "").strip()
    previous = old_text(base_ref, rel_path) if base_ref else None

    validate_living_shape(path, text, errors)

    new_rows = changelog_rows(text)
    old_rows = changelog_rows(previous) if previous is not None else []
    if old_rows and new_rows[: len(old_rows)] != old_rows:
        fail(errors, path, "Changelog rows must be append-only")
    appended_rows = new_rows[len(old_rows) :]

    if previous is None:
        if not appended_rows:
            fail(errors, path, "new ADR must include an initial Changelog row")
        return

    old_body = body_without_changelog(previous)
    new_body = body_without_changelog(text)
    old_metadata = parse_metadata(previous)
    new_metadata = parse_metadata(text)
    body_changed = old_body != new_body
    review_changed = old_metadata.get("last reviewed") != new_metadata.get("last reviewed")

    if (body_changed or review_changed) and not appended_rows:
        fail(errors, path, "ADR body or Last reviewed changed without a new Changelog row")

    old_status = old_metadata.get("status", "").lower().split()[0]
    if old_status in {"superseded", "obsolete"} and body_changed:
        fail(errors, path, f"terminal {old_status!r} ADR body must stay frozen")


def main() -> None:
    errors: list[str] = []
    files = adr_files()
    files_by_number = {path.name[:4]: path for path in files}
    changed = changed_adr_paths()

    for path in files:
        text = path.read_text(encoding="utf-8")
        rel_path = path.relative_to(ROOT).as_posix()
        validate_required_shape(path, text, errors)
        validate_terminal_links(path, text, files_by_number, errors)
        if rel_path in changed:
            validate_changed_adr(path, rel_path, text, errors)

    if errors:
        joined = "\n  - ".join(errors)
        raise SystemExit(f"ADR schema check failed:\n  - {joined}")

    scope = f"{len(changed)} changed ADR(s)" if changed else "static ADR shape"
    print(f"ADR schema check passed: {len(files)} ADR(s), {scope}")


if __name__ == "__main__":
    main()
