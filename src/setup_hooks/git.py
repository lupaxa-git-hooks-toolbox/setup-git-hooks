from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from setup_hooks.config import VersionSpec, parse_version

SYMREF_HEAD = re.compile(r"^ref:\s+refs/heads/(\S+)\s+HEAD\b", re.MULTILINE)
SEMVER_TAG = re.compile(
    r"^(?:v|V)?\d+\.\d+\.\d+"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


class GitError(Exception):
    """Not a work tree, or resolve/fetch failed."""


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def work_tree_root(cwd: Path | None = None) -> Path:
    if cwd is not None and not cwd.is_dir():
        raise GitError("Not a git repository (or any of the parent directories).")
    result = _run(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    if result.returncode != 0:
        raise GitError("Not a git repository (or any of the parent directories).")
    return Path(result.stdout.strip()).resolve()


def git_hooks_dir(cwd: Path | None = None) -> Path:
    result = _run(["git", "rev-parse", "--git-path", "hooks"], cwd=cwd)
    if result.returncode != 0:
        raise GitError("Could not resolve the git hooks directory.")
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        base = cwd if cwd is not None else Path.cwd()
        path = base / path
    return path.resolve()


def core_hooks_path(cwd: Path | None = None) -> str | None:
    result = _run(["git", "config", "--get", "core.hooksPath"], cwd=cwd)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _ls_remote(url: str, *extra: str) -> str:
    result = _run(["git", "ls-remote", *extra, url])
    if result.returncode != 0:
        raise GitError(f"Failed to list refs from {url}: {result.stderr.strip()}")
    return result.stdout


def _default_branch(url: str) -> str:
    result = _run(["git", "ls-remote", "--symref", url, "HEAD"])
    if result.returncode != 0:
        raise GitError(f"Failed to resolve HEAD from {url}: {result.stderr.strip()}")
    match = SYMREF_HEAD.search(result.stdout)
    if match:
        return match.group(1)
    raise GitError(f"Could not resolve default branch for {url}.")


def _latest_semver_tag(url: str) -> str:
    output = _ls_remote(url, "--tags")
    tags: list[str] = []
    for line in output.splitlines():
        if not line.strip() or "\t" not in line:
            continue
        ref = line.split("\t", 1)[1]
        if ref.endswith("^{}"):
            continue
        if not ref.startswith("refs/tags/"):
            continue
        tag = ref.removeprefix("refs/tags/")
        if SEMVER_TAG.fullmatch(tag):
            tags.append(tag)
    if not tags:
        raise GitError(f"No semver tags found at {url}.")
    tags.sort(key=_semver_key)
    return tags[-1]


_IDENT_SPLIT = re.compile(r"(\d+)")
IdentKey = tuple[tuple[int, int | str], ...]
SemverKey = tuple[int, int, int, int, tuple[IdentKey, ...]]


def _prerelease_ident_key(ident: str) -> IdentKey:
    parts: list[tuple[int, int | str]] = []
    for piece in _IDENT_SPLIT.split(ident):
        if piece == "":
            continue
        if piece.isdigit():
            parts.append((0, int(piece)))
        else:
            parts.append((1, piece))
    return tuple(parts)


def _semver_key(tag: str) -> SemverKey:
    body = tag[1:] if tag[:1] in {"v", "V"} else tag
    body = body.split("+", 1)[0]
    core, _, pre = body.partition("-")
    major, minor, patch = (int(part) for part in core.split(".")[:3])
    if not pre:
        return (major, minor, patch, 1, ())
    idents = tuple(_prerelease_ident_key(part) for part in pre.split("."))
    return (major, minor, patch, 0, idents)


def _tag_exists(url: str, tag: str) -> bool:
    output = _ls_remote(url, "--tags")
    wanted = {f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"}
    for line in output.splitlines():
        if "\t" not in line:
            continue
        ref = line.split("\t", 1)[1]
        if ref in wanted or ref.removeprefix("refs/tags/") == tag:
            return True
    return False


def resolve_version(url: str, version: str) -> str:
    spec: VersionSpec = parse_version(version)
    if spec.kind == "head":
        return _default_branch(url)
    if spec.kind == "latest":
        return _latest_semver_tag(url)
    if spec.kind == "tag":
        if not _tag_exists(url, spec.value):
            raise GitError(f"Tag {spec.value} not found at {url}.")
        return spec.value
    return spec.value


def fetch_blob(url: str, ref: str, blob_path: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="setup-hooks-") as tmp:
        git_dir = Path(tmp) / "fetch.git"
        init = _run(["git", "init", "--bare", str(git_dir)])
        if init.returncode != 0:
            raise GitError(f"Failed to create temp git dir: {init.stderr.strip()}")

        def show(spec: str) -> bytes | None:
            shown = subprocess.run(
                ["git", "--git-dir", str(git_dir), "show", spec],
                capture_output=True,
                check=False,
            )
            if shown.returncode != 0:
                return None
            return shown.stdout

        for fetch_args in (
            ["git", "--git-dir", str(git_dir), "fetch", "--depth", "1", url, ref],
            ["git", "--git-dir", str(git_dir), "fetch", url, ref],
        ):
            fetched = _run(fetch_args)
            if fetched.returncode == 0:
                content = show(f"FETCH_HEAD:{blob_path}")
                if content is None:
                    raise GitError(f"Missing {blob_path} at {ref} in {url}.")
                return content

        fetched = _run(["git", "--git-dir", str(git_dir), "fetch", url, "HEAD"])
        if fetched.returncode != 0:
            raise GitError(f"Failed to fetch {ref} from {url}: {fetched.stderr.strip()}")
        content = show(f"{ref}:{blob_path}")
        if content is None:
            raise GitError(f"Missing {blob_path} at {ref} in {url}.")
        return content
