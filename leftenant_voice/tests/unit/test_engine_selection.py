"""Engine selection on POST /speak, an unknown engine, the default fallback and /voices, with stub engines.

No GPU and no model: the stubs in conftest return one second of silence, and the MP3 writer is replaced by a
stub file because `audio_out.write_render` needs ffmpeg. The real MP3 path is the functional suite's business.
"""
import threading

import app
from fastapi.testclient import TestClient
from stubs import StubEngine


def test_named_engine_is_selected(client, engines):
    """The request's engine speaks the text, and the other engine is not used."""
    response = client.post(
        "/speak", json={"text": "hello", "voice": "grimaldus", "engine": "beta"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert engines["beta"].spoken == [("hello", "grimaldus")]
    assert engines["alpha"].spoken == []


def test_absent_engine_uses_the_environment_default(client, engines):
    """A request without an engine uses DEFAULT_ENGINE."""
    response = client.post("/speak", json={"text": "hello", "voice": "grimaldus"})
    assert response.status_code == 200
    assert engines["alpha"].spoken == [("hello", "grimaldus")]
    assert engines["beta"].spoken == []


def test_unknown_engine_is_4xx_and_lists_the_known_ones(client):
    """An engine that is not installed is a 404 whose message names the installed ones."""
    response = client.post(
        "/speak", json={"text": "hello", "voice": "grimaldus", "engine": "nope"})
    assert response.status_code == 404
    assert "alpha" in response.text and "beta" in response.text


def test_switching_engines_unloads_the_previous_one(client, engines):
    """One engine is resident at a time: a request for the other unloads the first."""
    client.post("/speak", json={"text": "one", "voice": "grimaldus", "engine": "alpha"})
    client.post("/speak", json={"text": "two", "voice": "grimaldus", "engine": "beta"})
    assert (engines["alpha"].loads, engines["alpha"].unloads) == (1, 1)
    assert (engines["beta"].loads, engines["beta"].unloads) == (1, 0)


def test_voices_lists_every_engine(client):
    """GET /voices maps each installed engine to its voices."""
    response = client.get("/voices")
    body = response.json()
    assert body["voices"] == {"alpha": ["grimaldus"], "beta": ["grimaldus"]}
    assert isinstance(body["uploaded"], list)


def test_health_answers_while_the_default_engine_loads(engines):
    """The startup load runs off the request path: /health is 200 with loaded false during it."""
    started, release = threading.Event(), threading.Event()

    class SlowEngine(StubEngine):
        def load(self, report=None) -> None:
            started.set()
            release.wait(10)
            super().load(report)

    engines["alpha"] = SlowEngine("alpha")
    with TestClient(app.app) as client:  # the context manager runs the lifespan, which starts the load
        assert started.wait(5)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["loaded"] is False
        release.set()
