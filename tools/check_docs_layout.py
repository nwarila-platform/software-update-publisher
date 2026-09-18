"""Validate the org documentation layout."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

ALLOWED_DOC_DIRS = {
    "decision-records",
    "diagrams",
    "explanation",
    "how-to",
    "reference",
    "runbooks",
    "tutorials",
}

ALLOWED_DIAGRAM_SUFFIXES = {".mmd"}


def fail(message: str) -> None:
    raise SystemExit(f"docs-layout check failed: {message}")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> None:
    if not DOCS.is_dir():
        fail("docs/ is missing")

    missing = [name for name in sorted(ALLOWED_DOC_DIRS) if not (DOCS / name).is_dir()]
    if missing:
        fail(f"required docs subdirectories are missing: {missing}")

    unexpected_dirs = [
        rel(path)
        for path in DOCS.iterdir()
        if path.is_dir() and path.name not in ALLOWED_DOC_DIRS
    ]
    if unexpected_dirs:
        fail(f"unexpected top-level docs directories: {unexpected_dirs}")

    misplaced_markdown = [
        rel(path)
        for path in DOCS.rglob("*.md")
        if path.relative_to(DOCS).parts[0] not in (ALLOWED_DOC_DIRS - {"diagrams"})
    ]
    if misplaced_markdown:
        fail(f"Markdown files are outside sanctioned docs subtrees: {misplaced_markdown}")

    bad_diagrams = [
        rel(path)
        for path in (DOCS / "diagrams").rglob("*")
        if path.is_file() and path.name != ".gitkeep" and path.suffix not in ALLOWED_DIAGRAM_SUFFIXES
    ]
    if bad_diagrams:
        fail(f"diagram sources must use .mmd: {bad_diagrams}")

    print("docs-layout check passed")


if __name__ == "__main__":
    main()
