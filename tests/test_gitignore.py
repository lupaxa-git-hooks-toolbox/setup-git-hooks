from __future__ import annotations

from pathlib import Path

from setup_hooks.gitignore import GITIGNORE_RULE, GITIGNORE_SNIPPET, ensure_gitignore


def test_ensure_gitignore_creates_and_is_idempotent(tmp_path: Path) -> None:
    ensure_gitignore(tmp_path)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert GITIGNORE_RULE in text.splitlines()
    assert "# Git Hooks Toolbox — generated subhooks" in text
    ensure_gitignore(tmp_path)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == text


def test_ensure_gitignore_appends_existing(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    path.write_text(".venv/\n", encoding="utf-8")
    ensure_gitignore(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert ".venv/" in text
    assert GITIGNORE_RULE in text.splitlines()
    assert GITIGNORE_SNIPPET.splitlines()[0] in text
