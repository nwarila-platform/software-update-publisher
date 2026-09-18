#!/usr/bin/env python3
"""Validate release version markers and floating reusable workflow tags."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
ON_RE = re.compile(r"^on\s*:\s*(.*)$")
REUSABLE_WORKFLOWS = (
    ".github/workflows/self-update.yml",
    ".github/workflows/python-qa.yml",
)


class GitError(RuntimeError):
    """Raised when a required git lookup fails."""


@dataclass(frozen=True, order=True)
class ReleaseTag:
    major: int
    minor: int
    patch: int
    name: str


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(  # noqa: S603 - controlled git queries
            ["git", *args],  # noqa: S607
            cwd=ROOT,
            encoding="utf-8",
            stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        detail = f": {stderr}" if stderr else ""
        raise GitError(f"git {' '.join(args)} failed{detail}") from exc


def version_markers() -> tuple[Path, Path]:
    return (
        ROOT / ".github" / "scripts" / ".version",
        ROOT / "scripts" / ".version",
    )


def parse_release_tag(name: str) -> ReleaseTag | None:
    match = RELEASE_TAG_RE.match(name)
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return ReleaseTag(major=major, minor=minor, patch=patch, name=name)


def release_tags() -> list[ReleaseTag]:
    output = run_git(["tag", "--list", "v*"])
    tags = [parsed for line in output.splitlines() if (parsed := parse_release_tag(line.strip())) is not None]
    return sorted(tags)


def latest_release(tags: list[ReleaseTag]) -> ReleaseTag:
    if not tags:
        raise GitError("no vX.Y.Z release tags found")
    return tags[-1]


def latest_release_for_major(tags: list[ReleaseTag], major: int) -> ReleaseTag:
    matches = [tag for tag in tags if tag.major == major]
    if not matches:
        raise GitError(f"no v{major}.x release tags found")
    return matches[-1]


def resolve_commit(ref: str) -> str:
    return run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"])


def show_at_ref(ref: str, path: str) -> str:
    return run_git(["show", f"{ref}:{path}"])


def strip_yaml_comment(line: str) -> str:
    quote = ""
    result: list[str] = []
    for char in line:
        if quote:
            result.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            result.append(char)
            continue
        if char == "#":
            break
        result.append(char)
    return "".join(result).rstrip()


def mentions_workflow_call(value: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9_-])workflow_call(?![A-Za-z0-9_-])", value) is not None


def leading_spaces(value: str) -> int:
    return len(value) - len(value.lstrip(" "))


def is_workflow_call_event(value: str) -> bool:
    event = value.removeprefix("-").strip()
    if event.startswith(("'", '"')):
        quote = event[0]
        if not event.startswith(f"{quote}workflow_call{quote}"):
            return False
        suffix = event[len("'workflow_call'") :].lstrip()
        return suffix == "" or suffix.startswith(":")
    return event == "workflow_call" or event.startswith("workflow_call:")


def declares_workflow_call(workflow_text: str) -> bool:
    lines = workflow_text.splitlines()

    for index, line in enumerate(lines):
        if line[:1].isspace():
            continue

        stripped = strip_yaml_comment(line).strip()
        if not stripped:
            continue

        match = ON_RE.match(stripped)
        if match is None:
            continue

        inline_value = match.group(1).strip()
        if inline_value:
            return mentions_workflow_call(inline_value)

        child_indent: int | None = None
        for child in lines[index + 1 :]:
            child_without_comment = strip_yaml_comment(child)
            if not child_without_comment.strip():
                continue
            if not child[:1].isspace():
                return False

            indent = leading_spaces(child_without_comment)
            if child_indent is None:
                child_indent = indent
            if indent > child_indent:
                continue

            child_value = child_without_comment.strip()
            if is_workflow_call_event(child_value):
                return True
            if mentions_workflow_call(child_value) and child_value.startswith(("[", "{")):
                return True

        return False

    return False


def collect_errors() -> list[str]:
    errors: list[str] = []

    try:
        tags = release_tags()
        latest = latest_release(tags)
        latest_v1 = latest_release_for_major(tags, 1)
        latest_v1_commit = resolve_commit(latest_v1.name)
    except GitError as exc:
        return [str(exc)]

    required_marker, optional_marker = version_markers()
    if not required_marker.is_file():
        errors.append(".github/scripts/.version is missing")
    else:
        marker_value = required_marker.read_text(encoding="utf-8").strip()
        if marker_value != latest.name:
            errors.append(f".github/scripts/.version is {marker_value!r}, expected {latest.name!r}")

    if optional_marker.exists():
        marker_value = optional_marker.read_text(encoding="utf-8").strip()
        if marker_value != latest.name:
            errors.append(f"scripts/.version is {marker_value!r}, expected {latest.name!r}")

    try:
        floating_v1_commit = resolve_commit("v1")
    except GitError as exc:
        errors.append(str(exc))
    else:
        if floating_v1_commit != latest_v1_commit:
            errors.append(
                f"floating v1 resolves to {floating_v1_commit}, expected {latest_v1.name} at {latest_v1_commit}"
            )

    for workflow in REUSABLE_WORKFLOWS:
        try:
            workflow_text = show_at_ref("v1", workflow)
        except GitError as exc:
            errors.append(str(exc))
            continue
        if not declares_workflow_call(workflow_text):
            errors.append(f"{workflow}@v1 does not declare on: workflow_call")

    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        sys.stderr.write("release-drift check failed:\n")
        for error in errors:
            sys.stderr.write(f"  - {error}\n")
        return 1

    sys.stdout.write("release-drift check passed\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
