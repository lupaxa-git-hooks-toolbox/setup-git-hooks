from __future__ import annotations

from pathlib import Path

GITIGNORE_COMMENT = "# Git Hooks Toolbox — generated subhooks"
GITIGNORE_RULE = "hooks/*/*"
GITIGNORE_SNIPPET = f"{GITIGNORE_COMMENT}\n{GITIGNORE_RULE}\n"


class GitignoreError(Exception):
    """Could not update .gitignore."""


def ensure_gitignore(repo_root: Path) -> None:
    path = repo_root / ".gitignore"
    try:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if GITIGNORE_RULE in existing.splitlines():
            return
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        block = GITIGNORE_SNIPPET if not existing else f"{prefix}\n{GITIGNORE_SNIPPET}"
        path.write_text(existing + block, encoding="utf-8")
    except OSError as exc:
        raise GitignoreError(f"Could not update {path}: {exc}") from exc
