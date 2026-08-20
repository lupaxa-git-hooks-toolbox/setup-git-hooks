from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
SHORT_SHA_RE = re.compile(r"^[0-9a-fA-F]{4,39}$")
SEMVER_RE = re.compile(
    r"^(?:v|V)?(\d+)\.(\d+)\.(\d+)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
CONFIG_SUFFIX = "-config.yml"
MULTIPLEXER_STEM = "multiplexer"


class ConfigError(Exception):
    """Invalid consumer YAML or version grammar."""


@dataclass(frozen=True)
class HookEntry:
    name: str
    filename: str
    url: str
    version: str


@dataclass(frozen=True)
class MultiplexerConfig:
    url: str
    version: str


@dataclass(frozen=True)
class VersionSpec:
    kind: Literal["head", "latest", "tag", "sha"]
    raw: str
    value: str


def parse_version(version: str) -> VersionSpec:
    raw = version.strip() if isinstance(version, str) else ""
    if not raw:
        raise ConfigError("Invalid version: empty.")
    if raw.upper() == "HEAD":
        return VersionSpec("head", raw, "")
    if raw.upper() == "LATEST":
        return VersionSpec("latest", raw, "")
    if SHA_RE.fullmatch(raw):
        return VersionSpec("sha", raw, raw)
    if SHORT_SHA_RE.fullmatch(raw):
        raise ConfigError("Invalid version: short SHA rejected; use a full 40-char SHA.")
    if SEMVER_RE.fullmatch(raw):
        return VersionSpec("tag", raw, raw)
    raise ConfigError(f"Invalid version: {raw!r}.")


def installed_basename(index: int, filename: str) -> str:
    if index < 1:
        raise ConfigError(f"Invalid index: {index}.")
    if index > 99:
        raise ConfigError("A hook type config cannot have more than 99 entries.")
    return f"{index:02d}-{filename}"


def _require_str(data: dict[str, Any], key: str, where: str) -> str:
    if key not in data:
        raise ConfigError(f"Missing {key} in {where}.")
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Missing {key} in {where}.")
    return value.strip()


def load_hook_type_config(path: Path) -> list[HookEntry]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc
    if loaded is None:
        loaded = []
    if not isinstance(loaded, list):
        raise ConfigError(f"{path} must be a YAML list.")
    if len(loaded) > 99:
        raise ConfigError("A hook type config cannot have more than 99 entries.")
    entries: list[HookEntry] = []
    seen: set[str] = set()
    for offset, item in enumerate(loaded, start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"Entry {offset} in {path} must be a mapping.")
        name = _require_str(item, "name", f"entry {offset} of {path}")
        filename = _require_str(item, "filename", f"entry {offset} of {path}")
        url = _require_str(item, "url", f"entry {offset} of {path}")
        version = _require_str(item, "version", f"entry {offset} of {path}")
        if not FILENAME_RE.fullmatch(filename):
            raise ConfigError(f"Invalid filename {filename!r} in {path}.")
        if filename in seen:
            raise ConfigError(f"Duplicate filename {filename!r} in {path}.")
        parse_version(version)
        seen.add(filename)
        entries.append(HookEntry(name=name, filename=filename, url=url, version=version))
    return entries


def load_multiplexer_config(path: Path) -> MultiplexerConfig:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} must be a YAML mapping.")
    url = _require_str(loaded, "url", str(path))
    version = _require_str(loaded, "version", str(path))
    parse_version(version)
    return MultiplexerConfig(url=url, version=version)


def hook_type_config_path(hooks_dir: Path, hook_type: str) -> Path:
    return hooks_dir / f"{hook_type}{CONFIG_SUFFIX}"


def multiplexer_config_path(hooks_dir: Path) -> Path:
    return hooks_dir / f"{MULTIPLEXER_STEM}{CONFIG_SUFFIX}"


def discover_hook_types(hooks_dir: Path) -> list[str]:
    if not hooks_dir.is_dir():
        return []
    names: list[str] = []
    for path in hooks_dir.iterdir():
        if not path.is_file() or not path.name.endswith(CONFIG_SUFFIX):
            continue
        stem = path.name[: -len(CONFIG_SUFFIX)]
        if stem == MULTIPLEXER_STEM or not stem:
            continue
        names.append(stem)
    return sorted(names)
