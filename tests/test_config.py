from __future__ import annotations

from pathlib import Path

import pytest

from setup_hooks.config import (
    ConfigError,
    discover_hook_types,
    installed_basename,
    load_hook_type_config,
    load_multiplexer_config,
    parse_version,
)


def test_parse_version_head_and_latest() -> None:
    head = parse_version("HEAD")
    assert head.kind == "head"
    assert parse_version("head").kind == "head"
    assert parse_version("LATEST").kind == "latest"
    assert parse_version("latest").kind == "latest"


def test_parse_version_semver_and_sha() -> None:
    tag = parse_version("v1.2.0")
    assert tag.kind == "tag"
    assert tag.value == "v1.2.0"
    assert parse_version("1.0.0").kind == "tag"
    sha = "0123456789abcdef0123456789abcdef01234567"
    spec = parse_version(sha)
    assert spec.kind == "sha"
    assert spec.value == sha


def test_parse_version_rejects_short_sha_and_junk() -> None:
    with pytest.raises(ConfigError, match="short"):
        parse_version("0123456")
    with pytest.raises(ConfigError, match="version"):
        parse_version("main")
    with pytest.raises(ConfigError, match="version"):
        parse_version("")


def test_installed_basename_and_limit() -> None:
    assert installed_basename(1, "ruff") == "01-ruff"
    assert installed_basename(12, "confirm_default_branch") == "12-confirm_default_branch"
    with pytest.raises(ConfigError, match="99"):
        installed_basename(100, "ruff")
    with pytest.raises(ConfigError, match="index"):
        installed_basename(0, "ruff")


def test_load_hook_type_config_ok(tmp_path: Path) -> None:
    path = tmp_path / "pre-commit-config.yml"
    path.write_text(
        "- name: Ruff\n"
        "  filename: ruff\n"
        "  url: https://example.test/ruff\n"
        "  version: LATEST\n"
        "- name: Confirm\n"
        "  filename: confirm_default_branch\n"
        "  url: https://example.test/confirm\n"
        "  version: v1.2.0\n",
        encoding="utf-8",
    )
    entries = load_hook_type_config(path)
    assert [item.filename for item in entries] == ["ruff", "confirm_default_branch"]
    assert installed_basename(1, entries[0].filename) == "01-ruff"
    assert installed_basename(2, entries[1].filename) == "02-confirm_default_branch"


def test_load_hook_type_config_rejects_bad_filename_and_duplicates(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text(
        "- name: X\n  filename: ../x\n  url: https://example.test/x\n  version: HEAD\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="filename"):
        load_hook_type_config(bad)
    dup = tmp_path / "dup.yml"
    dup.write_text(
        "- name: A\n  filename: ruff\n  url: https://example.test/a\n  version: HEAD\n"
        "- name: B\n  filename: ruff\n  url: https://example.test/b\n  version: HEAD\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="(?i)duplicate"):
        load_hook_type_config(dup)


def test_load_hook_type_config_rejects_missing_keys_and_too_many(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yml"
    missing.write_text(
        "- name: X\n  url: https://example.test/x\n  version: HEAD\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="filename"):
        load_hook_type_config(missing)
    lines = [
        f"- name: H{i}\n  filename: f{i}\n  url: https://example.test/{i}\n  version: HEAD\n"
        for i in range(100)
    ]
    many = tmp_path / "many.yml"
    many.write_text("".join(lines), encoding="utf-8")
    with pytest.raises(ConfigError, match="99"):
        load_hook_type_config(many)


def test_load_multiplexer_config(tmp_path: Path) -> None:
    path = tmp_path / "multiplexer-config.yml"
    path.write_text(
        "url: https://example.test/mux\nversion: LATEST\n",
        encoding="utf-8",
    )
    cfg = load_multiplexer_config(path)
    assert cfg.url == "https://example.test/mux"
    assert cfg.version == "LATEST"
    with pytest.raises(ConfigError, match="mapping"):
        other = tmp_path / "list.yml"
        other.write_text("- url: https://example.test/mux\n  version: HEAD\n", encoding="utf-8")
        load_multiplexer_config(other)


def test_discover_hook_types(tmp_path: Path) -> None:
    (tmp_path / "pre-commit-config.yml").write_text("[]\n", encoding="utf-8")
    (tmp_path / "commit-msg-config.yml").write_text("[]\n", encoding="utf-8")
    (tmp_path / "multiplexer-config.yml").write_text("url: x\nversion: HEAD\n", encoding="utf-8")
    (tmp_path / "notes.yml").write_text("nope\n", encoding="utf-8")
    assert discover_hook_types(tmp_path) == ["commit-msg", "pre-commit"]
