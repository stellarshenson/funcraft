"""The image pulls S2 Pro from Hugging Face into a named volume: a cold start, a warm restart, a failed pull."""
import json
import os
import re
import subprocess
import time

import pytest
import support

COLD_SECONDS = 3600   # about 11 GB from Hugging Face, then the model build
WARM_SECONDS = 900    # the model build alone, from the volume
FAILURE_SECONDS = 600  # the Hugging Face client's retries with no network


def _image_exists() -> bool:
    return support.docker("image", "inspect", support.IMAGE).returncode == 0


def _gpu_containers_run(gpu: str) -> bool:
    probe = support.docker("run", "--rm", "--gpus", f"device={gpu}",
                           "--entrypoint", "true", support.IMAGE, timeout=300)
    return probe.returncode == 0


def _host_gpu() -> str:
    """The GPU index the queue chose, as Docker's host-side device id."""
    return os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(",")[0]


def _start(name: str, volume: str, gpu: str | None = None, network: str | None = None) -> float:
    """Start the image detached on one data volume at /data with the test password; return the start time."""
    args = ["run", "-d", "--name", name, "-e", "IDLE_UNLOAD_SECONDS=600",
            "-e", f"S2PRO_PASSWORD={support.PASSWORD}", "-v", f"{volume}:/data"]
    if gpu is not None:
        args += ["--gpus", f"device={gpu}"]
    if network is not None:
        args += ["--network", network]
    started = time.monotonic()
    run = support.docker(*args, support.IMAGE, timeout=300)
    assert run.returncode == 0, run.stderr
    return started


def _running(name: str) -> bool | None:
    """True when running, False when it has exited, None when Docker cannot answer."""
    result = support.docker("inspect", "-f", "{{.State.Running}}", name)
    if result.returncode != 0:
        return None
    return result.stdout.strip() == "true"


def _health_or_fail(name: str) -> dict | None:
    """The /health body, or an error carrying the log tail when the container has exited."""
    health = support.container_health(name)
    if health is None and _running(name) is False:
        raise AssertionError(f"the container exited; log tail:\n{support.container_logs(name)[-2000:]}")
    return health


def _wait_for_state(name: str, wanted: str, timeout: float) -> list[str]:
    """Poll /health until `state` is `wanted`; return every state seen in order."""
    started = time.monotonic()
    health = support.wait_for(lambda: _health_or_fail(name), min(timeout, 180),
                              "the container to answer /health")
    states = [health["state"]]
    while states[-1] != wanted and time.monotonic() - started < timeout:
        time.sleep(2)
        health = _health_or_fail(name)
        if health and health["state"] != states[-1]:
            states.append(health["state"])
    assert states[-1] == wanted, f"states seen: {states}"
    return states


def _error_state(name: str) -> dict | None:
    """The /health body once the failed load is reported, else None."""
    health = _health_or_fail(name)
    return health if health and health["state"] == "error" else None


def _container_get(path: str, cookies: bool = True) -> tuple[int, str, str]:
    """The status code, content type and body of a GET from inside the test container.

    `cookies` sends the session cookie that `support.container_login` stored, for a protected path.
    """
    args = ["exec", support.CONTAINER, "curl", "-sS"]
    if cookies:
        args += ["-b", "/tmp/s2pro-cookies"]
    args += ["-w", "\n%{http_code} %{content_type}", f"http://localhost:8000{path}"]
    result = support.docker(*args)
    assert result.returncode == 0, result.stderr
    body, _, status = result.stdout.rpartition("\n")
    code, content_type = status.split(" ", 1)
    return int(code), content_type, body


def _docker_health(name: str) -> str | None:
    """The container's Docker health status once it is healthy, else None."""
    status = support.docker("inspect", "-f", "{{.State.Health.Status}}", name).stdout.strip()
    return status if status == "healthy" else None


def _volume_bytes(volume: str) -> int:
    """The bytes the data volume at /data holds, measured from a throwaway container."""
    result = support.docker("run", "--rm", "-v", f"{volume}:/data",
                            "--entrypoint", "du", support.IMAGE, "-sb", "/data",
                            timeout=300)
    assert result.returncode == 0, result.stderr
    return int(result.stdout.split()[0])


def _download_seconds(log: str) -> int | None:
    """The seconds the engine logged for its Hugging Face fetch, or None when the log has no fetch."""
    found = re.search(r"download finished in (\d+) s", log)
    return int(found.group(1)) if found else None


def _write_log(log: str, filename: str) -> None:
    """Keep a captured container log in the suite's log folder, so a failure leaves its evidence."""
    support.LOG_DIR.mkdir(parents=True, exist_ok=True)
    (support.LOG_DIR / filename).write_text(log)


