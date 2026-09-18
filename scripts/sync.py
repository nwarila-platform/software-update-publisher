"""Sync template-managed files into a target repo using sync-manifest.json.

Usage:
    python sync.py TEMPLATE_ROOT REPO_ROOT

Reads sync-manifest.json from TEMPLATE_ROOT, copies files into REPO_ROOT using
the mode specified for each mapping:

    overwrite          Full replacement.
    marker-preserve    Replaces template-owned // #region sections while
                       preserving repo-specific content.

Exit codes:
    0    Success (prints synced file count).
    1    Missing arguments or manifest not found.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def marker_preserve_copy(src: Path, dst: Path) -> None:
    """Copy src to dst, preserving content outside template marker regions."""
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(), encoding="utf-8")
        return

    src_text = src.read_text(encoding="utf-8")
    dst_text = dst.read_text(encoding="utf-8")

    pattern = re.compile(
        r"(//\s*#region\s+Template:\s*\S+.*?\n)(.*?)(//\s*#endregion\s+Template:)",
        re.DOTALL,
    )

    src_regions: dict[str, str] = {}
    for match in pattern.finditer(src_text):
        name_match = re.search(r"Template:\s*(\S+)", match.group(1))
        if name_match:
            src_regions[name_match.group(1)] = match.group(2)

    def replace_region(match: re.Match[str]) -> str:
        name_match = re.search(r"Template:\s*(\S+)", match.group(1))
        if name_match and name_match.group(1) in src_regions:
            return match.group(1) + src_regions[name_match.group(1)] + match.group(3)
        return match.group(0)

    dst.write_text(pattern.sub(replace_region, dst_text), encoding="utf-8")


def sync(template_root: Path, repo_root: Path) -> int:
    """Run the sync and return the number of files synced."""
    manifest_path = template_root / "sync-manifest.json"
    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    changed: list[str] = []
    for mapping in manifest.get("files", []):
        src = template_root / mapping["src"]
        dst = repo_root / mapping["dest"]
        mode = mapping.get("mode", "overwrite")

        if not src.exists():
            print(f"  Skip (source missing): {mapping['src']}")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)

        if mode == "marker-preserve":
            marker_preserve_copy(src, dst)
        else:
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

        changed.append(mapping["dest"])
        print(f"  Synced: {mapping['src']} -> {mapping['dest']} ({mode})")

    print(f"\n{len(changed)} file(s) synced.")
    return len(changed)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} TEMPLATE_ROOT REPO_ROOT", file=sys.stderr)
        sys.exit(1)

    sync(Path(sys.argv[1]), Path(sys.argv[2]))
