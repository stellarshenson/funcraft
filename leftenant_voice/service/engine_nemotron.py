"""Nemotron 3.5 Transcribe as a child-process engine over `service/nemotron_worker.py`.

The model runs in the ASR interpreter (`/opt/venv` in the image, `.venv-asr` natively) through
`service/nemotron_worker.py`; its torch and Transformers stay in that child process's modules. The engine
hides the process: `load()` starts the worker and waits for its ready line, `transcribe_window()` sends one
JSON request and reads back the text, `unload()` stops the worker, which frees the GPU.
"""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

import numpy as np

from engine import EngineError, LoadReport

ROOT = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).resolve().with_name("nemotron_worker.py")
IMAGE_PYTHON = Path("/opt/venv/bin/python")
LOCAL_PYTHON = ROOT / ".venv-asr/bin/python"
STOP_SECONDS = 10


class NemotronTranscriber:
    """Nemotron 3.5 Transcribe in a child process; one model load serves every window until `unload()`."""

    def __init__(self, token: Callable[[], str | None] = lambda: None) -> None:
        """Nothing starts until `load()`.

        Args:
            token: returns the Hugging Face token or None; read when the worker starts, so a token set
                through the page is used without a restart.
        """
        self.token = token
        self._process: subprocess.Popen | None = None
        self._folder: Path | None = None
        self._log = None

    def python_path(self) -> Path:
        """The worker's interpreter: `ASR_PYTHON`, else `/opt/venv`, else the project's `.venv-asr`."""
        override = os.environ.get("ASR_PYTHON")
        if override:
            return Path(override)
        return IMAGE_PYTHON if IMAGE_PYTHON.is_file() else LOCAL_PYTHON

    def available(self) -> bool:
        """Whether the worker's interpreter is installed."""
        return self.python_path().is_file()

    def is_loaded(self) -> bool:
        """Whether the worker process is running."""
        return self._process is not None and self._process.poll() is None

    def load(self, report: LoadReport | None = None) -> None:
        """Start the worker on the ASR GPU and wait until it reports the model loaded.

        Args:
            report: unused; the worker reports ready when the model is loaded.

        Raises:
            EngineError: the interpreter is missing, or the worker exited or reported an error instead
                of ready.
        """
        if self.is_loaded():
            return
        self.unload()  # a worker that died leaves its process and folder behind
        if not self.available():
            raise EngineError(f"the transcription interpreter is missing: {self.python_path()}")
        self._folder = Path(tempfile.mkdtemp(prefix="nemotron-engine-"))
        self._log = (self._folder / "worker.log").open("w")
        try:
            self._start()
        except Exception as error:  # the worker exited or broke its protocol; its log says why
            reason = self._log_tail()
            self.unload()
            raise EngineError(f"the nemotron worker did not start: {reason}") from error

    def _start(self) -> None:
        """Spawn the worker and wait for its ready line.

        Raises:
            EngineError: the worker closed its output or sent a line that is not ready.
        """
        # PCI bus order makes the index the nvidia-smi index, as src/transcribe.py measured on this workstation
        env = {**os.environ, "CUDA_DEVICE_ORDER": "PCI_BUS_ID",
               "CUDA_VISIBLE_DEVICES": os.environ.get("ASR_GPU_INDEX", "1")}
        token = self.token()
        if token:  # None keeps a container HF_TOKEN from os.environ
            env["HF_TOKEN"] = token
        self._process = subprocess.Popen(
            [str(self.python_path()), str(WORKER)], env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._log, text=True, bufsize=1)
        ready = self._read()
        if not ready.get("ready"):
            raise EngineError(f"the nemotron worker did not report ready: {ready}")

    def transcribe_window(self, samples: np.ndarray, prompt: str) -> str:
        """Transcribe one window and return the worker's text.

        Args:
            samples: mono float32 samples at `asr.SAMPLE_RATE`.
            prompt: the instruction `asr.build_prompt` built.

        Returns:
            The transcript of the window.

        Raises:
            EngineError: the engine is not loaded, the worker stopped, or it reported an error.
        """
        if self._process is None or self._folder is None:
            raise EngineError("the nemotron engine is not loaded")
        audio = self._folder / "window.f32"
        samples.astype("<f4").tofile(audio)
        try:
            self._process.stdin.write(json.dumps({"audio": str(audio), "prompt": prompt}) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise EngineError(f"the nemotron worker stopped: {self._log_tail()}") from error
        reply = self._read()
        if not reply.get("ok"):
            raise EngineError(str(reply.get("error", "the nemotron worker failed")))
        return str(reply["text"])

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

    def _read(self) -> dict:
        """One protocol line from the worker.

        Raises:
            EngineError: the worker closed its output or wrote a line that is not JSON.
        """
        line = self._process.stdout.readline()
        if not line:
            raise EngineError(f"the nemotron worker stopped: {self._log_tail()}")
        try:
            return json.loads(line)
        except json.JSONDecodeError as error:
            raise EngineError(f"the nemotron worker sent a bad line {line!r}: {error}") from error

    def _log_tail(self, lines: int = 5) -> str:
        """The last stderr lines of the worker, for an error message."""
        if self._folder is None:
            return "no worker log"
        try:
            tail = (self._folder / "worker.log").read_text(errors="replace").splitlines()[-lines:]
        except OSError:
            return "no worker log"
        return " | ".join(tail) or "no worker output"
