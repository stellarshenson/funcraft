"""The interface every text-to-speech model implements to be served, its error and its voice-folder rule.

An engine is a model that can do five things: `load()`, `unload()`, `speak(text, voice) -> (samples, rate)`,
`voices()`, and a `name`. Where the model runs is the engine's own business: in this interpreter (S2 Pro) or
in a child process with another Python environment (AuK-Flash).
"""
from pathlib import Path
from typing import Callable, Protocol

import numpy as np

LoadReport = Callable[[str], None]
"""Receives each load phase: "downloading" while the weights are fetched, "loading" while the model is built."""


class EngineError(RuntimeError):
    """An engine could not be loaded or could not speak; the API reports it as a 5xx."""


class Engine(Protocol):
    """One text-to-speech model, by the five calls the service makes."""

    name: str

    def load(self, report: LoadReport | None = None) -> None:
        """Load the model into memory.

        Args:
            report: receives the phase changes; a load from the local cache reports "loading", a load that
                fetches the weights first reports "downloading" then "loading".
        """

    def unload(self) -> None:
        """Free the model's memory; safe to call when not loaded."""

    def speak(self, text: str, voice: str) -> tuple[np.ndarray, int]:
        """Speak `text` in `voice`; returns mono float32 samples and their sample rate in Hz."""

    def voices(self) -> list[str]:
        """The voices this engine can speak."""


def voice_names(voices_dir: Path) -> list[str]:
    """The voices in a folder: `<name>.wav` with a `<name>.txt` transcript beside it.

    Args:
        voices_dir: folder that holds the voice pairs.

    Returns:
        The names, sorted.
    """
    folder = Path(voices_dir)
    return sorted(p.stem for p in folder.glob("*.wav") if p.with_suffix(".txt").exists())