def _write_record(record: dict, filename: str) -> None:
    """Keep the measured states, times and size beside the log; the log itself is a separate file."""
    support.LOG_DIR.mkdir(parents=True, exist_ok=True)
    (support.LOG_DIR / filename).write_text(
        json.dumps({key: value for key, value in record.items() if key != "log"}, indent=1))


@pytest.fixture(scope="module")
def cold():
    """A fresh named volume and the first start: the weights come from Hugging Face."""
    if not _image_exists():
        pytest.skip(f"{support.IMAGE} is not in the image store")
    gpu = _host_gpu()
    if not _gpu_containers_run(gpu):
        pytest.skip("the Docker daemon does not run GPU containers")
    support.docker("rm", "-f", support.CONTAINER)
    support.docker("volume", "rm", "-f", support.COLD_VOLUME)
    record = {"states": None, "seconds": None, "log": "", "bytes": 0}
    try:
        started = _start(support.CONTAINER, support.COLD_VOLUME, gpu=gpu)
        record["states"] = _wait_for_state(support.CONTAINER, "ready", COLD_SECONDS)
        login = support.container_login()
        assert login.stdout.strip() == "200", login.stdout + login.stderr
        record["seconds"] = round(time.monotonic() - started)
        record["log"] = support.container_logs(support.CONTAINER)
        record["download_seconds"] = _download_seconds(record["log"])
        record["bytes"] = _volume_bytes(support.COLD_VOLUME)
        yield record
    finally:
        _write_log(record["log"] or support.container_logs(support.CONTAINER),
                   "functional-container-cold.log")
        _write_record(record, "functional-container-cold.json")
        support.docker("rm", "-f", support.CONTAINER, timeout=300)
        support.docker("volume", "rm", "-f", support.COLD_VOLUME, timeout=300)


@pytest.fixture(scope="module")
def warm(cold):
    """A second start on the same volume: the weights come from the volume, not the network."""
    support.docker("rm", "-f", support.CONTAINER, timeout=300)
    record = {"states": None, "seconds": None, "log": "", "load_seconds": None}
    try:
        started = _start(support.CONTAINER, support.COLD_VOLUME, gpu=_host_gpu())
        record["states"] = _wait_for_state(support.CONTAINER, "ready", WARM_SECONDS)
        login = support.container_login()
        assert login.stdout.strip() == "200", login.stdout + login.stderr
        record["seconds"] = round(time.monotonic() - started)
        record["log"] = support.container_logs(support.CONTAINER)
        found = re.search(r"engine s2pro loaded in (\d+) s", record["log"])
        record["load_seconds"] = int(found.group(1)) if found else None
        yield record
    finally:
        _write_log(record["log"] or support.container_logs(support.CONTAINER),
                   "functional-container-warm.log")
        _write_record(record, "functional-container-warm.json")
        support.docker("rm", "-f", support.CONTAINER, timeout=300)


def test_cold_start_downloads_from_hugging_face(cold):
    """The log shows the fetch and /health moves downloading then ready; the volume holds the weights."""
    states = cold["states"]
    assert "downloading" in states and "ready" in states, states
    assert states.index("downloading") < states.index("ready"), states
    assert "downloading fishaudio/s2-pro" in cold["log"]
    assert _download_seconds(cold["log"]) is not None
    assert cold["bytes"] > 5 * 1024 ** 3, f"the volume holds {cold['bytes']} bytes"


def test_container_is_healthy(cold):
    """docker ps reports healthy by the time the model has loaded, not starting."""
    assert support.wait_for(lambda: _docker_health(support.CONTAINER), 120,
                            "the container to report healthy") == "healthy"


def test_container_lists_its_voices(cold):
    """The image carries grimaldus, and the host-only AuK engine is unknown there."""
    code, _, body = _container_get("/voices")
    assert code == 200
    voices = json.loads(body)
    assert "grimaldus" in voices["voices"]["s2pro"]
    assert "auk-flash" not in voices["voices"]
    response = support.container_speak('{"text":"hello","voice":"grimaldus","engine":"auk-flash"}')
    assert response.stdout.strip().endswith("404 application/json"), response.stdout


def test_container_serves_the_page_and_the_settings(cold):
    """Inside the container: the page and its ids, no token, and /voices is 401 before a login."""
    code, content_type, body = _container_get("/")
    assert code == 200 and content_type.split(";")[0] == "text/html", (code, content_type)
    missing = [element for element in support.PAGE_IDS if f'id="{element}"' not in body]
    assert not missing, missing
    code, _, body = _container_get("/voices", cookies=False)
    assert code == 401
    code, _, body = _container_get("/settings")
    assert code == 200
    assert json.loads(body)["hf_token_set"] is False
    code, _, body = _container_get("/voices")
    assert code == 200
    voices = json.loads(body)
    assert "grimaldus" in voices["voices"]["s2pro"]
    assert voices["uploaded"] == []


