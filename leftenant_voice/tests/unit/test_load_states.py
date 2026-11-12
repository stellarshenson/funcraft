"""The load state /health reports: downloading a cold cache, loading a warm one, ready, and a failed load."""
import time
from pathlib import Path

import app
import engine_s2pro
import pytest
from conftest import PASSWORD
from engine import EngineError
from fastapi.testclient import TestClient
from huggingface_hub.errors import LocalEntryNotFoundError
from stubs import StubEngine


class FakeSpeaker:
    """Stand-in for S2ProSpeaker: records the voice folder and loads nothing."""

    def __init__(self, voices_dir: Path) -> None:
        self.voices_dir = voices_dir


def snapshot_that(cache_has_it: bool):
    """A stand-in for huggingface_hub.snapshot_download that records each mode it is asked for."""
    calls = []

    def snapshot_download(repo, revision, local_files_only=False, **kwargs):
        calls.append(local_files_only)
        if local_files_only and not cache_has_it:
            raise LocalEntryNotFoundError("the pinned snapshot is not in the cache")
        return "/cache/snapshot"

    return snapshot_download, calls


def test_a_cold_cache_downloads_then_loads(monkeypatch, tmp_path):
    """A cache without the pinned snapshot reports downloading for the fetch, then loading for the model."""
    download, calls = snapshot_that(cache_has_it=False)
    monkeypatch.setattr(engine_s2pro, "snapshot_download", download)
    monkeypatch.setattr(engine_s2pro, "S2ProSpeaker", FakeSpeaker)
    phases = []
    engine_s2pro.S2ProEngine(tmp_path).load(phases.append)
    assert phases == ["downloading", "loading"]
    assert calls == [True, False]


def test_a_warm_cache_loads_without_downloading(monkeypatch, tmp_path):
    """The volume keeps the weights: a cached snapshot reports loading and never fetches."""
    download, calls = snapshot_that(cache_has_it=True)
    monkeypatch.setattr(engine_s2pro, "snapshot_download", download)
    monkeypatch.setattr(engine_s2pro, "S2ProSpeaker", FakeSpeaker)
    phases = []
    engine_s2pro.S2ProEngine(tmp_path).load(phases.append)
    assert phases == ["loading"]
    assert calls == [True]


def test_a_failed_download_is_an_engine_error(monkeypatch, tmp_path):
    """A download that cannot reach Hugging Face raises EngineError with the reason, not a bare traceback."""
    def unreachable(repo, revision, local_files_only=False, **kwargs):
        if local_files_only:
            raise LocalEntryNotFoundError("the pinned snapshot is not in the cache")
        raise ConnectionError("the network is down")

    monkeypatch.setattr(engine_s2pro, "snapshot_download", unreachable)
    monkeypatch.setattr(engine_s2pro, "S2ProSpeaker", FakeSpeaker)
    with pytest.raises(EngineError, match="the network is down"):
        engine_s2pro.S2ProEngine(tmp_path).load()


def wait_for_state(client: TestClient, wanted: str, timeout: float = 5.0) -> dict:
    """Poll /health until it reports `wanted` and return that body."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get("/health").json()
        if body["state"] == wanted:
            return body
        time.sleep(0.05)
    raise AssertionError(f"/health never reported state {wanted!r}; last body {body}")


class FailingEngine(StubEngine):
    """An engine whose load always fails with an EngineError."""

    def load(self, report=None) -> None:
        raise EngineError("the s2pro model could not be loaded: the network is down")


def test_health_reports_ready_after_a_load(engines):
    """A successful background load leaves /health loaded, ready and without an error."""
    with TestClient(app.app) as client:
        body = wait_for_state(client, "ready")
    assert body["loaded"] is True
    assert body["engine"] == "alpha"
    assert body["error"] is None


def test_health_reports_a_failed_load_and_speak_answers_500(engines):
    """A failed load is visible on /health, and the next request answers 500 with the same reason."""
    engines["alpha"] = FailingEngine("alpha")
    with TestClient(app.app) as client:
        assert client.post("/login", json={"password": PASSWORD}).status_code == 200
        body = wait_for_state(client, "error")
        assert body["loaded"] is False
        assert "the network is down" in body["error"]
        response = client.post("/speak", json={"text": "hello", "voice": "grimaldus"})
    assert response.status_code == 500
    assert "the network is down" in response.text
