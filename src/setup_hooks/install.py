from __future__ import annotations

import contextlib
import re
import sys
from collections.abc import Callable
from pathlib import Path

from setup_hooks import git as git_mod
from setup_hooks.config import (
    ConfigError,
    hook_type_config_path,
    installed_basename,
    load_hook_type_config,
    load_multiplexer_config,
    multiplexer_config_path,
)
from setup_hooks.gitignore import ensure_gitignore
from setup_hooks.progress import Progress

GENERATED_NAME = re.compile(r"^[0-9]{2}-")


class InstallError(Exception):
    """Refuse to overwrite, or install failed after validation."""


def generated_scripts(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    found = [
        path for path in directory.iterdir() if path.is_file() and GENERATED_NAME.match(path.name)
    ]
    return sorted(found)


def clear_generated_scripts(directory: Path) -> None:
    for path in generated_scripts(directory):
        path.unlink()


def write_executable(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    path.chmod(path.stat().st_mode | 0o111)


def _rollback(paths: list[Path]) -> None:
    for path in paths:
        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)


def _display_path(repo_root: Path, path: Path) -> str:
    if path.is_relative_to(repo_root):
        return str(path.relative_to(repo_root))
    return str(path)


def _install_label(progress: Progress, name: str, url: str, version: str, dest: str) -> str:
    if progress.verbose:
        return f"Installing {name} from {url} ({version}) -> {dest}"
    return f"Installing {name} -> {dest}"


def _destination_hooks_dir(repo_root: Path, hooks_dir: Path | None) -> Path:
    if hooks_dir is not None:
        return hooks_dir
    try:
        resolved = git_mod.git_hooks_dir(repo_root)
    except git_mod.GitError:
        return repo_root / ".git" / "hooks"
    configured = git_mod.core_hooks_path(repo_root)
    if configured:
        print(
            f"Warning: core.hooksPath is set to {configured}; "
            f"writing the multiplexer to {resolved}.",
            file=sys.stderr,
        )
    return resolved


def install_hook_type(
    repo_root: Path,
    hook_type: str,
    *,
    force: bool = False,
    skip_multiplexer: bool = False,
    skip_gitignore: bool = False,
    hooks_dir: Path | None = None,
    resolve_version: Callable[[str, str], str] = git_mod.resolve_version,
    fetch_blob: Callable[[str, str, str], bytes] = git_mod.fetch_blob,
    progress: Progress | None = None,
) -> None:
    config_dir = repo_root / "hooks"
    config_path = hook_type_config_path(config_dir, hook_type)
    if not config_path.is_file():
        raise InstallError(f"{config_path} does not exist.")
    try:
        entries = load_hook_type_config(config_path)
        mux = None
        if not skip_multiplexer:
            mux_path = multiplexer_config_path(config_dir)
            if not mux_path.is_file():
                raise InstallError(f"{mux_path} does not exist.")
            mux = load_multiplexer_config(mux_path)
    except ConfigError as exc:
        raise InstallError(str(exc)) from exc

    dest_dir = config_dir / hook_type
    existing = generated_scripts(dest_dir)
    if existing and not force:
        raise InstallError(
            f"Generated scripts already exist in {dest_dir}. Re-run with --force to replace them."
        )

    report = progress if progress is not None else Progress(enabled=False)
    if existing and force:
        report.info(f"Replacing generated scripts in hooks/{hook_type}.")

    jobs: list[tuple[Path, str, str, str, str]] = []
    for index, entry in enumerate(entries, start=1):
        dest = dest_dir / installed_basename(index, entry.filename)
        jobs.append((dest, entry.name, entry.url, entry.version, f"src/{hook_type}"))
    if mux is not None:
        dest = _destination_hooks_dir(repo_root, hooks_dir) / hook_type
        jobs.append((dest, "multiplexer", mux.url, mux.version, "src/multiplexer"))

    written: list[Path] = []
    try:
        if force:
            clear_generated_scripts(dest_dir)

        for dest, name, url, version, blob_path in jobs:
            report.start(_install_label(report, name, url, version, _display_path(repo_root, dest)))
            ref = resolve_version(url, version)
            blob = fetch_blob(url, ref, blob_path)
            write_executable(dest, blob)
            written.append(dest)
            report.succeed()
    except OSError as exc:
        report.fail(str(exc))
        _rollback(written)
        raise InstallError(f"Failed to write hooks: {exc}") from exc
    except git_mod.GitError as exc:
        report.fail(str(exc))
        _rollback(written)
        raise

    if not skip_gitignore:
        ensure_gitignore(repo_root)
