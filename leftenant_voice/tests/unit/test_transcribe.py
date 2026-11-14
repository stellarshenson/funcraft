"""Transcription: the model card's prompt, the window cut, and POST /transcribe with stubs.

No model, no GPU and no worker process. The unit suite carries no ffmpeg either, so `asr.decode_audio` is
replaced by a stand-in the way `stubs.fake_render` replaces the MP3 writer; the endpoint's decoding is
otherwise the service's own business.
"""
import io
import itertools
import time

import app
import asr
import models
import numpy as np
import pytest
import soundfile
from engine import EngineError
from fastapi.testclient import TestClient

SAMPLE_RATE = 16000


class FakeTranscriber:
    """Stand-in for NemotronTranscriber: records loads and windows, returns fixed text, starts no worker."""

    def __init__(self, available: bool = True) -> None:
        self._available = available
        self.loads = 0
        self.windows: list[tuple[np.ndarray, str]] = []
        self.load_error: Exception | None = None

    def available(self) -> bool:
        return self._available

    def is_loaded(self) -> bool:
        return self.loads > 0

    def load(self, report=None) -> None:
        if self.load_error is not None:
            raise self.load_error
        self.loads += 1

    def transcribe_window(self, samples: np.ndarray, prompt: str) -> str:
        self.windows.append((samples, prompt))
        return "hello world"


@pytest.fixture
def transcriber(client, monkeypatch):
    """The endpoint's transcriber, stubbed and ready, installed after the lifespan started."""
    fake = FakeTranscriber()
    monkeypatch.setattr(app, "transcriber", fake)
    monkeypatch.setattr(app, "asr_state", "ready")
    monkeypatch.setattr(app, "asr_error", None)
    return fake


