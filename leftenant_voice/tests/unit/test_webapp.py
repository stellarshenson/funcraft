"""The page's endpoints: the session token, the writable voice folder, upload, delete and the token's path
to the weight download. Stub engines and generated WAVs; no GPU, no model, no network."""
import io
import os
import re
import wave

import app
import asr
import engine_s2pro
import numpy as np
import pytest
import registry
import soundfile
import speak_s2pro
import torch
from conftest import PASSWORD
from fastapi.testclient import TestClient
from stubs import StubEngine

PAGE_IDS = ("service-status", "asr-state", "token-form", "token-input", "token-state", "engine-select",
            "voice-select", "upload-form", "upload-name", "upload-text", "upload-file", "uploaded-list",
            "speak-form", "speak-text", "speak-button", "player", "message", "login-form", "login-password",
            "login-button", "logout-button", "app-section", "api-token-form", "api-token-name",
            "api-token-create", "api-token-list", "model-list", "models-status", "models-error",
            "transcribe-form", "transcribe-file", "transcribe-language", "transcribe-wording",
            "transcribe-context", "transcribe-button", "transcribe-state", "transcribe-busy",
            "transcribe-error", "transcribe-output", "transcribe-result")


def wav_bytes(seconds: float, channels: int = 1, rate: int = 16000) -> bytes:
    """A PCM_16 WAV of `seconds` of a quiet tone.

    Args:
        seconds: duration in seconds.
        channels: channel count; more than one gives a stereo or wider file.
        rate: sample rate in Hz.
    """
    tone = (0.1 * np.sin(2 * np.pi * 220 * np.arange(int(seconds * rate)) / rate) * 32767).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as file:
        file.setnchannels(channels)
        file.setsampwidth(2)
        file.setframerate(rate)
        file.writeframes(np.repeat(tone[:, None], channels, axis=1).tobytes())
    return buffer.getvalue()


def upload(client, name: str = "newvoice", text: str = "A reference transcript.",
           data: bytes | None = None):
    """POST /voices; the reference is a 4 s mono WAV unless `data` says otherwise."""
    return client.post("/voices", data={"name": name, "text": text},
                       files={"file": ("reference.wav", wav_bytes(4.0) if data is None else data,
                                       "audio/wav")})


def seed_folder(tmp_path, name: str) -> "os.PathLike":
    """Write a bundled `<name>.wav` + `<name>.txt` pair into a fresh seed folder and return it."""
    seed = tmp_path / "seed"
    seed.mkdir(exist_ok=True)
    (seed / f"{name}.wav").write_bytes(wav_bytes(4.0))
    (seed / f"{name}.txt").write_text("bundled transcript")
    return seed


@pytest.fixture
def client(tmp_path, monkeypatch):
    """The app on an empty writable voice folder, one stub engine and no token, logged in."""
    voices = tmp_path / "voices"
    voices.mkdir()
    monkeypatch.setattr(app, "VOICES_DIR", voices)
    monkeypatch.setattr(app, "SEED_VOICES_DIR", None)
    monkeypatch.setattr(app, "ENGINES", {"alpha": StubEngine("alpha")})
    monkeypatch.setattr(app, "hf_token", None)
    client = TestClient(app.app)
    assert client.post("/login", json={"password": PASSWORD}).status_code == 200
    return client


def test_the_page_is_served(client):
    """GET / answers text/html with every element id the page script uses."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    for element in PAGE_IDS:
        assert f'id="{element}"' in response.text, element


def test_the_page_contains_the_transcription_form_and_the_models_section(client):
    """The page has the transcription form over the five formats and the Settings models list."""
    page = client.get("/").text
    assert '<form id="transcribe-form">' in page
    assert 'accept=".mp3,.m4a,.wav,.flac,.ogg"' in page
    assert '<h3>Models</h3>' in page
    assert 'id="model-list"' in page


def test_the_language_options_equal_the_servers_languages(client):
    """The select's values are 'as spoken' plus asr.LANGUAGES, so a drift in either fails here."""
    page = client.get("/").text
    select = page.split('id="transcribe-language"', 1)[1].split("</select>", 1)[0]
    values = re.findall(r'<option value="([^"]*)">', select)
    assert values == ["as spoken", *asr.LANGUAGES]


