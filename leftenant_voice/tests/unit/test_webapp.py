"""The page's endpoints: the session token, the writable voice folder, upload, delete and the token's path
to the weight download. Stub engines, generated WAVs and a stubbed Hugging Face `whoami`; no GPU, no model,
no network."""
import hashlib
import io
import os
import re
import wave

import app
import asr
import engine_s2pro
import httpx
import numpy as np
import pytest
import registry
import soundfile
import speak_s2pro
import torch
from conftest import PASSWORD
from fastapi.testclient import TestClient
from stubs import StubEngine

WHOAMI_URL = "https://huggingface.co/api/whoami-v2"
REAL_WHOAMI = app.whoami  # conftest replaces app.whoami in every test; the timeout tests call the real one


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


def page_ids() -> list[str]:
    """Every element id the page script looks up, read from the script itself: `$("...")`, the step ids it passes
    to `setStep`, and the page and Settings tab sections it builds from PAGES and TABS."""
    script = (app.STATIC_DIR / "app.js").read_text()
    found = set(re.findall(r'\$\("([a-z-]+)"\)', script)) | set(re.findall(r'setStep\("([a-z-]+)"', script))
    found |= {f"page-{name}" for name in ("render", "transcribe", "settings")}
    found |= {f"set-{name}" for name in ("hf", "api", "voices", "models")}
    return sorted(found)


def whoami_account(token: str) -> dict:
    """`whoami` for a token Hugging Face accepts."""
    return {"name": "konrad", "type": "user"}


def hub_answer(status: int, body: dict) -> httpx.Response:
    """An answer of Hugging Face's whoami-v2 endpoint."""
    return httpx.Response(status, json=body, request=httpx.Request("GET", WHOAMI_URL))


def whoami_refused(token: str) -> dict:
    """`whoami` for a token Hugging Face refuses: its 401 answer raised by `raise_for_status`."""
    hub_answer(401, {"error": "Invalid credentials in Authorization header"}).raise_for_status()


def whoami_unreachable(token: str) -> dict:
    """`whoami` when Hugging Face cannot be reached."""
    raise httpx.ConnectError("[Errno -3] Temporary failure in name resolution")


@pytest.fixture
def client(tmp_path, monkeypatch):
    """The app on an empty writable voice folder, one stub engine and no token, logged in."""
    voices = tmp_path / "voices"
    voices.mkdir()
    monkeypatch.setattr(app, "VOICES_DIR", voices)
    monkeypatch.setattr(app, "SEED_VOICES_DIR", None)
    monkeypatch.setattr(app, "ENGINES", {"alpha": StubEngine("alpha")})
    client = TestClient(app.app)
    assert client.post("/login", json={"password": PASSWORD}).status_code == 200
    return client


def test_the_page_is_served(client):
    """GET / answers text/html with every element id the page script uses."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    ids = page_ids()
    assert len(ids) > 40
    for element in ids:
        assert f'id="{element}"' in response.text, element


def test_the_stylesheet_and_the_script_are_public_and_carry_a_content_hash():
    """The page links /static/app.css and /static/app.js with a hash of their content, so a deploy is never served
    an old script, and both answer without a login."""
    anonymous = TestClient(app.app)
    page = anonymous.get("/").text
    content = (app.STATIC_DIR / "app.js").read_bytes() + (app.STATIC_DIR / "app.css").read_bytes()
    key = hashlib.sha256(content).hexdigest()[:12]
    assert f'href="/static/app.css?v={key}"' in page and f'src="/static/app.js?v={key}"' in page
    assert "__ASSET_KEY__" not in page
    css = anonymous.get("/static/app.css")
    assert css.status_code == 200 and css.headers["content-type"].startswith("text/css")
    script = anonymous.get("/static/app.js")
    assert script.status_code == 200 and "javascript" in script.headers["content-type"]


def test_the_page_has_its_pages_and_settings_tabs_behind_the_login(client):
    """Logged out only the login box can show: the app shell starts hidden and holds Voice rendering, Transcription
    and Settings, with Settings' four tabs, each at its own hash address. tests/functional/test_browser.py drives
    them in a browser."""
    page = client.get("/").text
    assert '<div id="app-section" class="p-app" hidden>' in page
    for name in ("render", "transcribe", "settings"):
        assert f'<a href="#/{name}" data-nav="{name}">' in page
        assert f'<section id="page-{name}" hidden>' in page
    for tab in ("hf", "api", "voices", "models"):
        assert f'<a href="#/settings/{tab}" data-tab="{tab}">' in page
        assert f'id="set-{tab}"' in page


def test_the_page_contains_the_transcription_form_and_the_models_section(client):
    """The page has the transcription form over the five formats and the Settings models list."""
    page = client.get("/").text
    assert '<form class="p-card" id="transcribe-form">' in page
    assert 'accept=".mp3,.m4a,.wav,.flac,.ogg"' in page
    assert "<h2>Models</h2>" in page
    assert 'id="model-list"' in page


def test_the_language_options_equal_the_servers_languages(client):
    """The select offers 'as spoken' first, then asr.LANGUAGES in alphabetical order, so a drift in either fails
    here."""
    page = client.get("/").text
    select = page.split('id="transcribe-language"', 1)[1].split("</select>", 1)[0]
    values = [value or text for value, text in re.findall(r'<option(?: value="([^"]*)")?>([^<]*)</option>', select)]
    assert values == ["as spoken", *sorted(asr.LANGUAGES)]


def test_settings_start_without_a_token(client):
    assert client.get("/settings").json() == {"hf_token_set": False, "hf_account": None,
                                              "default_engine": app.DEFAULT_ENGINE,
                                              "max_text_chars": app.MAX_TEXT_CHARS}


def test_the_token_is_set_cleared_and_never_echoed(client, monkeypatch):
    """A token whoami accepts is kept and its account named; an empty token clears it; nothing echoes it."""
    asked = []
    monkeypatch.setattr(app, "whoami", lambda token: asked.append(token) or whoami_account(token))
    response = client.post("/settings/hf-token", json={"token": " hf_secret_value "})
    assert response.status_code == 200
    assert response.json() == {"hf_token_set": True, "hf_account": "konrad"}
    assert asked == ["hf_secret_value"]
    assert "hf_secret_value" not in response.text
    settings = client.get("/settings")
    assert settings.json()["hf_token_set"] is True and settings.json()["hf_account"] == "konrad"
    assert "hf_secret_value" not in settings.text
    assert app._hf_token() == "hf_secret_value"
    cleared = client.post("/settings/hf-token", json={"token": "  "})
    assert cleared.json() == {"hf_token_set": False, "hf_account": None}
    assert asked == ["hf_secret_value"]
    assert app._hf_token() is None


def test_a_refused_token_is_422_with_the_hubs_reason_and_the_saved_token_stays(client, monkeypatch):
    """whoami refusing the token answers 422 with Hugging Face's words; the token saved before is kept."""
    monkeypatch.setattr(app, "whoami", whoami_account)
    assert client.post("/settings/hf-token", json={"token": "hf_good"}).status_code == 200
    monkeypatch.setattr(app, "whoami", whoami_refused)
    response = client.post("/settings/hf-token", json={"token": "hf_wrong_value"})
    assert response.status_code == 422
    assert response.json()["detail"] == ("Hugging Face refused the token: HTTP 401 Unauthorized "
                                         "(Invalid credentials in Authorization header)")
    assert "hf_wrong_value" not in response.text
    assert app._hf_token() == "hf_good"
    assert client.get("/settings").json()["hf_account"] == "konrad"


