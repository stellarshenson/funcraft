"""Stub engines and a stub renderer for the unit suite: no GPU, no model, no ffmpeg."""
import threading
import time
from pathlib import Path

import numpy as np

from engine import LoadReport


class StubEngine:
    """An engine with one voice that returns one second of silence and records each request.

    `delay` makes `speak` take that many seconds, so a test can observe what runs at the same time;
    `fail` makes `speak` raise that exception, so a test can exercise the error paths.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.spoken: list[tuple[str, str]] = []
        self.loads = 0
        self.unloads = 0
        self.delay = 0.0
        self.fail: Exception | None = None
        self.active = 0
        self.max_active = 0
        self._active_lock = threading.Lock()

    def load(self, report: LoadReport | None = None) -> None:
        self.loads += 1

    def unload(self) -> None:
        self.unloads += 1

    def speak(self, text: str, voice: str) -> tuple[np.ndarray, int]:
        """Return one second of silence, waiting `delay` seconds and raising `fail` when set."""
        with self._active_lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if self.delay:
                time.sleep(self.delay)
            if self.fail is not None:
                raise self.fail
            self.spoken.append((text, voice))
            return np.zeros(16000, dtype=np.float32), 16000
        finally:
            with self._active_lock:
                self.active -= 1

    def voices(self) -> list[str]:
        return ["grimaldus"]


def fake_render(path: Path, audio: np.ndarray, rate: int) -> Path:
    """Stand-in for `audio_out.write_render`: writes a placeholder file instead of an MP3."""
    path.write_bytes(b"ID3")
    return path
