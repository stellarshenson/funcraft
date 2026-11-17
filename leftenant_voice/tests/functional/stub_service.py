"""The service with stub engines, for the browser test of the page: the unit suite's stub speech engines named s2pro
and auk-flash, a stub transcriber, a stubbed Hugging Face whoami (a token starting hf_valid belongs to "voice-owner",
every other token is refused as the hub refuses it), and throwaway voice, token and Hugging Face folders whose model
caches are sparse files, so Delete on a model touches nothing real. No GPU, no model, no network.

Usage: python stub_service.py PORT [FOLDER]; FOLDER holds the throwaway folders, a new temporary folder without it.
The password is S2PRO_PASSWORD, else "test-password". ffmpeg must be on PATH.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

P = Path(__file__).resolve().parents[2]
ROOT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.mkdtemp(prefix="voice-stub-service-"))
os.environ.setdefault("S2PRO_PASSWORD", "test-password")
os.environ.update(TOKENS_FILE=str(ROOT / "tokens.json"), VOICES_DIR=str(ROOT / "voices"),
                  SEED_VOICES_DIR=str(P / "service/voices"), HF_HOME=str(ROOT / "huggingface"), ENGINE="s2pro")
os.environ.pop("HF_TOKEN", None)
sys.path[:0] = [str(P / "service"), str(P / "tests/unit"), str(P / "src/fish"), str(P / "src")]

import app  # noqa: E402
import httpx  # noqa: E402
import models  # noqa: E402
import uvicorn  # noqa: E402
from engine import voice_names  # noqa: E402
from stubs import StubEngine  # noqa: E402

CACHE_BYTES = {"s2pro": int(11.0 * 1024**3), "nemotron": int(67.5 * 1024**3)}
TRANSCRIPT = "Brothers, we stand upon the wall and we do not yield."


def fake_cache(name: str) -> None:
    """A model cache whose one weight file is sparse: `GET /models` reports the real size, the disk holds nothing."""
    folder = models.cache_dir(name) / "snapshots/main"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "model.safetensors").open("wb") as file:
        file.truncate(CACHE_BYTES[name])


class ToneEngine(StubEngine):
    """The unit suite's stub engine over the voice folder, speaking a 3 s tone that swells and fades, so the page has
    a waveform to draw."""

    def voices(self) -> list[str]:
        return voice_names(app.VOICES_DIR)

    def speak(self, text: str, voice: str) -> tuple[np.ndarray, int]:
        super().speak(text, voice)
        rate = 16000
        seconds = np.arange(3 * rate) / rate
        return (0.3 * np.sin(2 * np.pi * 220 * seconds) * np.abs(np.sin(2 * np.pi * 0.9 * seconds))).astype(np.float32), rate


class StubTranscriber:
    """Stand-in for NemotronTranscriber: its load takes `load_seconds` and writes the model cache, as a download
    does; every window reads TRANSCRIPT."""

    def __init__(self) -> None:
        self.loaded = False
        self.load_seconds = 0.0

    def available(self) -> bool:
        return True

    def python_path(self) -> str:
        return "stub"

    def is_loaded(self) -> bool:
        return self.loaded

    def load(self, report=None) -> None:
        time.sleep(self.load_seconds)
        fake_cache("nemotron")
        self.loaded = True

    def unload(self) -> None:
        self.loaded = False

    def transcribe_window(self, samples: np.ndarray, prompt: str) -> str:
        return TRANSCRIPT


def whoami(token: str) -> dict:
    """Hugging Face whoami as the hub answers: a token starting hf_valid belongs to voice-owner, any other is 401."""
    if token.startswith("hf_valid"):
        return {"name": "voice-owner", "type": "user"}
    request = httpx.Request("GET", app.WHOAMI_URL)
    response = httpx.Response(401, json={"error": "Invalid credentials in Authorization header"}, request=request)
    raise httpx.HTTPStatusError("401 Unauthorized", request=request, response=response)


for model in CACHE_BYTES:
    fake_cache(model)
engine = ToneEngine("s2pro")
transcriber = StubTranscriber()
app.ENGINES = {"s2pro": engine, "auk-flash": ToneEngine("auk-flash")}
app.DEFAULT_ENGINE = "s2pro"
app.transcriber = transcriber
app.whoami = whoami

if __name__ == "__main__":
    uvicorn.run(app.app, host="127.0.0.1", port=int(sys.argv[1]), log_level="warning")