def test_a_token_the_hub_cannot_check_is_502_and_not_kept(client, monkeypatch):
    """Hugging Face out of reach answers 502 naming the network error; no token is stored."""
    monkeypatch.setattr(app, "whoami", whoami_unreachable)
    response = client.post("/settings/hf-token", json={"token": "hf_unchecked"})
    assert response.status_code == 502
    assert response.json()["detail"].startswith("Hugging Face could not be reached: ")
    assert app._hf_token() is None
    assert client.get("/settings").json()["hf_token_set"] is False


def test_whoami_asks_the_hub_with_the_bearer_token_and_a_ten_second_timeout(client, monkeypatch):
    """The real `whoami` sends the token as Bearer to whoami-v2 with a 10 s timeout; a valid answer names the
    account and a 401 answer is the 422 with the hub's words."""
    asked = []

    def hub(url, headers, timeout):
        asked.append((url, headers, timeout))
        if headers["Authorization"] == "Bearer hf_good":
            return hub_answer(200, {"name": "konrad", "type": "user"})
        return hub_answer(401, {"error": "Invalid credentials in Authorization header"})

    monkeypatch.setattr(app, "whoami", REAL_WHOAMI)
    monkeypatch.setattr(httpx, "get", hub)
    assert client.post("/settings/hf-token", json={"token": "hf_good"}).json() == {"hf_token_set": True,
                                                                                 "hf_account": "konrad"}
    refused = client.post("/settings/hf-token", json={"token": "hf_bad"})
    assert refused.status_code == 422
    assert "(Invalid credentials in Authorization header)" in refused.json()["detail"]
    assert asked == [(WHOAMI_URL, {"Authorization": "Bearer hf_good"}, 10.0),
                     (WHOAMI_URL, {"Authorization": "Bearer hf_bad"}, 10.0)]
    assert app._hf_token() == "hf_good"


def test_a_hub_that_does_not_answer_in_time_is_502_and_the_token_is_not_kept(client, monkeypatch):
    """A timeout of the whoami request answers 502 naming it; no token is stored."""

    def silent_hub(url, headers, timeout):
        raise httpx.ConnectTimeout("")

    monkeypatch.setattr(app, "whoami", REAL_WHOAMI)
    monkeypatch.setattr(httpx, "get", silent_hub)
    response = client.post("/settings/hf-token", json={"token": "hf_unchecked"})
    assert response.status_code == 502
    assert response.json()["detail"] == "Hugging Face could not be reached: ConnectTimeout"
    assert app._hf_token() is None


def test_a_hub_error_other_than_a_refusal_is_502(client, monkeypatch):
    """A 5xx answer of the hub says Hugging Face did not check the token."""
    monkeypatch.setattr(app, "whoami", lambda token: hub_answer(503, {"error": "Service unavailable"}).raise_for_status())
    response = client.post("/settings/hf-token", json={"token": "hf_later"})
    assert response.status_code == 502
    assert response.json()["detail"] == ("Hugging Face did not check the token: HTTP 503 Service Unavailable "
                                         "(Service unavailable)")


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
