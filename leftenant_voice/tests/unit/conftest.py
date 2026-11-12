"""The engine registry every unit test uses: two stubs, no model and no GPU; one test password."""
import time

import app
import pytest
from fastapi.testclient import TestClient
from stubs import StubEngine, fake_render

PASSWORD = "test-password"


@pytest.fixture(autouse=True)
def auth(tmp_path, monkeypatch):
    """Every unit test runs with the same password, a fresh session store, no tokens and no token file."""
    monkeypatch.setenv("S2PRO_PASSWORD", PASSWORD)
    monkeypatch.delenv("S2PRO_PASSWORD_FILE", raising=False)
    monkeypatch.setattr(app, "password", PASSWORD.encode())
    monkeypatch.setattr(app, "sessions", {})
    monkeypatch.setattr(app, "tokens", [])
    monkeypatch.setattr(app, "token_salt", None)
    monkeypatch.setattr(app, "TOKENS_FILE", tmp_path / "tokens.json")


@pytest.fixture
def engines(monkeypatch):
    """Two stub engines as the registry, `alpha` as the ENGINE default, and no model or GPU."""
    stubs = {"alpha": StubEngine("alpha"), "beta": StubEngine("beta")}
    monkeypatch.setattr(app, "ENGINES", stubs)
    monkeypatch.setattr(app, "DEFAULT_ENGINE", "alpha")
    monkeypatch.setattr(app, "write_render", fake_render)
    monkeypatch.setattr(app, "loaded_engine", None)
    monkeypatch.setattr(app, "state", "loading")
    monkeypatch.setattr(app, "load_error", None)
    monkeypatch.setattr(app, "last_request", time.monotonic())
    return stubs


@pytest.fixture
def client(engines):
    """A test client holding a login session; the lifespan starts the stub engine."""
    with TestClient(app.app) as client:
        assert client.post("/login", json={"password": PASSWORD}).status_code == 200
        yield client
