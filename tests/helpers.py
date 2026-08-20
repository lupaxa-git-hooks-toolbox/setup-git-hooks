from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    run_git(["init", "-b", "master"], cwd=path)
    run_git(["config", "user.email", "test@example.test"], cwd=path)
    run_git(["config", "user.name", "Setup Hooks Test"], cwd=path)
    run_git(["config", "tag.forceSignAnnotated", "false"], cwd=path)
    run_git(["config", "tag.gpgsign", "false"], cwd=path)
    return path


def commit_file(repo: Path, relpath: str, content: str, message: str) -> str:
    dest = repo / relpath
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    run_git(["add", relpath], cwd=repo)
    run_git(["commit", "-m", message], cwd=repo)
    return run_git(["rev-parse", "HEAD"], cwd=repo)
