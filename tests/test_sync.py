"""Tests for scripts/sync.py — manifest-driven file sync."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.sync import marker_preserve_copy, sync


class TestMarkerPreserveCopy:
    """Tests for the marker-preserve merge strategy."""

    def test_replaces_template_regions(self, tmp_path: Path) -> None:
        src = tmp_path / "src.json"
        dst = tmp_path / "dst.json"

        src.write_text("// #region Template:QA\nNEW CONTENT\n// #endregion Template:QA\n")
        dst.write_text("// #region Template:QA\nOLD CONTENT\n// #endregion Template:QA\n")

        marker_preserve_copy(src, dst)
        result = dst.read_text()

        assert "NEW CONTENT" in result
        assert "OLD CONTENT" not in result

    def test_preserves_repo_specific_content(self, tmp_path: Path) -> None:
        src = tmp_path / "src.json"
        dst = tmp_path / "dst.json"

        src.write_text("// #region Template:QA\nTEMPLATE\n// #endregion Template:QA\n")
        dst.write_text("REPO HEADER\n// #region Template:QA\nOLD\n// #endregion Template:QA\nREPO FOOTER\n")

        marker_preserve_copy(src, dst)
        result = dst.read_text()

        assert "REPO HEADER" in result
        assert "REPO FOOTER" in result
        assert "TEMPLATE" in result
        assert "OLD" not in result

    def test_multiple_regions(self, tmp_path: Path) -> None:
        src = tmp_path / "src.json"
        dst = tmp_path / "dst.json"

        src.write_text(
            "// #region Template:A\nNEW_A\n// #endregion Template:A\n"
            "// #region Template:B\nNEW_B\n// #endregion Template:B\n"
        )
        dst.write_text(
            "// #region Template:A\nOLD_A\n// #endregion Template:A\n"
            "BETWEEN\n"
            "// #region Template:B\nOLD_B\n// #endregion Template:B\n"
        )

        marker_preserve_copy(src, dst)
        result = dst.read_text()

        assert "NEW_A" in result
        assert "NEW_B" in result
        assert "BETWEEN" in result
        assert "OLD_A" not in result
        assert "OLD_B" not in result

    def test_creates_dst_if_missing(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        dst = tmp_path / "subdir" / "dst.txt"

        src.write_text("content")

        marker_preserve_copy(src, dst)

        assert dst.exists()
        assert dst.read_text() == "content"

    def test_region_in_src_not_in_dst(self, tmp_path: Path) -> None:
        """Regions in src but not dst — dst is unchanged outside its own regions."""
        src = tmp_path / "src.json"
        dst = tmp_path / "dst.json"

        src.write_text("// #region Template:New\nSTUFF\n// #endregion Template:New\n")
        dst.write_text("NO REGIONS HERE\n")

        marker_preserve_copy(src, dst)

        assert dst.read_text() == "NO REGIONS HERE\n"


class TestSync:
    """Tests for the full sync function."""

    def _make_template(self, tmp_path: Path) -> Path:
        """Create a minimal template directory with manifest and source files."""
        template = tmp_path / "template"
        template.mkdir()

        scripts = template / "scripts"
        scripts.mkdir()
        (scripts / "check_lint.py").write_text("# lint script\n")
        (scripts / "check_types.py").write_text("# types script\n")

        reference = template / "reference"
        reference.mkdir()
        (reference / "settings.json").write_text('{"editor.rulers": [120]}\n')

        manifest = {
            "files": [
                {"src": "scripts/check_lint.py", "dest": ".github/scripts/check_lint.py", "mode": "overwrite"},
                {"src": "scripts/check_types.py", "dest": ".github/scripts/check_types.py", "mode": "overwrite"},
                {"src": "reference/settings.json", "dest": ".vscode/settings.json", "mode": "overwrite"},
            ]
        }
        (template / "sync-manifest.json").write_text(json.dumps(manifest))

        return template

    def test_syncs_all_files(self, tmp_path: Path) -> None:
        template = self._make_template(tmp_path)
        repo = tmp_path / "repo"
        repo.mkdir()

        count = sync(template, repo)

        assert count == 3
        assert (repo / ".github" / "scripts" / "check_lint.py").read_text() == "# lint script\n"
        assert (repo / ".github" / "scripts" / "check_types.py").read_text() == "# types script\n"
        assert (repo / ".vscode" / "settings.json").read_text() == '{"editor.rulers": [120]}\n'

    def test_creates_directories(self, tmp_path: Path) -> None:
        template = self._make_template(tmp_path)
        repo = tmp_path / "repo"
        repo.mkdir()

        sync(template, repo)

        assert (repo / ".github" / "scripts").is_dir()
        assert (repo / ".vscode").is_dir()

    def test_overwrites_existing_files(self, tmp_path: Path) -> None:
        template = self._make_template(tmp_path)
        repo = tmp_path / "repo"
        repo.mkdir()
        scripts_dir = repo / ".github" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "check_lint.py").write_text("# old version\n")

        sync(template, repo)

        assert (scripts_dir / "check_lint.py").read_text() == "# lint script\n"

    def test_skips_missing_source(self, tmp_path: Path) -> None:
        template = tmp_path / "template"
        template.mkdir()

        manifest = {
            "files": [
                {"src": "does/not/exist.py", "dest": "output.py", "mode": "overwrite"},
            ]
        }
        (template / "sync-manifest.json").write_text(json.dumps(manifest))

        count = sync(template, tmp_path / "repo")
        assert count == 0

    def test_marker_preserve_mode(self, tmp_path: Path) -> None:
        template = tmp_path / "template"
        template.mkdir()

        (template / "tasks.json").write_text("// #region Template:QA\nNEW QA\n// #endregion Template:QA\n")

        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "tasks.json").write_text("REPO STUFF\n// #region Template:QA\nOLD QA\n// #endregion Template:QA\n")

        manifest = {
            "files": [
                {"src": "tasks.json", "dest": "tasks.json", "mode": "marker-preserve"},
            ]
        }
        (template / "sync-manifest.json").write_text(json.dumps(manifest))

        count = sync(template, repo)
        result = (repo / "tasks.json").read_text()

        assert count == 1
        assert "REPO STUFF" in result
        assert "NEW QA" in result
        assert "OLD QA" not in result

    def test_empty_manifest(self, tmp_path: Path) -> None:
        template = tmp_path / "template"
        template.mkdir()
        (template / "sync-manifest.json").write_text('{"files": []}')

        count = sync(template, tmp_path / "repo")
        assert count == 0

    def test_missing_manifest_exits(self, tmp_path: Path) -> None:
        import pytest

        template = tmp_path / "template"
        template.mkdir()

        with pytest.raises(SystemExit):
            sync(template, tmp_path / "repo")
