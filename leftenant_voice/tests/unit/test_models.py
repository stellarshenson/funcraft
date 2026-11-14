"""The model cache API: listing both caches, deleting one, and unloading a loaded model first."""
import time

import app
import models
import pytest
from fastapi.testclient import TestClient
from stubs import StubEngine

S2PRO_BYTES = 1000
NEMOTRON_BYTES = 2000


class FakeTranscriber:
    """Stand-in for NemotronTranscriber: reports whether it is loaded and records each unload."""

    def __init__(self, loaded: bool = False) -> None:
        self.loaded = loaded
        self.unloads = 0

    def is_loaded(self) -> bool:
        return self.loaded

    def unload(self) -> None:
        self.unloads += 1
        self.loaded = False


@pytest.fixture
def hub(tmp_path, monkeypatch):
    """A temporary HF_HOME with both model caches holding files of known sizes."""
    monkeypatch.setattr(models, "HF_HOME", str(tmp_path / "huggingface"))
    (models.cache_dir("s2pro") / "blobs").mkdir(parents=True)
    (models.cache_dir("s2pro") / "blobs" / "weights").write_bytes(b"x" * 700)
    (models.cache_dir("s2pro") / "snapshots" / "rev").mkdir(parents=True)
    (models.cache_dir("s2pro") / "snapshots" / "rev" / "config.json").write_bytes(b"x" * 300)
    (models.cache_dir("nemotron") / "blobs").mkdir(parents=True)
    (models.cache_dir("nemotron") / "blobs" / "weights").write_bytes(b"x" * NEMOTRON_BYTES)


def wait_for_default() -> None:
    """Wait for the lifespan's background load, so a later monkeypatch of `loaded_engine` is not overwritten."""
    deadline = time.monotonic() + 5
    while app.loaded_engine is None:
        if time.monotonic() > deadline:
            raise AssertionError("the default stub engine never loaded")
        time.sleep(0.01)


def test_get_models_lists_both_caches_with_their_sizes(client, hub):
    """GET /models names both models in MODELS order with the cache folder, its bytes and the loaded flag."""
    listed = client.get("/models").json()["models"]
    assert [entry["name"] for entry in listed] == ["s2pro", "nemotron"]
    s2pro, nemotron = listed
    assert s2pro == {"name": "s2pro", "model": "fishaudio/s2-pro",
                     "path": str(models.cache_dir("s2pro")), "cached": True, "bytes": S2PRO_BYTES,
                     "loaded": False}
    assert (nemotron["model"], nemotron["cached"], nemotron["bytes"], nemotron["loaded"]) == (
        "nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B", True, NEMOTRON_BYTES, False)


def test_a_snapshotted_cache_counts_each_blob_once(client, tmp_path, monkeypatch):
    """The hub's layout stores a blob under blobs/ and links it from snapshots/: list and delete count it once."""
    monkeypatch.setattr(models, "HF_HOME", str(tmp_path / "huggingface"))
    blob = models.cache_dir("s2pro") / "blobs" / "abcdef"
    blob.parent.mkdir(parents=True)
    blob.write_bytes(b"x" * S2PRO_BYTES)
    link = models.cache_dir("s2pro") / "snapshots" / "rev" / "model.bin"
    link.parent.mkdir(parents=True)
    link.symlink_to(blob)
    assert models.tree_bytes(models.cache_dir("s2pro")) == S2PRO_BYTES
    assert client.get("/models").json()["models"][0]["bytes"] == S2PRO_BYTES
    assert client.delete("/models/s2pro").json() == {"deleted": "s2pro", "freed_bytes": S2PRO_BYTES}


def test_a_shared_blob_counts_for_every_model_and_goes_with_the_last(client, tmp_path, monkeypatch):
    """A blob in the hub's shared store counts for each model linking it and is freed by the last delete."""
    monkeypatch.setattr(models, "HF_HOME", str(tmp_path / "huggingface"))
    shared = tmp_path / "huggingface" / "hub" / "blobs" / "shared"
    shared.parent.mkdir(parents=True)
    shared.write_bytes(b"x" * NEMOTRON_BYTES)
    for name in ("s2pro", "nemotron"):
        link = models.cache_dir(name) / "snapshots" / "rev" / "weights"
        link.parent.mkdir(parents=True)
        link.symlink_to(shared)
    assert [entry["bytes"] for entry in client.get("/models").json()["models"]] == [
        NEMOTRON_BYTES, NEMOTRON_BYTES]
    assert client.delete("/models/s2pro").json() == {"deleted": "s2pro", "freed_bytes": 0}
    assert shared.stat().st_size == NEMOTRON_BYTES
    assert client.get("/models").json()["models"][1]["bytes"] == NEMOTRON_BYTES
    assert client.delete("/models/nemotron").json() == {
        "deleted": "nemotron", "freed_bytes": NEMOTRON_BYTES}
    assert not shared.exists()


def test_a_missing_cache_frees_nothing(client, tmp_path, monkeypatch):
    """DELETE /models/{name} with no cache directory removes nothing and reports 0 bytes."""
    monkeypatch.setattr(models, "HF_HOME", str(tmp_path / "huggingface"))
    assert client.delete("/models/s2pro").json() == {"deleted": "s2pro", "freed_bytes": 0}


def test_delete_removes_the_cache_and_a_second_delete_frees_nothing(client, hub):
    """DELETE /models/s2pro reports the bytes held before the delete; the second delete finds no cache."""
    path = models.cache_dir("s2pro")
    assert client.delete("/models/s2pro").json() == {"deleted": "s2pro", "freed_bytes": S2PRO_BYTES}
    assert not path.exists()
    assert client.delete("/models/s2pro").json() == {"deleted": "s2pro", "freed_bytes": 0}


def test_delete_unloads_a_loaded_s2pro_engine_first(client, hub, monkeypatch):
    """A resident s2pro engine is unloaded under the service lock before its cache is removed."""
    wait_for_default()
    stub = StubEngine("s2pro")
    monkeypatch.setitem(app.ENGINES, "s2pro", stub)
    monkeypatch.setattr(app, "loaded_engine", "s2pro")
    assert client.get("/models").json()["models"][0]["loaded"] is True
    assert client.delete("/models/s2pro").json() == {"deleted": "s2pro", "freed_bytes": S2PRO_BYTES}
    assert stub.unloads == 1
    assert app.loaded_engine is None
    assert not models.cache_dir("s2pro").exists()


def test_delete_unloads_the_nemotron_transcriber_first(client, hub, monkeypatch):
    """A loaded transcriber is unloaded under asr_lock before its cache is removed, and its state goes down."""
    fake = FakeTranscriber(loaded=True)
    monkeypatch.setattr(app, "transcriber", fake)
    monkeypatch.setattr(app, "asr_state", "ready")
    assert client.get("/models").json()["models"][1]["loaded"] is True
    assert client.delete("/models/nemotron").json() == {"deleted": "nemotron", "freed_bytes": NEMOTRON_BYTES}
    assert fake.unloads == 1
    assert app.asr_state == "down"
    assert app.asr_error is None
    assert not models.cache_dir("nemotron").exists()


def test_an_unknown_model_is_404(client):
    """DELETE /models/{name} refuses a name the service does not know."""
    response = client.delete("/models/other")
    assert response.status_code == 404
    assert "unknown model" in response.text


def test_no_session_is_401(hub):
    """Both requests need the session cookie."""
    assert TestClient(app.app).get("/models").status_code == 401
    assert TestClient(app.app).delete("/models/s2pro").status_code == 401
