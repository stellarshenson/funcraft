"""AuK-Flash as a child-process engine over the trial script wip/tts-trial/auk/speak_auk.py.

The AuK model runs in `.venv-auk` through `service/auk_worker.py`; its interpreter is never the service's.
The engine hides the process: `load()` starts the worker and waits for its ready line, `speak()` sends one
JSON request and reads back the samples, `unload()` stops the worker, which frees the GPU.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from engine import EngineError, LoadReport, voice_names

ROOT = Path(__file__).resolve().parents[1]
AUK_PYTHON = ROOT / ".venv-auk/bin/python"
WORKER = Path(__file__).resolve().with_name("auk_worker.py")
TRIAL = ROOT / "wip/tts-trial/auk/speak_auk.py"
STOP_SECONDS = 10


class AukEngine:
    """AuK-Flash in a child process; one model load serves every request until `unload()`."""

    name = "auk-flash"

    def __init__(self, voices_dir: Path) -> None:
        """Remember the voice folder; nothing starts until `load()`.

        Args:
            voices_dir: folder of `<voice>.wav` + `<voice>.txt` pairs.
        """
        self.voices_dir = Path(voices_dir)
        self._process: subprocess.Popen | None = None
        self._folder: Path | None = None
        self._log = None

    def load(self, report: LoadReport | None = None) -> None:
        """Start the worker in .venv-auk and wait until it reports the model loaded.

        Args:
            report: unused; the worker reports ready when the model is loaded.

        Raises:
            EngineError: the worker exited or reported an error instead of ready.
        """
        if self._process is not None:
            return
        self._folder = Path(tempfile.mkdtemp(prefix="auk-engine-"))
        self._log = (self._folder / "worker.log").open("w")
        try:
            self._start()
        except Exception as error:  # the worker exited or broke its protocol; its log says why
            reason = self._log_tail()
            self.unload()
            raise EngineError(f"the auk-flash worker did not start: {reason}") from error

    def _start(self) -> None:
        """Spawn the worker and wait for its ready line.

        Raises:
            EngineError: the worker closed its output or sent a line that is not ready.
        """
        self._process = subprocess.Popen(
            [str(AUK_PYTHON), str(WORKER), "--trial", str(TRIAL), "--voices-dir", str(self.voices_dir)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._log, text=True, bufsize=1)
        ready = self._read()
        if not ready.get("ready"):
            raise EngineError(f"the auk-flash worker did not report ready: {ready}")

    def unload(self) -> None:
        """Stop the worker, freeing its GPU memory, and remove its temporary folder; safe to repeat."""
        process, folder, log = self._process, self._folder, self._log
        self._process, self._folder, self._log = None, None, None
        if process is not None:
            try:
                process.stdin.write('{"quit": true}\n')
                process.stdin.flush()
                process.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            try:
                process.wait(timeout=STOP_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if log is not None:
            log.close()
        if folder is not None:
            shutil.rmtree(folder, ignore_errors=True)

    def speak(self, text: str, voice: str) -> tuple[np.ndarray, int]:
        """Send one request to the worker and read the samples it wrote.

        Raises:
            EngineError: the worker stopped, or reported an error.
        """
        if self._process is None or self._folder is None:
            raise EngineError("the auk-flash engine is not loaded")
        out = self._folder / "speech.f32"
        try:
            self._process.stdin.write(json.dumps({"text": text, "voice": voice, "out": str(out)}) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise EngineError(f"the auk-flash worker stopped: {self._log_tail()}") from error
        reply = self._read()
        if not reply.get("ok"):
            raise EngineError(str(reply.get("error", "the auk-flash worker failed")))
        return np.fromfile(out, dtype="<f4"), int(reply["rate"])

    def voices(self) -> list[str]:
        """The voices in the shared voices folder."""
        return voice_names(self.voices_dir)

    def _read(self) -> dict:
        """One protocol line from the worker.

        Raises:
            EngineError: the worker closed its output or wrote a line that is not JSON.
        """
        line = self._process.stdout.readline()
        if not line:
            raise EngineError(f"the auk-flash worker stopped: {self._log_tail()}")
        try:
            return json.loads(line)
        except json.JSONDecodeError as error:
            raise EngineError(f"the auk-flash worker sent a bad line {line!r}: {error}") from error

    def _log_tail(self, lines: int = 5) -> str:
        """The last stderr lines of the worker, for an error message."""
        if self._folder is None:
            return "no worker log"
        try:
            tail = (self._folder / "worker.log").read_text(errors="replace").splitlines()[-lines:]
        except OSError:
            return "no worker log"
        return " | ".join(tail) or "no worker output"
