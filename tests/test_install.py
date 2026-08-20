from __future__ import annotations

from pathlib import Path

import pytest

from setup_hooks.git import GitError
from setup_hooks.install import InstallError, install_hook_type


def _hooks_dir(repo: Path) -> Path:
    return repo / ".git" / "hooks"


def _write_configs(repo: Path, *, mux: bool = True) -> None:
    hooks = repo / "hooks"
    hooks.mkdir()
    (hooks / "pre-commit-config.yml").write_text(
        "- name: Ruff\n"
        "  filename: ruff\n"
        "  url: /upstream/ruff\n"
        "  version: HEAD\n"
        "- name: Confirm\n"
        "  filename: confirm\n"
        "  url: /upstream/confirm\n"
        "  version: HEAD\n",
        encoding="utf-8",
    )
    if mux:
        (hooks / "multiplexer-config.yml").write_text(
            "url: /upstream/mux\nversion: HEAD\n",
            encoding="utf-8",
        )


def _fake_resolve(url: str, version: str) -> str:
    return "master"


def _fake_fetch(url: str, ref: str, blob_path: str) -> bytes:
    return f"{url}:{blob_path}\n".encode()


def test_first_install_writes_prefixed_executables_and_mux(tmp_path: Path) -> None:
    repo = tmp_path / "consumer"
    repo.mkdir()
    _hooks_dir(repo).mkdir(parents=True)
    _write_configs(repo)
    install_hook_type(
        repo,
        "pre-commit",
        skip_gitignore=True,
        hooks_dir=_hooks_dir(repo),
        resolve_version=_fake_resolve,
        fetch_blob=_fake_fetch,
    )
    first = repo / "hooks" / "pre-commit" / "01-ruff"
    second = repo / "hooks" / "pre-commit" / "02-confirm"
    mux = repo / ".git" / "hooks" / "pre-commit"
    assert first.read_text(encoding="utf-8") == "/upstream/ruff:src/pre-commit\n"
    assert second.read_text(encoding="utf-8") == "/upstream/confirm:src/pre-commit\n"
    assert mux.read_text(encoding="utf-8") == "/upstream/mux:src/multiplexer\n"
    assert first.stat().st_mode & 0o111
    assert mux.stat().st_mode & 0o111


def test_rerun_without_force_fails(tmp_path: Path) -> None:
    repo = tmp_path / "consumer"
    repo.mkdir()
    _hooks_dir(repo).mkdir(parents=True)
    _write_configs(repo)
    install_hook_type(
        repo,
        "pre-commit",
        skip_gitignore=True,
        hooks_dir=_hooks_dir(repo),
        resolve_version=_fake_resolve,
        fetch_blob=_fake_fetch,
    )
    before = (repo / "hooks" / "pre-commit" / "01-ruff").read_bytes()
    with pytest.raises(InstallError, match="--force"):
        install_hook_type(
            repo,
            "pre-commit",
            skip_gitignore=True,
            hooks_dir=_hooks_dir(repo),
            resolve_version=_fake_resolve,
            fetch_blob=_fake_fetch,
        )
    assert (repo / "hooks" / "pre-commit" / "01-ruff").read_bytes() == before


def test_force_clears_generated_and_keeps_yaml(tmp_path: Path) -> None:
    repo = tmp_path / "consumer"
    repo.mkdir()
    _hooks_dir(repo).mkdir(parents=True)
    _write_configs(repo)
    target = repo / "hooks" / "pre-commit"
    target.mkdir()
    stale = target / "01-old"
    stale.write_text("stale\n", encoding="utf-8")
    extra = target / "notes.txt"
    extra.write_text("keep\n", encoding="utf-8")
    install_hook_type(
        repo,
        "pre-commit",
        force=True,
        skip_gitignore=True,
        hooks_dir=_hooks_dir(repo),
        resolve_version=_fake_resolve,
        fetch_blob=_fake_fetch,
    )
    assert not stale.exists()
    assert extra.exists()
    assert (repo / "hooks" / "pre-commit-config.yml").exists()
    assert (repo / "hooks" / "pre-commit" / "01-ruff").exists()


def test_skip_multiplexer_does_not_require_mux_config(tmp_path: Path) -> None:
    repo = tmp_path / "consumer"
    repo.mkdir()
    _hooks_dir(repo).mkdir(parents=True)
    _write_configs(repo, mux=False)
    install_hook_type(
        repo,
        "pre-commit",
        skip_multiplexer=True,
        skip_gitignore=True,
        hooks_dir=_hooks_dir(repo),
        resolve_version=_fake_resolve,
        fetch_blob=_fake_fetch,
    )
    assert not (repo / ".git" / "hooks" / "pre-commit").exists()


def test_missing_mux_config_fails_before_fetch(tmp_path: Path) -> None:
    repo = tmp_path / "consumer"
    repo.mkdir()
    _hooks_dir(repo).mkdir(parents=True)
    _write_configs(repo, mux=False)

    def boom(url: str, ref: str, blob_path: str) -> bytes:
        raise AssertionError("fetch must not run")

    with pytest.raises(InstallError, match="multiplexer-config"):
        install_hook_type(
            repo,
            "pre-commit",
            skip_gitignore=True,
            hooks_dir=_hooks_dir(repo),
            resolve_version=_fake_resolve,
            fetch_blob=boom,
        )


def test_fetch_failure_on_first_install_leaves_no_generated(tmp_path: Path) -> None:
    repo = tmp_path / "consumer"
    repo.mkdir()
    _hooks_dir(repo).mkdir(parents=True)
    _write_configs(repo)
    seen = {"n": 0}

    def fetch_second_fails(url: str, ref: str, blob_path: str) -> bytes:
        seen["n"] += 1
        if seen["n"] == 2:
            raise GitError("fetch failed")
        return f"{url}:{blob_path}\n".encode()

    with pytest.raises(GitError, match="fetch failed"):
        install_hook_type(
            repo,
            "pre-commit",
            skip_gitignore=True,
            hooks_dir=_hooks_dir(repo),
            resolve_version=_fake_resolve,
            fetch_blob=fetch_second_fails,
        )
    dest = repo / "hooks" / "pre-commit"
    assert not dest.exists() or not any(dest.glob("[0-9][0-9]-*"))


def test_write_oserror_becomes_install_error(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "consumer"
    repo.mkdir()
    _hooks_dir(repo).mkdir(parents=True)
    _write_configs(repo)

    def boom(path: Path, content: bytes) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("setup_hooks.install.write_executable", boom)
    with pytest.raises(InstallError, match="Failed to write"):
        install_hook_type(
            repo,
            "pre-commit",
            skip_gitignore=True,
            hooks_dir=_hooks_dir(repo),
            resolve_version=_fake_resolve,
            fetch_blob=_fake_fetch,
        )
