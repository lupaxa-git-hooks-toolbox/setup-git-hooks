from __future__ import annotations

import io
import time

from setup_hooks.progress import CYAN, FRAMES, GREEN, RED, RESET, YELLOW, Progress


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


def _visible_lines(output: str) -> list[str]:
    lines: list[str] = []
    for raw in output.split("\n"):
        if "\r" in raw:
            raw = raw.split("\r")[-1]
        if raw:
            lines.append(raw)
    return lines


def test_progress_rewrites_installing_to_installed_on_same_line() -> None:
    stream = io.StringIO()
    progress = Progress(stream, use_spinner=False, use_color=False)
    progress.start("Installing Demo -> hooks/pre-commit/01-demo")
    progress.succeed()
    progress.close()
    output = stream.getvalue()
    assert output.count("\n") == 1
    assert "Installing Demo -> hooks/pre-commit/01-demo" in output
    assert _visible_lines(output) == ["Installed Demo -> hooks/pre-commit/01-demo"]


def test_progress_each_hook_stays_on_one_line() -> None:
    stream = io.StringIO()
    progress = Progress(stream, use_spinner=False, use_color=False)
    progress.start("Installing Demo -> hooks/pre-commit/01-demo")
    progress.succeed()
    progress.start("Installing multiplexer -> .git/hooks/pre-commit")
    progress.succeed()
    progress.close()
    output = stream.getvalue()
    assert output.count("\n") == 2
    assert _visible_lines(output) == [
        "Installed Demo -> hooks/pre-commit/01-demo",
        "Installed multiplexer -> .git/hooks/pre-commit",
    ]


def test_progress_fail_rewrites_installing_on_same_line() -> None:
    stream = io.StringIO()
    progress = Progress(stream, use_spinner=False, use_color=False)
    progress.start("Installing Demo -> hooks/pre-commit/01-demo")
    progress.fail("Missing src/pre-commit")
    output = stream.getvalue()
    assert progress.failed
    assert output.count("\n") == 1
    assert "Installed" not in output
    assert "Failed Demo -> hooks/pre-commit/01-demo: Missing src/pre-commit" in output


def test_progress_disabled_prints_nothing() -> None:
    stream = io.StringIO()
    progress = Progress(stream, enabled=False)
    progress.start("Installing Demo -> hooks/pre-commit/01-demo")
    progress.succeed()
    progress.info("Replacing generated scripts in hooks/pre-commit.")
    progress.close()
    assert stream.getvalue() == ""


def test_progress_tty_spinner_is_cyan_text_yellow_then_green() -> None:
    stream = _Tty()
    progress = Progress(stream, use_spinner=True, use_color=True, interval=0.02)
    progress.start("Installing Demo -> hooks/pre-commit/01-demo")
    time.sleep(0.06)
    progress.succeed()
    progress.close()
    output = stream.getvalue()
    assert any(frame in output for frame in FRAMES)
    assert f"{CYAN}" in output
    assert f"{YELLOW}" in output
    assert f"{GREEN}" in output
    assert f"{RESET}" in output
    assert "Installed Demo -> hooks/pre-commit/01-demo" in output


def test_progress_tty_fail_is_red() -> None:
    stream = _Tty()
    progress = Progress(stream, use_spinner=True, use_color=True, interval=0.02)
    progress.start("Installing Demo -> hooks/pre-commit/01-demo")
    time.sleep(0.05)
    progress.fail("Missing src/pre-commit")
    output = stream.getvalue()
    assert f"{RED}" in output
    assert "Failed Demo -> hooks/pre-commit/01-demo: Missing src/pre-commit" in output
    assert "Installed" not in output
