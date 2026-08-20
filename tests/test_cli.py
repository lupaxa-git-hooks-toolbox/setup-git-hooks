from __future__ import annotations

from pathlib import Path

from setup_hooks.cli import main
from setup_hooks.gitignore import GITIGNORE_RULE, GITIGNORE_SNIPPET, GitignoreError
from tests.helpers import commit_file, init_repo, run_git


def _upstream(tmp_path: Path, name: str, blob_path: str, body: str) -> Path:
    repo = init_repo(tmp_path / name)
    commit_file(repo, blob_path, body, "add")
    return repo


def _consumer(tmp_path: Path, hook_url: Path, mux_url: Path) -> Path:
    repo = init_repo(tmp_path / "consumer")
    hooks = repo / "hooks"
    hooks.mkdir()
    (hooks / "pre-commit-config.yml").write_text(
        f"- name: Demo\n  filename: demo\n  url: {hook_url}\n  version: HEAD\n",
        encoding="utf-8",
    )
    (hooks / "multiplexer-config.yml").write_text(
        f"url: {mux_url}\nversion: HEAD\n",
        encoding="utf-8",
    )
    return repo


def test_cli_first_install_and_list(tmp_path: Path, monkeypatch, capsys) -> None:
    hook = _upstream(tmp_path, "hook", "src/pre-commit", "#!/bin/sh\nexit 0\n")
    mux = _upstream(tmp_path, "mux", "src/multiplexer", "#!/bin/sh\necho mux\n")
    repo = _consumer(tmp_path, hook, mux)
    monkeypatch.chdir(repo)
    assert main([]) == 0
    script = repo / "hooks" / "pre-commit" / "01-demo"
    assert script.read_text(encoding="utf-8") == "#!/bin/sh\nexit 0\n"
    assert script.stat().st_mode & 0o111
    assert (repo / ".git" / "hooks" / "pre-commit").is_file()
    assert GITIGNORE_RULE in (repo / ".gitignore").read_text(encoding="utf-8")
    err = capsys.readouterr().err
    assert "Installing Demo -> hooks/pre-commit/01-demo" in err
    assert "Installed Demo -> hooks/pre-commit/01-demo" in err
    assert "Installing multiplexer -> .git/hooks/pre-commit" in err
    assert "Installed multiplexer -> .git/hooks/pre-commit" in err
    assert main(["--list-hook-types"]) == 0


def test_cli_rerun_needs_force(tmp_path: Path, monkeypatch, capsys) -> None:
    hook = _upstream(tmp_path, "hook", "src/pre-commit", "one\n")
    mux = _upstream(tmp_path, "mux", "src/multiplexer", "mux\n")
    repo = _consumer(tmp_path, hook, mux)
    monkeypatch.chdir(repo)
    assert main([]) == 0
    assert main([]) != 0
    assert (repo / "hooks" / "pre-commit" / "01-demo").read_text(encoding="utf-8") == "one\n"
    run_git(["rm", "-f", "src/pre-commit"], cwd=hook)
    commit_file(hook, "src/pre-commit", "two\n", "update")
    capsys.readouterr()
    assert main(["--force"]) == 0
    assert (repo / "hooks" / "pre-commit" / "01-demo").read_text(encoding="utf-8") == "two\n"
    assert (repo / "hooks" / "pre-commit-config.yml").exists()
    err = capsys.readouterr().err
    assert "Replacing generated scripts in hooks/pre-commit." in err
    assert "Installing Demo -> hooks/pre-commit/01-demo" in err
    assert "Installed Demo -> hooks/pre-commit/01-demo" in err


def test_cli_skip_flags_and_missing_mux(tmp_path: Path, monkeypatch, capsys) -> None:
    hook = _upstream(tmp_path, "hook", "src/pre-commit", "hook\n")
    mux = _upstream(tmp_path, "mux", "src/multiplexer", "mux\n")
    repo = _consumer(tmp_path, hook, mux)
    (repo / "hooks" / "multiplexer-config.yml").unlink()
    monkeypatch.chdir(repo)
    assert main([]) != 0
    capsys.readouterr()
    assert main(["--skip-multiplexer", "--skip-gitignore"]) == 0
    err = capsys.readouterr().err
    assert "Installing Demo -> hooks/pre-commit/01-demo" in err
    assert "Installed Demo -> hooks/pre-commit/01-demo" in err
    assert "Installing multiplexer" not in err
    assert not (repo / ".git" / "hooks" / "pre-commit").exists()
    assert not (repo / ".gitignore").exists() or GITIGNORE_RULE not in (
        (repo / ".gitignore").read_text(encoding="utf-8") if (repo / ".gitignore").exists() else ""
    )


def test_cli_discovers_two_types(tmp_path: Path, monkeypatch) -> None:
    hook = _upstream(tmp_path, "hook", "src/pre-commit", "pc\n")
    commit_file(hook, "src/commit-msg", "cm\n", "commit-msg hook")
    mux = _upstream(tmp_path, "mux", "src/multiplexer", "mux\n")
    repo = _consumer(tmp_path, hook, mux)
    (repo / "hooks" / "commit-msg-config.yml").write_text(
        f"- name: Msg\n  filename: msg\n  url: {hook}\n  version: HEAD\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)
    assert main([]) == 0
    assert (repo / "hooks" / "pre-commit" / "01-demo").read_text(encoding="utf-8") == "pc\n"
    assert (repo / "hooks" / "commit-msg" / "01-msg").read_text(encoding="utf-8") == "cm\n"


def test_cli_missing_blob_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    hook = _upstream(tmp_path, "hook", "src/other", "nope\n")
    mux = _upstream(tmp_path, "mux", "src/multiplexer", "mux\n")
    repo = _consumer(tmp_path, hook, mux)
    monkeypatch.chdir(repo)
    assert main(["--skip-multiplexer", "--skip-gitignore"]) != 0
    err = capsys.readouterr().err
    assert "Installing Demo -> hooks/pre-commit/01-demo" in err
    assert "Installed Demo" not in err
    assert "Failed Demo -> hooks/pre-commit/01-demo" in err


def test_cli_verbose_includes_source_url(tmp_path: Path, monkeypatch, capsys) -> None:
    hook = _upstream(tmp_path, "hook", "src/pre-commit", "hook\n")
    mux = _upstream(tmp_path, "mux", "src/multiplexer", "mux\n")
    repo = _consumer(tmp_path, hook, mux)
    monkeypatch.chdir(repo)
    assert main(["-v", "--skip-multiplexer", "--skip-gitignore"]) == 0
    err = capsys.readouterr().err
    assert f"Installing Demo from {hook} (HEAD) -> hooks/pre-commit/01-demo" in err
    assert f"Installed Demo from {hook} (HEAD) -> hooks/pre-commit/01-demo" in err


def test_cli_gitignore_error_prints_snippet(tmp_path: Path, monkeypatch, capsys) -> None:
    hook = _upstream(tmp_path, "hook", "src/pre-commit", "hook\n")
    mux = _upstream(tmp_path, "mux", "src/multiplexer", "mux\n")
    repo = _consumer(tmp_path, hook, mux)
    monkeypatch.chdir(repo)

    def boom(_root: Path) -> None:
        raise GitignoreError("cannot write gitignore")

    monkeypatch.setattr("setup_hooks.cli.ensure_gitignore", boom)
    assert main([]) == 0
    err = capsys.readouterr().err
    assert "cannot write gitignore" in err
    assert "Add this to .gitignore:" in err
    assert GITIGNORE_SNIPPET in err
