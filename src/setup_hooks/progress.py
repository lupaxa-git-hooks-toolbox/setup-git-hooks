from __future__ import annotations

import itertools
import os
import re
import sys
import threading
from typing import TextIO

FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"
ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def visible_len(text: str) -> int:
    return len(ANSI_RE.sub("", text))


class Progress:
    """In-place stderr progress: cyan spinner, yellow while running, green/red when done."""

    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        verbose: bool = False,
        use_spinner: bool | None = None,
        use_color: bool | None = None,
        enabled: bool = True,
        interval: float = 0.08,
    ) -> None:
        self.stream = sys.stderr if stream is None else stream
        self.verbose = verbose
        self.enabled = enabled
        self.failed = False
        tty = self.stream.isatty()
        if use_spinner is None:
            self.use_spinner = enabled and tty
        else:
            self.use_spinner = enabled and use_spinner
        if use_color is None:
            self.use_color = enabled and tty and "NO_COLOR" not in os.environ
        else:
            self.use_color = enabled and use_color
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._message = ""
        self._width = 0
        self._lock = threading.Lock()

    def start(self, message: str) -> None:
        if not self.enabled:
            return
        self._halt_spinner()
        self._message = message
        if self.use_spinner:
            self._stop.clear()
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        else:
            self._paint(self._style(message, YELLOW))

    def succeed(self, message: str | None = None) -> None:
        if not self.enabled:
            return
        self._halt_spinner()
        text = message if message is not None else self._swap_verb("Installed")
        self._finish(self._style(text, GREEN))

    def fail(self, reason: str = "") -> None:
        self.failed = True
        if not self.enabled:
            return
        self._halt_spinner()
        if self._message:
            text = self._swap_verb("Failed")
            if reason:
                text = f"{text}: {reason}"
        else:
            text = reason or "Failed"
        self._finish(self._style(text, RED))

    def info(self, message: str) -> None:
        if not self.enabled:
            return
        self._halt_spinner()
        self._finish(message)

    def close(self) -> None:
        self._halt_spinner()
        if self.enabled and self._message:
            self._finish(self._style(self._message, YELLOW))

    def _swap_verb(self, verb: str) -> str:
        if self._message.startswith("Installing "):
            return verb + self._message[len("Installing") :]
        return self._message or verb

    def _style(self, text: str, code: str) -> str:
        if not self.use_color:
            return text
        return f"{code}{text}{RESET}"

    def _spin(self) -> None:
        for frame in itertools.cycle(FRAMES):
            with self._lock:
                if self._stop.is_set():
                    return
                painted = f"{self._style(frame, CYAN)} {self._style(self._message, YELLOW)}"
                self._paint(painted)
            if self._stop.wait(self.interval):
                return

    def _halt_spinner(self) -> None:
        self._stop.set()
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=1.0)

    def _paint(self, text: str) -> None:
        pad = max(0, self._width - visible_len(text))
        clear = "\033[K" if self.use_spinner else ""
        self.stream.write(f"\r{text}{' ' * pad}{clear}")
        self.stream.flush()
        self._width = visible_len(text)

    def _finish(self, text: str) -> None:
        with self._lock:
            if self.use_spinner:
                pad = max(0, self._width - visible_len(text))
                self.stream.write(f"\r{text}{' ' * pad}\033[K\n")
            else:
                self.stream.write(f"\r{text}\n")
            self.stream.flush()
            self._width = 0
            self._message = ""