def test_the_script_calls_the_transcription_and_model_endpoints(client):
    """The page script posts to /transcribe, lists /models and deletes /models/<name>."""
    page = client.get("/").text
    assert 'fetch("/transcribe"' in page
    assert 'fetch("/models"' in page
    assert 'fetch("/models/" + encodeURIComponent(name)' in page


def test_the_page_carries_the_transcription_state_and_the_ready_gate(client):
    """The status view shows the ASR state, and Transcribe is enabled only in `ready`, `down` and `error`, so a press can start the load."""
    page = client.get("/").text
    assert 'id="asr-state"' in page
    assert 'id="transcribe-state"' in page
    assert 'asrState = asr.state || "unknown"' in page
    assert 'ui.transcribeButton.disabled = transcribing || !["ready", "down", "error"].includes(asrState)' in page


def test_settings_start_without_a_token(client):
    assert client.get("/settings").json() == {"hf_token_set": False, "default_engine": app.DEFAULT_ENGINE,
                                              "max_text_chars": app.MAX_TEXT_CHARS}


def test_the_token_is_set_cleared_and_never_echoed(client):
    response = client.post("/settings/hf-token", json={"token": "hf_secret_value"})
    assert response.status_code == 200
    assert response.json() == {"hf_token_set": True}
    assert "hf_secret_value" not in response.text
    assert client.get("/settings").json()["hf_token_set"] is True
    assert "hf_secret_value" not in client.get("/settings").text
    assert app._hf_token() == "hf_secret_value"
    cleared = client.post("/settings/hf-token", json={"token": "  "})
    assert cleared.json() == {"hf_token_set": False}
    assert app._hf_token() is None


def test_upload_writes_both_files_and_lists_the_voice(client):
    response = upload(client)
    assert response.status_code == 201
    assert response.json() == {"name": "newvoice"}
    assert (app.VOICES_DIR / "newvoice.wav").is_file()
    assert (app.VOICES_DIR / "newvoice.txt").read_text() == "A reference transcript."
    assert app.uploaded_voices() == ["newvoice"]
    assert client.get("/voices").json()["uploaded"] == ["newvoice"]


def test_a_stereo_reference_is_stored_as_one_channel(client):
    assert upload(client, data=wav_bytes(4.0, channels=2)).status_code == 201
    audio, _ = soundfile.read(app.VOICES_DIR / "newvoice.wav")
    assert audio.ndim == 1


def test_a_bad_name_is_422_naming_the_rule(client):
    response = upload(client, name="Not A Name")
    assert response.status_code == 422
    assert "^[a-z0-9][a-z0-9_-]{0,39}$" in response.text


def test_a_reference_shorter_than_three_seconds_is_422_with_its_length(client):
    response = upload(client, data=wav_bytes(1.0))
    assert response.status_code == 422
    assert "1.0 s" in response.text


def test_a_reference_longer_than_thirty_seconds_is_422_with_its_length(client):
    response = upload(client, data=wav_bytes(31.0))
    assert response.status_code == 422
    assert "31.0 s" in response.text


def test_garbage_bytes_are_422(client):
    response = upload(client, data=b"not a wave file")
    assert response.status_code == 422
    assert "not a readable audio file" in response.text


def test_a_transcript_over_a_thousand_characters_is_422(client):
    response = upload(client, text="x" * 1001)
    assert response.status_code == 422
    assert "1000" in response.text


def test_an_uploaded_name_is_409(client):
    assert upload(client).status_code == 201
    assert upload(client).status_code == 409


def test_an_upload_over_a_lone_transcript_succeeds(client):
    """A retry after an interrupted upload writes both files and replaces the lone transcript."""
    (app.VOICES_DIR / "half.txt").write_text("left by an interrupted upload")
    response = upload(client, name="half", text="A new transcript.")
    assert response.status_code == 201
    assert (app.VOICES_DIR / "half.wav").is_file()
    assert (app.VOICES_DIR / "half.txt").read_text() == "A new transcript."


def test_a_bundled_name_is_409(client, tmp_path, monkeypatch):
    monkeypatch.setattr(app, "SEED_VOICES_DIR", seed_folder(tmp_path, "grimaldus"))
    app.seed_voices()
    response = upload(client, name="grimaldus")
    assert response.status_code == 409
    assert "already exists" in response.text