def test_cold_start_serves_an_mp3(cold):
    """POST /speak in the container answers audio/mpeg and the copied file is an MP3."""
    response = support.container_speak(
        '{"text":"Brothers, we stand upon the wall and we do not yield.","voice":"grimaldus"}',
        out="/tmp/speech.mp3")
    assert response.stdout.strip() == "200 audio/mpeg", response.stdout + response.stderr
    out = support.W / "functional-container.mp3"
    copy = support.docker("cp", f"{support.CONTAINER}:/tmp/speech.mp3", str(out))
    assert copy.returncode == 0, copy.stderr
    assert out.read_bytes().startswith(b"ID3")
    probe = subprocess.run(
        [support.tool("ffprobe"), "-v", "error", "-show_entries", "format=format_name,duration",
         "-of", "json", str(out)],
        capture_output=True, text=True, check=True)
    found = json.loads(probe.stdout)["format"]
    assert "mp3" in found["format_name"]
    assert float(found["duration"]) > 0


def test_warm_start_downloads_nothing(warm):
    """The volume keeps the weights: the restart reports loading only and never fetches."""
    assert "downloading" not in warm["states"], warm["states"]
    assert warm["states"][-1] == "ready", warm["states"]
    assert "downloading fishaudio/s2-pro" not in warm["log"]
    assert "download finished" not in warm["log"]
    assert warm["load_seconds"] is not None, "the log has no engine load line"


def test_network_off_reports_the_failure():
    """An empty volume with no network: /health answers and reports the error, and /speak is a 500."""
    if not _image_exists():
        pytest.skip(f"{support.IMAGE} is not in the image store")
    support.docker("rm", "-f", support.NO_NETWORK_CONTAINER)
    support.docker("volume", "rm", "-f", support.EMPTY_VOLUME)
    record = {}
    try:
        started = _start(support.NO_NETWORK_CONTAINER, support.EMPTY_VOLUME, network="none")
        first = support.wait_for(lambda: _health_or_fail(support.NO_NETWORK_CONTAINER), 180,
                                 "/health to answer during the failed download")
        assert first["loaded"] is False
        record["first_state"] = first["state"]
        login = support.container_login(support.NO_NETWORK_CONTAINER)
        assert login.stdout.strip() == "200", login.stdout + login.stderr
        begin = time.monotonic()
        assert _health_or_fail(support.NO_NETWORK_CONTAINER) is not None
        assert time.monotonic() - begin < 10, "/health did not answer promptly"
        health = support.wait_for(lambda: _error_state(support.NO_NETWORK_CONTAINER), FAILURE_SECONDS,
                                  "the failed download to report error")
        assert "could not be loaded" in health["error"], health
        record["error_seconds"] = round(time.monotonic() - started)
        record["error"] = health["error"]
        assert record["error_seconds"] < FAILURE_SECONDS
        response = support.container_speak('{"text":"hello","voice":"grimaldus"}',
                                           name=support.NO_NETWORK_CONTAINER)
        assert response.stdout.strip().endswith("500 application/json"), response.stdout + response.stderr
        assert "could not be loaded" in response.stdout, response.stdout
    finally:
        _write_log(support.container_logs(support.NO_NETWORK_CONTAINER),
                   "functional-container-no-network.log")
        _write_record(record, "functional-container-no-network.json")
        support.docker("rm", "-f", support.NO_NETWORK_CONTAINER, timeout=300)
        support.docker("volume", "rm", "-f", support.EMPTY_VOLUME, timeout=300)


def test_a_start_without_a_password_stops_with_the_message():
    """The image alone carries no password: the process exits non-zero and names both variables."""
    if not _image_exists():
        pytest.skip(f"{support.IMAGE} is not in the image store")
    name = "s2pro-functional-test-nopassword"
    support.docker("rm", "-f", name)
    started = support.docker("run", "-d", "--name", name, support.IMAGE, timeout=300)
    assert started.returncode == 0, started.stderr
    try:
        code = support.docker("wait", name, timeout=300).stdout.strip()
        log = support.container_logs(name)
        assert code != "0", log
        assert "no password: set S2PRO_PASSWORD_FILE or S2PRO_PASSWORD" in log, log[-2000:]
    finally:
        support.docker("rm", "-f", name, timeout=300)
