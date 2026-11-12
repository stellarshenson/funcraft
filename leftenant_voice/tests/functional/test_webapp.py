"""The web app on the real service: the login, the page, reference upload, speak and token rules.

The service reads a throwaway voice folder seeded from `service/voices`, so `service/voices` itself is never
written. The tests run in file order and share one uploaded voice: the upload test creates `functional-upload`,
the speak test uses it and the delete test removes it.
"""
import json
import os
import signal
import subprocess
import uuid
from types import SimpleNamespace

import httpx
import pytest
import support

W = support.PROJECT / "tmp/workflows/webapp"
SENTENCE = "Brothers, we stand upon the wall and we do not yield."
UPLOAD_NAME = "functional-upload"


@pytest.fixture(scope="module")
def service(tmp_path_factory):
    """Boot uvicorn over a throwaway voice folder seeded from `service/voices`, with the test password."""
    folder = tmp_path_factory.mktemp("webapp")
    reference = folder / "reference.wav"
    reference.write_bytes((support.PROJECT / "service/voices/grimaldus.wav").read_bytes())
    transcript = (support.PROJECT / "service/voices/grimaldus.txt").read_text()
    port = support.free_port()
    (W / "logs").mkdir(parents=True, exist_ok=True)
    log = (W / "logs/functional-webapp-uvicorn.log").open("w")
    env = os.environ.copy()
    env.pop("HF_TOKEN", None)  # GET /settings must start with no token
    env.update({
        "ENGINE": "s2pro",
        "IDLE_UNLOAD_SECONDS": "600",
        "S2PRO_PASSWORD": support.PASSWORD,
        "TOKENS_FILE": str(folder / "tokens.json"),
        "VOICES_DIR": str(folder / "voices"),
        "SEED_VOICES_DIR": str(support.PROJECT / "service/voices"),
        "PYTHONPATH": f"{support.PROJECT}/service:{support.PROJECT}/src/fish:{support.PROJECT}/src",
    })
    if support.FFMPEG_DIR:
        env["PATH"] = f"{support.FFMPEG_DIR}:{env['PATH']}"
    process = subprocess.Popen(
        [str(support.PYTHON), "-m", "uvicorn", "app:app", "--app-dir", "service",
         "--host", "127.0.0.1", "--port", str(port)],
        cwd=support.PROJECT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    (W / "functional").mkdir(parents=True, exist_ok=True)
    (W / "functional/webapp.pid").write_text(str(process.pid))
    (W / "functional/webapp.port").write_text(str(port))
    base = f"http://127.0.0.1:{port}"
    try:
        support.wait_for(lambda: support.get_json(f"{base}/health")["status"] == "ok", 60,
                         "the service to answer /health")
        client = support.login(base)
        warm = support.post_speak(base, {"text": "Warm the engine.", "voice": "grimaldus"},
                                  timeout=300, client=client)
        assert warm.status_code == 200
        support.wait_for(lambda: support.get_json(f"{base}/health")["busy"] is False, 30,
                         "the engine to finish the warm-up")
        yield SimpleNamespace(base=base, client=client, reference=reference, transcript=transcript)
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        log.close()


def test_page_is_served(service):
    """GET / is an HTML page carrying every element id the page's script uses."""
    response = httpx.get(f"{service.base}/", timeout=30)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    missing = [element for element in support.PAGE_IDS if f'id="{element}"' not in response.text]
    assert not missing, missing


def test_the_page_starts_on_the_login_form(service):
    """Without a session the app section is hidden; a wrong password is 401 and the right one opens it."""
    page = httpx.get(f"{service.base}/", timeout=30).text
    assert 'id="login-form"' in page
    assert '<div id="app-section" hidden>' in page
    anonymous = httpx.Client(timeout=30)
    assert anonymous.get(f"{service.base}/session").json() == {"authenticated": False}
    assert anonymous.post(f"{service.base}/login", json={"password": "wrong"}).status_code == 401
    assert anonymous.get(f"{service.base}/settings").status_code == 401
    login = anonymous.post(f"{service.base}/login", json={"password": support.PASSWORD})
    assert login.status_code == 200
    assert anonymous.get(f"{service.base}/session").json() == {"authenticated": True}
    assert anonymous.get(f"{service.base}/settings").status_code == 200


def test_settings_token_stays_in_memory(service):
    """The token starts unset, a POST sets it, an empty POST clears it, and no response carries it."""
    token = f"hf_{uuid.uuid4().hex}"
    assert support.get_json(f"{service.base}/settings", client=service.client)["hf_token_set"] is False
    set_response = service.client.post(f"{service.base}/settings/hf-token", json={"token": token}, timeout=30)
    assert set_response.status_code == 200
    assert set_response.json() == {"hf_token_set": True}
    assert token not in set_response.text
    assert support.get_json(f"{service.base}/settings", client=service.client)["hf_token_set"] is True
    clear_response = service.client.post(f"{service.base}/settings/hf-token", json={"token": ""}, timeout=30)
    assert clear_response.status_code == 200
    assert clear_response.json() == {"hf_token_set": False}
    assert token not in clear_response.text
    assert support.get_json(f"{service.base}/settings", client=service.client)["hf_token_set"] is False


def test_upload_reference(service):
    """A reference WAV and its transcript become a voice listed by both engines, and `uploaded` marks it."""
    response = service.client.post(
        f"{service.base}/voices",
        data={"name": UPLOAD_NAME, "text": service.transcript},
        files={"file": ("reference.wav", service.reference.read_bytes(), "audio/wav")},
        timeout=60)
    assert response.status_code == 201, response.text
    assert response.json() == {"name": UPLOAD_NAME}
    voices = support.get_json(f"{service.base}/voices", client=service.client)
    assert UPLOAD_NAME in voices["voices"]["s2pro"]
    assert UPLOAD_NAME in voices["uploaded"]
    assert "grimaldus" not in voices["uploaded"]


def test_speak_with_the_uploaded_voice(service):
    """POST /speak clones the uploaded voice, answers audio/mpeg and ffprobe reads an MP3 with a duration."""
    response = support.post_speak(service.base, {"text": SENTENCE, "voice": UPLOAD_NAME},
                                  client=service.client)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("audio/mpeg")
    out = W / "functional-upload.mp3"
    out.write_bytes(response.content)
    probe = subprocess.run(
        [support.tool("ffprobe"), "-v", "error", "-show_entries", "format=format_name,duration",
         "-of", "json", str(out)],
        capture_output=True, text=True, check=True)
    found = json.loads(probe.stdout)["format"]
    assert "mp3" in found["format_name"]
    assert float(found["duration"]) > 0


def test_delete_rules(service):
    """An uploaded voice deletes; a bundled one is refused with 409; an unknown name is 404."""
    deleted = service.client.delete(f"{service.base}/voices/{UPLOAD_NAME}", timeout=30)
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": UPLOAD_NAME}
    voices = support.get_json(f"{service.base}/voices", client=service.client)
    assert UPLOAD_NAME not in voices["voices"]["s2pro"]
    assert UPLOAD_NAME not in voices["uploaded"]
    assert service.client.delete(f"{service.base}/voices/grimaldus", timeout=30).status_code == 409
    assert service.client.delete(f"{service.base}/voices/nobody", timeout=30).status_code == 404


def test_api_token_round_trip(service):
    """The session creates a token, the token speaks as Bearer, and after revoke it is 401."""
    created = service.client.post(f"{service.base}/tokens", json={"name": "functional-webapp"}, timeout=30)
    assert created.status_code == 201, created.text
    token = created.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    anonymous = httpx.Client(timeout=30)
    assert anonymous.get(f"{service.base}/voices", headers=headers).status_code == 200
    assert anonymous.get(f"{service.base}/settings", headers=headers).status_code == 401
    spoken = anonymous.post(f"{service.base}/speak", json={"text": SENTENCE, "voice": "grimaldus"},
                            headers=headers, timeout=240)
    assert spoken.status_code == 200, spoken.text
    revoked = service.client.delete(f"{service.base}/tokens/functional-webapp", timeout=30)
    assert revoked.json() == {"deleted": "functional-webapp"}
    assert anonymous.get(f"{service.base}/voices", headers=headers).status_code == 401


def test_service_voices_is_unchanged(service):
    """The run never wrote into `service/voices`: it holds the two bundled files and nothing else."""
    names = sorted(path.name for path in (support.PROJECT / "service/voices").iterdir())
    assert names == ["grimaldus.txt", "grimaldus.wav"]