def test_a_file_over_the_limit_is_413(client, monkeypatch):
    monkeypatch.setattr(app, "MAX_UPLOAD_BYTES", 1000)
    assert upload(client).status_code == 413


def test_delete_removes_an_uploaded_voice(client):
    upload(client)
    response = client.delete("/voices/newvoice")
    assert response.status_code == 200
    assert response.json() == {"deleted": "newvoice"}
    assert not (app.VOICES_DIR / "newvoice.wav").exists()
    assert not (app.VOICES_DIR / "newvoice.txt").exists()


def test_delete_of_a_bundled_voice_is_409(client, tmp_path, monkeypatch):
    monkeypatch.setattr(app, "SEED_VOICES_DIR", seed_folder(tmp_path, "grimaldus"))
    app.seed_voices()
    assert client.delete("/voices/grimaldus").status_code == 409
    assert (app.VOICES_DIR / "grimaldus.wav").is_file()


def test_delete_of_an_unknown_voice_is_404(client):
    assert client.delete("/voices/nobody").status_code == 404


def test_seed_copies_refreshes_and_leaves_uploads(client, tmp_path, monkeypatch):
    seed = seed_folder(tmp_path, "grimaldus")
    monkeypatch.setattr(app, "SEED_VOICES_DIR", seed)
    app.seed_voices()
    assert (app.VOICES_DIR / "grimaldus.txt").read_text() == "bundled transcript"
    (app.VOICES_DIR / "mine.wav").write_bytes(b"mine")
    (app.VOICES_DIR / "mine.txt").write_text("mine")
    (seed / "grimaldus.txt").write_text("changed transcript")
    app.seed_voices()
    assert (app.VOICES_DIR / "grimaldus.txt").read_text() == "changed transcript"
    assert (app.VOICES_DIR / "mine.txt").read_text() == "mine"
    assert app.uploaded_voices() == ["mine"]


def test_seed_does_nothing_when_the_folders_are_the_same(client, monkeypatch):
    monkeypatch.setattr(app, "SEED_VOICES_DIR", app.VOICES_DIR)
    (app.VOICES_DIR / "keep.wav").write_bytes(b"keep")
    (app.VOICES_DIR / "keep.txt").write_text("keep")
    app.seed_voices()
    assert (app.VOICES_DIR / "keep.wav").read_bytes() == b"keep"


def test_the_engine_passes_the_token_to_both_downloads(tmp_path, monkeypatch):
    seen = []

    def fake_snapshot_download(model, revision, **kwargs):
        seen.append(kwargs)
        if len(seen) == 1:
            raise engine_s2pro.LocalEntryNotFoundError("the snapshot is not cached")
        return str(tmp_path)

    monkeypatch.setattr(engine_s2pro, "snapshot_download", fake_snapshot_download)
    monkeypatch.setattr(engine_s2pro, "S2ProSpeaker", lambda folder: object())
    engine_s2pro.S2ProEngine(tmp_path, lambda: "tok").load()
    assert seen[0]["token"] == "tok"
    assert seen[1]["token"] == "tok"


def test_available_engines_passes_the_token_through(tmp_path):
    assert registry.available_engines(tmp_path, lambda: "tok")["s2pro"].token() == "tok"


def test_the_voice_cache_re_encodes_when_the_wav_changes(tmp_path, monkeypatch):
    encodes = []
    monkeypatch.setattr(speak_s2pro, "encode_audio",
                        lambda wav, codec, device: encodes.append(wav) or torch.zeros(4))
    speaker = object.__new__(speak_s2pro.S2ProSpeaker)
    speaker.voices_dir = tmp_path
    speaker._voices = {}
    speaker.codec = object()
    wav, transcript = tmp_path / "v.wav", tmp_path / "v.txt"
    wav.write_bytes(b"one")
    transcript.write_text("first words")
    assert speaker._voice("v")[0] == "first words"
    assert speaker._voice("v")[0] == "first words"
    assert len(encodes) == 1
    wav.write_bytes(b"two")
    transcript.write_text("second words")
    os.utime(wav, ns=(0, wav.stat().st_mtime_ns + 1_000_000))
    assert speaker._voice("v")[0] == "second words"
    assert len(encodes) == 2
