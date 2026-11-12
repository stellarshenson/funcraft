"""The password, the login session and the API tokens: startup, cookies, Bearer use and the store."""
import json

import app
import pytest
from conftest import PASSWORD
from fastapi.testclient import TestClient

BEARER = "Authorization"
PROTECTED = [
    ("get", "/settings", None, None),
    ("post", "/settings/hf-token", {"token": "hf_value"}, None),
    ("get", "/tokens", None, None),
    ("post", "/tokens", {"name": "ci"}, None),
    ("delete", "/tokens/ci", None, None),
    ("post", "/logout", None, None),
    ("post", "/speak", {"text": "hello", "voice": "grimaldus"}, None),
    ("get", "/voices", None, None),
    ("delete", "/voices/nobody", None, None),
]


def test_the_password_comes_from_the_environment(monkeypatch):
    """S2PRO_PASSWORD is the password when no file is named."""
    monkeypatch.setenv("S2PRO_PASSWORD", "from-env")
    assert app.load_password() == b"from-env"


def test_the_password_file_wins_and_only_the_first_line_counts(tmp_path, monkeypatch):
    """S2PRO_PASSWORD_FILE beats S2PRO_PASSWORD; its first line loses the CRLF and nothing else."""
    path = tmp_path / "password.txt"
    path.write_bytes(b"  from-file\r\nsecond line\n")
    monkeypatch.setenv("S2PRO_PASSWORD_FILE", str(path))
    monkeypatch.setenv("S2PRO_PASSWORD", "from-env")
    assert app.load_password() == b"  from-file"


def test_no_password_is_the_startup_error(monkeypatch):
    """Neither variable set raises the error naming both."""
    monkeypatch.delenv("S2PRO_PASSWORD", raising=False)
    monkeypatch.delenv("S2PRO_PASSWORD_FILE", raising=False)
    with pytest.raises(RuntimeError, match="no password: set S2PRO_PASSWORD_FILE or S2PRO_PASSWORD"):
        app.load_password()


def test_an_empty_password_is_the_startup_error(monkeypatch):
    """An empty S2PRO_PASSWORD counts as no password."""
    monkeypatch.setenv("S2PRO_PASSWORD", "")
    monkeypatch.delenv("S2PRO_PASSWORD_FILE", raising=False)
    with pytest.raises(RuntimeError, match="no password"):
        app.load_password()


def test_login_sets_a_strict_httponly_cookie():
    """A login sets `sid`, HttpOnly, SameSite=Strict, path /, and /session reports it."""
    client = TestClient(app.app)
    response = client.post("/login", json={"password": PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}
    cookie = response.headers["set-cookie"].lower()
    assert "sid=" in cookie and "httponly" in cookie and "samesite=strict" in cookie
    assert "path=/" in cookie and "max-age=43200" in cookie
    assert client.get("/session").json() == {"authenticated": True}


def test_a_wrong_or_empty_password_is_401():
    """A wrong password and an empty one are both 401 and open no session."""
    client = TestClient(app.app)
    assert client.post("/login", json={"password": "wrong"}).status_code == 401
    assert client.post("/login", json={"password": ""}).status_code == 401
    assert client.get("/session").json() == {"authenticated": False}


def test_logout_ends_the_session_and_clears_the_cookie(client):
    """A logged-in logout answers 200; afterwards /session is false and a protected call is 401."""
    response = client.post("/logout")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}
    assert client.get("/session").json() == {"authenticated": False}
    assert client.get("/settings").status_code == 401


@pytest.mark.parametrize("method,path,body,headers", PROTECTED)
def test_every_protected_endpoint_is_401_without_credentials(method, path, body, headers):
    """Each protected endpoint refuses an anonymous call."""
    if path == "/speak":
        body = {"voice": "grimaldus", **body}
    response = TestClient(app.app).request(method, path, json=body, headers=headers)
    assert response.status_code == 401, (method, path, response.text)


def test_the_voice_upload_is_401_without_credentials():
    """POST /voices is protected like the other voice calls."""
    response = TestClient(app.app).post(
        "/voices", data={"name": "newvoice", "text": "a transcript"},
        files={"file": ("reference.wav", b"", "audio/wav")})
    assert response.status_code == 401


def test_the_public_endpoints_answer_without_credentials():
    """The page, /health and /session are public; /login answers its own 401 for a wrong password."""
    client = TestClient(app.app)
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/session").json() == {"authenticated": False}


