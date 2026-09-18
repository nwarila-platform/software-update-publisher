"""Tests for the release drift guard."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools import check_release_drift as release_drift


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(  # noqa: S603 - controlled tests invoke local git
        ["git", *args],  # noqa: S607
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def reusable_workflow(has_workflow_call: bool) -> str:
    trigger = "  workflow_call:\n" if has_workflow_call else "  workflow_dispatch:\n"
    return (
        "name: Reusable\n"
        "\n"
        "on:\n"
        f"{trigger}"
        "\n"
        "jobs:\n"
        "  noop:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo ok\n"
    )


def write_release_files(repo: Path, tag: str, *, self_update_call: bool = True, python_qa_call: bool = True) -> None:
    scripts_dir = repo / ".github" / "scripts"
    workflows_dir = repo / ".github" / "workflows"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    workflows_dir.mkdir(parents=True, exist_ok=True)

    (scripts_dir / ".version").write_text(f"{tag}\n", encoding="utf-8")
    (workflows_dir / "self-update.yml").write_text(reusable_workflow(self_update_call), encoding="utf-8")
    (workflows_dir / "python-qa.yml").write_text(reusable_workflow(python_qa_call), encoding="utf-8")
    (repo / "README.md").write_text("# release fixture\n", encoding="utf-8")


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(repo, "commit", "-m", message)


def create_release_repo(
    tmp_path: Path,
    *,
    self_update_call: bool = True,
    python_qa_call: bool = True,
) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Release Test")
    git(repo, "config", "user.email", "release-test@example.com")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "tag.gpgsign", "false")

    write_release_files(repo, "v1.0.5")
    commit_all(repo, "release v1.0.5")
    git(repo, "tag", "v1.0.5")

    write_release_files(
        repo,
        "v1.0.6",
        self_update_call=self_update_call,
        python_qa_call=python_qa_call,
    )
    commit_all(repo, "release v1.0.6")
    git(repo, "tag", "v1.0.6")
    git(repo, "tag", "v1", "v1.0.6")

    return repo


def test_release_drift_guard_passes_when_version_and_floating_tag_are_current(tmp_path: Path) -> None:
    repo = create_release_repo(tmp_path)
    release_drift.ROOT = repo

    assert release_drift.collect_errors() == []


def test_release_drift_guard_fails_when_version_marker_drifts(tmp_path: Path) -> None:
    repo = create_release_repo(tmp_path)
    release_drift.ROOT = repo
    (repo / ".github" / "scripts" / ".version").write_text("v1.0.5\n", encoding="utf-8")

    errors = release_drift.collect_errors()

    assert any(".github/scripts/.version" in error for error in errors)


def test_release_drift_guard_fails_when_v1_points_at_an_old_release(tmp_path: Path) -> None:
    repo = create_release_repo(tmp_path)
    release_drift.ROOT = repo
    git(repo, "tag", "--force", "v1", "v1.0.5")

    errors = release_drift.collect_errors()

    assert any("floating v1 resolves" in error for error in errors)


def test_release_drift_guard_fails_when_reusable_workflow_call_is_missing(tmp_path: Path) -> None:
    repo = create_release_repo(tmp_path, self_update_call=False)
    release_drift.ROOT = repo

    errors = release_drift.collect_errors()

    assert ".github/workflows/self-update.yml@v1 does not declare on: workflow_call" in errors


def test_declares_workflow_call_accepts_quoted_trigger_key() -> None:
    workflow_text = 'name: Reusable\n\non:\n  "workflow_call":\n\njobs:\n  noop:\n    runs-on: ubuntu-latest\n'

    assert release_drift.declares_workflow_call(workflow_text)


def test_declares_workflow_call_ignores_nested_input_named_workflow_call() -> None:
    workflow_text = (
        "name: Manual\n"
        "\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "    inputs:\n"
        "      workflow_call:\n"
        "        description: Not a reusable workflow trigger\n"
        "\n"
        "jobs:\n"
        "  noop:\n"
        "    runs-on: ubuntu-latest\n"
    )

    assert not release_drift.declares_workflow_call(workflow_text)
