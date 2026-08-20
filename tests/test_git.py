from __future__ import annotations

from pathlib import Path

import pytest

from setup_hooks.git import GitError, fetch_blob, resolve_version, work_tree_root
from tests.helpers import commit_file, init_repo, run_git


def test_work_tree_root(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "consumer")
    assert work_tree_root(repo) == repo.resolve()
    with pytest.raises(GitError, match="git"):
        work_tree_root(tmp_path / "not-a-repo")


def test_resolve_head_latest_tag_and_sha(tmp_path: Path) -> None:
    upstream = init_repo(tmp_path / "hook")
    commit_file(upstream, "src/pre-commit", "old\n", "first")
    run_git(["tag", "v0.1.0"], cwd=upstream)
    sha = commit_file(upstream, "src/pre-commit", "new\n", "second")
    run_git(["tag", "v1.2.0"], cwd=upstream)
    url = str(upstream)
    assert resolve_version(url, "HEAD") == "master"
    assert resolve_version(url, "LATEST") == "v1.2.0"
    assert resolve_version(url, "v0.1.0") == "v0.1.0"
    assert resolve_version(url, sha) == sha
    with pytest.raises(GitError):
        resolve_version(url, "v9.9.9")


def test_resolve_latest_prefers_final_release_over_prereleases(tmp_path: Path) -> None:
    upstream = init_repo(tmp_path / "hook")
    commit_file(upstream, "src/pre-commit", "rc1\n", "rc1")
    run_git(["tag", "v1.0.0-rc1"], cwd=upstream)
    commit_file(upstream, "src/pre-commit", "rc9\n", "rc9")
    run_git(["tag", "v1.0.0-rc9"], cwd=upstream)
    commit_file(upstream, "src/pre-commit", "rc10\n", "rc10")
    run_git(["tag", "v1.0.0-rc10"], cwd=upstream)
    commit_file(upstream, "src/pre-commit", "final\n", "final")
    run_git(["tag", "v1.0.0"], cwd=upstream)
    assert resolve_version(str(upstream), "LATEST") == "v1.0.0"


def test_fetch_blob_and_missing_path(tmp_path: Path) -> None:
    upstream = init_repo(tmp_path / "hook")
    commit_file(upstream, "src/pre-commit", "hook-body\n", "add hook")
    url = str(upstream)
    assert fetch_blob(url, "master", "src/pre-commit") == b"hook-body\n"
    with pytest.raises(GitError, match="src/missing"):
        fetch_blob(url, "master", "src/missing")


def test_fetch_blob_at_tag_and_sha(tmp_path: Path) -> None:
    upstream = init_repo(tmp_path / "hook")
    sha = commit_file(upstream, "src/pre-commit", "tagged\n", "add hook")
    run_git(["tag", "v1.0.0"], cwd=upstream)
    commit_file(upstream, "src/pre-commit", "later\n", "later")
    url = str(upstream)
    assert fetch_blob(url, "v1.0.0", "src/pre-commit") == b"tagged\n"
    assert fetch_blob(url, sha, "src/pre-commit") == b"tagged\n"