def test_a_forged_session_and_an_unknown_token_are_401():
    """A made-up `sid` and an unknown Bearer token open nothing."""
    client = TestClient(app.app)
    client.cookies.set("sid", "not-a-session")
    assert client.get("/voices").status_code == 401
    assert client.get("/voices", headers={BEARER: "Bearer vtts_unknown"}).status_code == 401


def test_a_token_works_as_a_bearer(client):
    """A created token opens /voices and /speak, without the session cookie."""
    created = client.post("/tokens", json={"name": "bearer"}).json()
    headers = {BEARER: f"Bearer {created['token']}"}
    anonymous = TestClient(app.app)
    assert anonymous.get("/voices", headers=headers).status_code == 200
    response = anonymous.post("/speak", json={"text": "hello", "voice": "grimaldus"}, headers=headers)
    assert response.status_code == 200


def test_a_created_token_is_shown_once_listed_and_stored_encrypted(client):
    """The response carries the plaintext once; the list carries name, prefix and date; the file does not."""
    response = client.post("/tokens", json={"name": "ci"})
    assert response.status_code == 201
    created = response.json()
    assert set(created) == {"name", "token", "prefix", "created"}
    assert created["name"] == "ci"
    assert created["token"].startswith("vtts_")
    assert created["prefix"] == created["token"][len("vtts_"):][:8]
    listed = client.get("/tokens").json()["tokens"]
    assert listed == [{"name": "ci", "prefix": created["prefix"], "created": created["created"]}]
    store = app.TOKENS_FILE.read_bytes()
    assert set(json.loads(store)) == {"version", "salt", "nonce", "ciphertext"}
    assert created["token"].encode() not in store
    assert created["prefix"].encode() not in store
    assert PASSWORD.encode() not in store


def test_a_bad_token_name_is_422_and_a_duplicate_is_409(client):
    """Names follow the voice rule; a second token with the same name is 409."""
    assert client.post("/tokens", json={"name": "Not A Name"}).status_code == 422
    assert client.post("/tokens", json={"name": "ci"}).status_code == 201
    assert client.post("/tokens", json={"name": "ci"}).status_code == 409
    assert [token["name"] for token in client.get("/tokens").json()["tokens"]] == ["ci"]


def test_a_revoked_token_is_401_and_an_unknown_delete_is_404(client):
    """Revoking removes it from the store and the API refuses it; a second delete is 404."""
    token = client.post("/tokens", json={"name": "gone"}).json()["token"]
    headers = {BEARER: f"Bearer {token}"}
    assert client.delete("/tokens/gone").json() == {"deleted": "gone"}
    assert TestClient(app.app).get("/voices", headers=headers).status_code == 401
    assert client.delete("/tokens/gone").status_code == 404


def test_tokens_survive_a_reload(client):
    """A token created before a restart opens the API after the store is read again."""
    token = client.post("/tokens", json={"name": "kept"}).json()["token"]
    app.tokens = []
    app.token_salt = None
    app.load_tokens()
    assert [record["name"] for record in client.get("/tokens").json()["tokens"]] == ["kept"]
    assert TestClient(app.app).get(
        "/voices", headers={BEARER: f"Bearer {token}"}).status_code == 200


def test_a_store_written_with_one_password_does_not_load_with_another(client, monkeypatch):
    """A password other than the store's raises the startup error naming the file."""
    client.post("/tokens", json={"name": "kept"})
    monkeypatch.setattr(app, "password", b"another-password")
    with pytest.raises(RuntimeError, match="the token store cannot be decrypted"):
        app.load_tokens()


def test_token_management_needs_the_session_not_a_bearer(client):
    """A Bearer token opens /voices but not /settings or the token endpoints."""
    token = client.post("/tokens", json={"name": "api"}).json()["token"]
    headers = {BEARER: f"Bearer {token}"}
    anonymous = TestClient(app.app)
    assert anonymous.get("/settings", headers=headers).status_code == 401
    assert anonymous.post("/settings/hf-token", json={"token": "x"}, headers=headers).status_code == 401
    assert anonymous.get("/tokens", headers=headers).status_code == 401
    assert anonymous.post("/tokens", json={"name": "other"}, headers=headers).status_code == 401
    assert anonymous.delete("/tokens/api", headers=headers).status_code == 401
