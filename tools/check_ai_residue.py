"""Scan tracked text and PR commit messages for attribution residue."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


MARKERS = tuple(
    "".join(parts)
    for parts in (
        ("Co", "dex"),
        ("Clau", "de"),
        ("Co", "pilot"),
        ("Chat", "GPT"),
        ("Ge", "mini"),
        ("an", "thropic"),
        ("Generated", " with"),
        ("Co-authored", "-by"),
    )
)


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


def tracked_paths() -> list[str]:
    output = run_git(["ls-files", "--cached", "--others", "--exclude-standard"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    data = path.read_bytes()
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="ignore")


def find_markers(label: str, text: str) -> list[str]:
    haystack = text.casefold()
    return [marker for marker in MARKERS if marker.casefold() in haystack]


def commit_messages() -> str:
    base_ref = os.environ.get("AI_RESIDUE_BASE_REF", "").strip()
    if base_ref and run_git(["rev-parse", "--verify", base_ref]) is not None:
        return run_git(["log", "--format=%B", f"{base_ref}..HEAD"]) or ""
    if os.environ.get("GITHUB_ACTIONS"):
        return run_git(["log", "--format=%B", "-n", "1", "HEAD"]) or ""
    return ""


def main() -> None:
    failures: list[str] = []

    for rel_path in tracked_paths():
        path = ROOT / rel_path
        text = read_text(path)
        if text is None:
            continue
        matches = find_markers(rel_path, text)
        if matches:
            failures.append(f"{rel_path}: {', '.join(matches)}")

    messages = commit_messages()
    if messages:
        matches = find_markers("commit messages", messages)
        if matches:
            failures.append(f"commit messages: {', '.join(matches)}")

    if failures:
        joined = "\n  - ".join(failures)
        raise SystemExit(f"attribution-residue check failed:\n  - {joined}")

    print("attribution-residue check passed")


if __name__ == "__main__":
    main()
