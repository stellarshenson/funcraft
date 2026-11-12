"""The settings app reads from the environment at import, including IDLE_UNLOAD_SECONDS.

Each check imports the app in a fresh interpreter with the environment set, because the constants are
fixed at import; the reported seconds-until-unload must follow the variable.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
SNIPPET = """
import json
import time

from fastapi.testclient import TestClient

import app

app.loaded_engine = "s2pro"
app.last_request = time.monotonic()
print(json.dumps({
    "idle_seconds": app.IDLE_UNLOAD_SECONDS,
    "default_engine": app.DEFAULT_ENGINE,
    "max_text_chars": app.MAX_TEXT_CHARS,
    "health": TestClient(app.app).get("/health").json(),
}))
"""


def settings_with(**values: str) -> dict:
    """Import the app in a subprocess with `values` in its environment and report its settings."""
    env = os.environ.copy()
    env.pop("IDLE_UNLOAD_SECONDS", None)
    env.update(values)
    env["PYTHONPATH"] = f"{PROJECT}/service:{PROJECT}/src/fish:{PROJECT}/src"
    result = subprocess.run([sys.executable, "-c", SNIPPET], cwd=PROJECT, env=env,
                            capture_output=True, text=True, timeout=120, check=True)
    return json.loads(result.stdout)


def test_settings_come_from_the_environment():
    found = settings_with(IDLE_UNLOAD_SECONDS="61", ENGINE="alpha", MAX_TEXT_CHARS="99")
    assert found["idle_seconds"] == 61.0
    assert found["default_engine"] == "alpha"
    assert found["max_text_chars"] == 99


def test_idle_unload_seconds_changes_the_reported_seconds():
    short = settings_with(IDLE_UNLOAD_SECONDS="61")
    long = settings_with(IDLE_UNLOAD_SECONDS="1800")
    assert 50 <= short["health"]["seconds_until_unload"] <= 61
    assert 1780 <= long["health"]["seconds_until_unload"] <= 1800


def test_idle_unload_seconds_defaults_to_3600():
    found = settings_with()
    assert found["idle_seconds"] == 3600.0
