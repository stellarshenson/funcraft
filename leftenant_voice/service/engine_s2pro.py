"""S2 Pro as an in-process engine over src/fish/speak_s2pro.py.

The weights live in the Hugging Face cache at HF_HOME (`~/.cache/huggingface`, or `/root/.cache/huggingface`
in the image, where a named volume holds it). A load whose cache lacks the pinned snapshot downloads it from
Hugging Face first and reports "downloading"; a load that finds the snapshot reports "loading" only.
"""
import gc
import time
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from huggingface_hub import snapshot_download
from huggingface_hub.errors import LocalEntryNotFoundError

from engine import EngineError, LoadReport, voice_names
from speak_s2pro import MODEL, REVISION, S2ProSpeaker


class S2ProEngine:
    """Fish Audio S2 Pro in the service's own interpreter, loaded once per residency."""

    name = "s2pro"

    def __init__(self, voices_dir: Path, token: Callable[[], str | None] = lambda: None) -> None:
        """Remember the voice folder and the token source; the model loads in `load()`.

        Args:
            voices_dir: folder of `<voice>.wav` + `<voice>.txt` pairs.
            token: returns the Hugging Face token to download with, or None for huggingface_hub's own default;
                read at load time, so a token set through the page is used without a restart.
        """
        self.voices_dir = Path(voices_dir)
        self.token = token
        self._speaker: S2ProSpeaker | None = None

    def load(self, report: LoadReport | None = None) -> None:
        """Load the pinned model and codec, downloading the weights when the cache lacks them.

        Args:
            report: receives "downloading" before the weights are fetched and "loading" before the model is built.

        Raises:
            EngineError: the weights could not be downloaded, or the model did not load.
        """
        if self._speaker is not None:
            return
        report = report or (lambda _: None)
        try:
            try:
                snapshot_download(MODEL, revision=REVISION, local_files_only=True, token=self.token())
            except LocalEntryNotFoundError:
                report("downloading")
                start = time.time()
                print(f"s2pro: downloading {MODEL} revision {REVISION} from Hugging Face", flush=True)
                snapshot_download(MODEL, revision=REVISION, token=self.token())
                print(f"s2pro: download finished in {time.time() - start:.0f} s", flush=True)
            report("loading")
            self._speaker = S2ProSpeaker(self.voices_dir)
        except Exception as error:
            raise EngineError(f"the s2pro model could not be loaded: {error}") from error

    def unload(self) -> None:
        """Drop the model and return its GPU memory to the driver."""
        if self._speaker is not None:
            self._speaker = None
            gc.collect()
            torch.cuda.empty_cache()

    def speak(self, text: str, voice: str) -> tuple[np.ndarray, int]:
        """Speak the text; the samples are mono float32 at the codec's rate.

        Raises:
            ValueError: unknown voice or a text with no words.
        """
        return self._speaker.speak(text, voice), self._speaker.rate

    def voices(self) -> list[str]:
        """The voices in the shared voices folder."""
        return voice_names(self.voices_dir)
