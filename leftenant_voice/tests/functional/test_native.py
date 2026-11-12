"""The real service, booted natively on the GPU the queue chose: MP3, error codes, idle unload and reload."""
import json
import os
import signal
import subprocess
import threading
import time
from types import SimpleNamespace

import httpx
import pytest
import support

SENTENCE = "Brothers, we stand upon the wall and we do not yield."
LONG_TEXT = ("The reactor hums beneath the deck and the servitors keep their vigil. "
             "Count the shells before the gate opens and hold the line. "
             "The wall does not yield while one brother stands.")


@pytest.fixture(scope="module")
def service():
    """Boot uvicorn with the pinned voice folder, IDLE_UNLOAD_SECONDS=15 and the test password."""
    port = support.free_port()
    support.LOG_DIR.mkdir(parents=True, exist_ok=True)
    tokens_file = support.W / "functional-native-tokens.json"
    tokens_file.unlink(missing_ok=True)
    log = (support.LOG_DIR / "functional-native-uvicorn.log").open("w")
    env = os.environ.copy()
    env.update({
        "ENGINE": "s2pro",
        "IDLE_UNLOAD_SECONDS": "15",
        "MAX_TEXT_CHARS": "3000",
        "S2PRO_PASSWORD": support.PASSWORD,
        "TOKENS_FILE": str(tokens_file),
        "VOICES_DIR": str(support.PROJECT / "service/voices"),
        "PYTHONPATH": f"{support.PROJECT}/service:{support.PROJECT}/src/fish:{support.PROJECT}/src",
    })
    if support.FFMPEG_DIR:
        env["PATH"] = f"{support.FFMPEG_DIR}:{env['PATH']}"
    process = subprocess.Popen(
        [str(support.PYTHON), "-m", "uvicorn", "app:app", "--app-dir", "service",
         "--host", "127.0.0.1", "--port", str(port)],
        cwd=support.PROJECT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    (support.W / "functional").mkdir(parents=True, exist_ok=True)
    (support.W / "functional/native.pid").write_text(str(process.pid))
    (support.W / "functional/native.port").write_text(str(port))
    base = f"http://127.0.0.1:{port}"
    try:
        support.wait_for(lambda: support.get_json(f"{base}/health")["status"] == "ok", 60,
                         "the service to answer /health")
        client = support.login(base)
        # The first request waits for the background load and resets the idle clock; with IDLE_UNLOAD_SECONDS
        # shorter than the load, a wait for "loaded" alone would race the idle watcher's first unload.
        warm = support.post_speak(base, {"text": "Warm the engine.", "voice": "grimaldus"},
                                  timeout=300, client=client)
        assert warm.status_code == 200
        yield SimpleNamespace(base=base, client=client)
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


def test_health_and_voices(service):
    """GET /health reports the loaded engine; GET /voices lists grimaldus under s2pro."""
    health = support.get_json(f"{service.base}/health")
    assert health["status"] == "ok"
    assert health["loaded"] is True
    assert health["busy"] is False
    assert health["engine"] == "s2pro"
    voices = support.get_json(f"{service.base}/voices", client=service.client)
    assert "grimaldus" in voices["voices"]["s2pro"]


def test_no_credentials_is_401(service):
    """A protected endpoint without the cookie is 401; the logged-in client gets it."""
    assert httpx.get(f"{service.base}/voices", timeout=30).status_code == 401
    assert service.client.get(f"{service.base}/voices", timeout=30).status_code == 200


def test_speak_returns_an_mp3(service):
    """A real synthesis answers audio/mpeg and ffprobe reads the file as an MP3 with a duration."""
    response = support.post_speak(service.base, {"text": SENTENCE, "voice": "grimaldus"},
                                  client=service.client)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert response.content.startswith(b"ID3")
    out = support.W / "functional-native.mp3"
    out.write_bytes(response.content)
    probe = subprocess.run(
        [support.tool("ffprobe"), "-v", "error", "-show_entries", "format=format_name,duration",
         "-of", "json", str(out)],
        capture_output=True, text=True, check=True)
    found = json.loads(probe.stdout)["format"]
    assert "mp3" in found["format_name"]
    assert float(found["duration"]) > 0


def test_error_codes(service):
    """Empty text, too long text, an unknown voice and an unknown engine are 4xx with a message."""
    empty = support.post_speak(service.base, {"text": "", "voice": "grimaldus"}, client=service.client)
    assert empty.status_code == 422 and "text is empty" in empty.text
    long = support.post_speak(service.base, {"text": "x" * 3001, "voice": "grimaldus"},
                              client=service.client)
    assert long.status_code == 422 and "3000" in long.text
    voice = support.post_speak(service.base, {"text": "hello", "voice": "nobody"}, client=service.client)
    assert voice.status_code == 404 and "grimaldus" in voice.text
    engine = support.post_speak(service.base, {"text": "hello", "voice": "grimaldus", "engine": "nope"},
                                client=service.client)
    assert engine.status_code == 404 and "s2pro" in engine.text


def test_a_token_speaks_and_revoking_it_refuses(service):
    """The session creates a token, the token speaks as Bearer, and after revoke it is 401."""
    created = service.client.post(f"{service.base}/tokens", json={"name": "functional-native"}, timeout=30)
    assert created.status_code == 201, created.text
    headers = {"Authorization": f"Bearer {created.json()['token']}"}
    anonymous = httpx.Client(timeout=30)
    spoken = anonymous.post(f"{service.base}/speak",
                            json={"text": "The wall holds.", "voice": "grimaldus"},
                            headers=headers, timeout=300)
    assert spoken.status_code == 200, spoken.text
    revoked = service.client.delete(f"{service.base}/tokens/functional-native", timeout=30)
    assert revoked.json() == {"deleted": "functional-native"}
    refused = anonymous.post(f"{service.base}/speak", json={"text": "hello", "voice": "grimaldus"},
                             headers=headers, timeout=30)
    assert refused.status_code == 401


def _warm_up(service) -> None:
    """Speak a short sentence so the model is loaded and the idle countdown starts now."""
    response = support.post_speak(service.base, {"text": "Warm the engine.", "voice": "grimaldus"},
                                  timeout=300, client=service.client)
    assert response.status_code == 200
    support.wait_for(lambda: support.get_json(f"{service.base}/health")["busy"] is False, 30,
                     "the engine to finish the warm-up")


def test_no_unload_during_a_synthesis(service):
    """With a 15 s idle time, a synthesis longer than it holds the lock; /health stays loaded."""
    _warm_up(service)
    answer = {}

    def speak():
        answer["response"] = support.post_speak(
            service.base, {"text": LONG_TEXT, "voice": "grimaldus"}, timeout=300, client=service.client)

    worker = threading.Thread(target=speak)
    started = time.monotonic()
    worker.start()
    samples = []
    while worker.is_alive():
        samples.append(support.get_json(f"{service.base}/health"))
        time.sleep(0.5)
    worker.join()
    elapsed = time.monotonic() - started
    assert answer["response"].status_code == 200
    assert elapsed > 15, f"the synthesis ({elapsed:.1f} s) did not outlast the 15 s idle window"
    assert samples and any(sample["busy"] for sample in samples), "the synthesis was never seen as busy"
    assert all(sample["loaded"] for sample in samples), "the model was unloaded during the synthesis"


def test_idle_unload_and_reload(service):
    """The watcher unloads after 15 s idle; /health reports it, and the next request reloads and speaks."""
    support.wait_for(lambda: support.get_json(f"{service.base}/health")["loaded"] is False, 40,
                     "the idle watcher to unload the model")
    health = support.get_json(f"{service.base}/health")
    assert health["seconds_until_unload"] is None
    response = support.post_speak(service.base, {"text": "The wall holds.", "voice": "grimaldus"},
                                  timeout=300, client=service.client)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert support.get_json(f"{service.base}/health")["loaded"] is True
