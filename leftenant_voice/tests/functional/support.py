"""Helpers for the functional suite: boot the real service and talk to it over HTTP and Docker."""
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT / ".venv-fish/bin/python"
W = PROJECT / "tmp/workflows/goal-trackers"
LOG_DIR = W / "logs"
VERSION = (PROJECT / "service/VERSION").read_text().strip()
IMAGE = f"registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:{VERSION}"
CONTAINER = "s2pro-functional-test"
NO_NETWORK_CONTAINER = "s2pro-functional-test-empty"
COLD_VOLUME = "s2pro-hf-functional"
EMPTY_VOLUME = "s2pro-hf-functional-empty"
# The password the test services boot with; the same value reaches the service and the login helper
PASSWORD = os.environ.get("S2PRO_PASSWORD", "functional-test-password")
# The element ids the page must carry; both the native and the container checks read this one list.
PAGE_IDS = ("service-status", "token-form", "token-input", "token-state", "engine-select",
            "voice-select", "upload-form", "upload-name", "upload-text", "upload-file",
            "uploaded-list", "speak-form", "speak-text", "speak-button", "player", "message",
            "login-form", "login-password", "login-button", "logout-button", "app-section",
            "api-token-form", "api-token-name", "api-token-create", "api-token-list")


def _ffmpeg_dir() -> str | None:
    """A folder holding ffmpeg and ffprobe the tests can name directly; None when PATH has both.

    This workstation has no system ffmpeg; the earlier service check built a copy in wip/. A host with
    ffmpeg on PATH needs nothing.
    """
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return None
    local = PROJECT / "wip/s2pro-service/verify/bin"
    if (local / "ffmpeg").is_file() and (local / "ffprobe").is_file():
        return str(local)
    raise RuntimeError("ffmpeg and ffprobe are not on PATH and wip/s2pro-service/verify/bin has no copy")


FFMPEG_DIR = _ffmpeg_dir()


def tool(name: str) -> str:
    """The ffmpeg or ffprobe command to run: its bare name on PATH, else the local copy."""
    return name if FFMPEG_DIR is None else str(Path(FFMPEG_DIR) / name)


def free_port() -> int:
    """A TCP port that is free on the loopback interface right now."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(check, timeout: float, description: str, interval: float = 1.0):
    """Call `check` until it returns something true, or fail naming what never happened."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = check()
        except (httpx.HTTPError, OSError):
            result = None
        if result:
            return result
        time.sleep(interval)
    raise AssertionError(f"timed out after {timeout:.0f} s waiting for {description}")


def get_json(url: str, timeout: float = 30, client: httpx.Client | None = None) -> dict:
    """GET `url` and decode its JSON body; `client` carries the session cookie when given."""
    return (client or httpx).get(url, timeout=timeout).json()


def post_speak(base: str, body: dict, timeout: float = 240,
               client: httpx.Client | None = None) -> httpx.Response:
    """POST /speak and return the response; the model may load or speak for a minute."""
    return (client or httpx).post(f"{base}/speak", json=body, timeout=timeout)


def login(base: str, password: str = PASSWORD) -> httpx.Client:
    """A client holding a login session for `base`."""
    client = httpx.Client(timeout=30)
    response = client.post(f"{base}/login", json={"password": password})
    assert response.status_code == 200, response.text
    return client


def docker(*args: str, timeout: float = 120) -> subprocess.CompletedProcess:
    """Run one Docker CLI command and return its result."""
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)


def container_health(name: str = CONTAINER) -> dict | None:
    """The service's /health body from inside the test container, or None while it does not answer."""
    result = docker("exec", name, "curl", "-fsS", "http://localhost:8000/health", timeout=30)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def container_login(name: str = CONTAINER) -> subprocess.CompletedProcess:
    """Log in inside the test container; stdout is the status code, the cookie goes to /tmp/s2pro-cookies."""
    return docker("exec", name, "curl", "-sS", "-o", "/dev/null", "-c", "/tmp/s2pro-cookies",
                  "-X", "POST", "http://localhost:8000/login", "-H", "Content-Type: application/json",
                  "-d", json.dumps({"password": PASSWORD}), "-w", "%{http_code}")


def container_speak(body: str, out: str | None = None,
                    name: str = CONTAINER) -> subprocess.CompletedProcess:
    """POST /speak from inside the test container with its session cookie, status on stdout."""
    args = ["exec", name, "curl", "-sS", "-b", "/tmp/s2pro-cookies",
            "-X", "POST", "http://localhost:8000/speak",
            "-H", "Content-Type: application/json", "-d", body]
    if out:
        args += ["-o", out]
    args += ["-w", "%{http_code} %{content_type}"]
    return docker(*args, timeout=900)


def container_logs(name: str = CONTAINER) -> str:
    """Everything the container wrote to stdout and stderr."""
    result = docker("logs", name)
    return result.stdout + result.stderr