def wait_for_asr(client: TestClient, wanted: str, timeout: float = 5.0) -> dict:
    """Poll /health until the transcriber's state reads `wanted` and return that body."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get("/health").json()
        if body["asr"]["state"] == wanted:
            return body
        time.sleep(0.05)
    raise AssertionError(f"/health never reported asr state {wanted!r}; last body {body}")


@pytest.fixture(autouse=True)
def decoding(monkeypatch):
    """Every test in this file decodes without ffmpeg."""

    def fake_decode(data: bytes) -> tuple[np.ndarray, int]:
        if not data.startswith(b"RIFF"):
            raise ValueError("the recording is not readable audio")
        return np.zeros(SAMPLE_RATE, dtype=np.float32), SAMPLE_RATE

    monkeypatch.setattr(asr, "decode_audio", fake_decode)


def wav_bytes(seconds: float = 1.0) -> bytes:
    """A PCM_16 WAV of `seconds` of a quiet tone, written into memory."""
    tone = 0.1 * np.sin(2 * np.pi * 220 * np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE)
    buffer = io.BytesIO()
    soundfile.write(buffer, tone, SAMPLE_RATE, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def upload(client: TestClient, data: bytes | None = None, **fields):
    """POST /transcribe with a one-second WAV and the given form fields."""
    return client.post("/transcribe", data=fields,
                       files={"file": ("recording.wav", wav_bytes() if data is None else data, "audio/wav")})


def test_the_prompt_is_the_cards_verbatim_text():
    assert asr.build_prompt("as spoken", "verbatim") == (
        "Audio transcription. Language: as spoken. Wording: verbatim, including fillers and repetitions. "
        "Formatting: punctuation and capitalization. Output: transcript only.")


def test_readable_wording_and_a_named_language():
    prompt = asr.build_prompt("German", "readable")
    assert "Language: German." in prompt
    assert ("Wording: omit fillers and accidental repetitions; keep the remaining spoken wording "
            "unchanged.") in prompt


def test_context_terms_are_appended():
    prompt = asr.build_prompt("English", "readable", "Grimaldus, Helsreach")
    assert prompt.endswith(" Output: transcript only. Context terms: Grimaldus, Helsreach.")


def test_an_unlisted_language_or_unknown_wording_raises():
    with pytest.raises(ValueError):
        asr.build_prompt("Norwegian", "readable")
    with pytest.raises(ValueError):
        asr.build_prompt("English", "poetic")


def test_the_language_list_is_the_cards_forty_with_asr_support():
    assert len(asr.LANGUAGES) == 40
    assert asr.LANGUAGES[:3] == ("Czech", "Dutch", "English")
    assert asr.LANGUAGES[-1] == "Vietnamese"
    assert "Norwegian" not in asr.LANGUAGES


def test_window_bounds_cover_a_five_minute_recording():
    audio = np.sin(2 * np.pi * 220 * np.arange(300 * SAMPLE_RATE) / SAMPLE_RATE).astype(np.float32)
    bounds = asr.window_bounds(audio)
    assert bounds[0][0] == 0
    assert bounds[-1][1] == len(audio)
    assert all(end == start for (_, end), (start, _) in itertools.pairwise(bounds))
    assert all(asr.WINDOW_SECONDS - asr.SEARCH_SECONDS < (end - start) / SAMPLE_RATE
               <= asr.WINDOW_SECONDS + asr.SEARCH_SECONDS for start, end in bounds[:-1])


def test_a_wav_upload_returns_the_text(client, transcriber):
    response = upload(client, language="English", wording="verbatim", context="Grimaldus")
    assert response.status_code == 200
    assert response.json() == {"text": "hello world", "language": "English", "wording": "verbatim"}
    assert transcriber.loads == 1
    assert len(transcriber.windows) == 1
    samples, prompt = transcriber.windows[0]
    assert samples.shape == (SAMPLE_RATE,)
    assert "Language: English." in prompt and "Context terms: Grimaldus." in prompt


def test_the_form_defaults_are_as_spoken_and_readable(client, transcriber):
    response = upload(client)
    assert response.json() == {"text": "hello world", "language": "as spoken", "wording": "readable"}
    assert "Language: as spoken." in transcriber.windows[0][1]


def test_an_unknown_language_is_422_without_touching_the_model(client, transcriber):
    response = upload(client, language="Klingon")
    assert response.status_code == 422
    assert "unknown language" in response.text
    assert transcriber.loads == 0


def test_garbage_bytes_are_422(client, transcriber):
    response = upload(client, data=b"not a wave file")
    assert response.status_code == 422
    assert "not readable audio" in response.text
    assert transcriber.loads == 0


def test_a_failed_load_leaves_the_error_state(client, transcriber):
    transcriber.load_error = EngineError("the weights could not be downloaded")
    response = upload(client)
    assert response.status_code == 500
    assert app.asr_state == "error"
    assert "could not be downloaded" in app.asr_error


def test_a_start_with_the_interpreter_loads_the_transcriber_in_the_background(engines, monkeypatch):
    """The lifespan starts the load and /health ends at ready without any request."""
    fake = FakeTranscriber()
    monkeypatch.setattr(app, "transcriber", fake)
    monkeypatch.setattr(app, "asr_state", "down")
    monkeypatch.setattr(app, "asr_error", None)
    with TestClient(app.app) as client:
        body = wait_for_asr(client, "ready")
    assert body["asr"] == {"available": True, "loaded": True, "state": "ready", "error": None}
    assert fake.loads == 1


def test_a_start_without_the_interpreter_starts_no_load(engines, monkeypatch):
    """With no ASR interpreter the state stays down and no load thread runs."""
    fake = FakeTranscriber(available=False)
    monkeypatch.setattr(app, "transcriber", fake)
    monkeypatch.setattr(app, "asr_state", "down")
    with TestClient(app.app) as client:
        body = client.get("/health").json()
    assert body["asr"] == {"available": False, "loaded": False, "state": "down", "error": None}
    assert fake.loads == 0


@pytest.mark.parametrize("phase", ["downloading", "loading"])
def test_a_model_that_is_downloading_or_loading_is_503_with_retry_after(client, transcriber, monkeypatch,
                                                                      phase):
    """A request during the download or the load answers 503 at once and never touches the transcriber."""
    monkeypatch.setattr(app, "asr_state", phase)
    response = upload(client)
    assert response.status_code == 503
    assert response.json()["detail"] == f"the transcription model is {phase}"
    assert response.headers["Retry-After"] == "30"
    assert transcriber.loads == 0
    assert transcriber.windows == []


def test_a_down_state_starts_the_load_and_answers_503(client, transcriber, monkeypatch, tmp_path):
    """After the cache is deleted the next request starts the load and answers 503; the load runs once."""
    monkeypatch.setattr(models, "cache_dir", lambda name: tmp_path / name)
    monkeypatch.setattr(app, "asr_state", "down")
    response = upload(client)
    assert response.status_code == 503
    assert response.json()["detail"] == "the transcription model is downloading"
    assert response.headers["Retry-After"] == "30"
    assert wait_for_asr(client, "ready")["asr"]["loaded"] is True
    assert transcriber.loads == 1
    assert transcriber.windows == []
    assert upload(client).status_code == 200
    assert transcriber.loads == 1


def test_no_auth_is_401(transcriber):
    response = TestClient(app.app).post(
        "/transcribe", files={"file": ("recording.wav", wav_bytes(), "audio/wav")})
    assert response.status_code == 401


def test_health_carries_the_transcriber_state(client, transcriber):
    assert client.get("/health").json()["asr"] == {
        "available": True, "loaded": False, "state": "ready", "error": None}
