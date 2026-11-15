"""HTTP API over the installed text-to-speech engines and Nemotron 3.5 Transcribe: POST /speak returns an MP3,
POST /transcribe returns text.

Run: `make -f s2pro.mk serve` (native) or the Docker image. Settings come from environment variables:
VOICES_DIR, ENGINE (default s2pro), MAX_TEXT_CHARS (default 3000), IDLE_UNLOAD_SECONDS (default 3600),
ASR_GPU_INDEX (default 1), ASR_PYTHON, S2PRO_PASSWORD_FILE or S2PRO_PASSWORD, TOKENS_FILE.

The service starts only with a password. `POST /login` opens an in-memory session with an HttpOnly cookie;
the session opens the page and manages API tokens. The token store is encrypted with the password, so a
service without it cannot read the tokens.

Access: `GET /`, `GET /health`, `POST /login` and `GET /session` are public; settings, token management and
model management need the session cookie; `/speak`, `/transcribe` and `/voices` accept the cookie or
`Authorization: Bearer <token>`. Every refusal is 401.

The default engine loads in the background at start, so `/health` answers while the model loads. One engine is
resident at a time: a request for another engine unloads the resident one first, because the models do not fit
one GPU together. After IDLE_UNLOAD_SECONDS without a request the resident engine is unloaded; the next request
loads it again. One lock covers load, unload and synthesis, so only one of them runs at a time.

`/health` reports the load as `state`: `downloading` while the weights come from Hugging Face, `loading` while
the model is built, `ready` when the last load succeeded, and `error` with the message in `error` when it failed.

`POST /transcribe` transcribes an uploaded recording with Nemotron 3.5 Transcribe, bf16 on GPU 2, in a child
process that loads in the background at start, as the default engine does. `/health`
reports it under `asr` as `available`, `loaded`, `state` and `error`; `state` is `downloading` while its 67.5 GB
cache is absent, `loading` while the model is built, `ready` or `error`. A request during the download or the
load answers 503 with `Retry-After: 30` instead of waiting, and a request that finds the state `down`, or `error` with no worker running, starts the
load again and answers the same way. The upload may be any format ffmpeg decodes - mp3, m4a, wav, flac,
ogg - up to one hour. The language is "as spoken" for automatic detection or one of the 40 languages with ASR
support in the model card; the model receives it in the prompt, because its request has no language parameter.

`GET /models` lists the S2 Pro and Nemotron caches under `HF_HOME` with their folder, size and whether the model
is loaded. `DELETE /models/{name}` unloads the model when it is loaded and removes its cache, so the next use
downloads the weights again.

`GET /` serves the page in `service/static`. The page sets the Hugging Face token with `POST /settings/hf-token`;
the token lives in this process's memory for the session and reaches both weight downloads, S2 Pro and Nemotron. The page also uploads
reference recordings as new voices into the writable `VOICES_DIR`, which starts as a copy of `SEED_VOICES_DIR`.
"""
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
from base64 import b64decode, b64encode
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import asr
import engine_nemotron
import models
import soundfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from engine import Engine, EngineError, voice_names
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Response,
    Security,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from registry import UnknownEngineError, available_engines, get_engine
from starlette.background import BackgroundTask

from audio_out import write_render

STATIC_DIR = Path(__file__).resolve().parent / "static"
VOICES_DIR = Path(os.environ.get("VOICES_DIR", Path(__file__).resolve().parent / "voices"))
SEED_VOICES_DIR = Path(os.environ["SEED_VOICES_DIR"]) if os.environ.get("SEED_VOICES_DIR") else None
DEFAULT_ENGINE = os.environ.get("ENGINE", "s2pro")
MAX_TEXT_CHARS = int(os.environ.get("MAX_TEXT_CHARS", "3000"))
IDLE_UNLOAD_SECONDS = float(os.environ.get("IDLE_UNLOAD_SECONDS", "3600"))
WATCH_SECONDS = 5.0
MAX_TRANSCRIPT_CHARS = 1000
MAX_CONTEXT_CHARS = 500
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
UPLOAD_MIN_SECONDS, UPLOAD_MAX_SECONDS = 3.0, 30.0
VOICE_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,39}")
SESSION_SECONDS = 12 * 3600
TOKENS_FILE = (Path(os.environ["TOKENS_FILE"]) if os.environ.get("TOKENS_FILE")
               else Path(VOICES_DIR).parent / "tokens.json")
TOKEN_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,39}")
TOKEN_PREFIX = "vtts_"

password: bytes = b""
sessions: dict[str, float] = {}
tokens: list[dict] = []
token_salt: bytes | None = None
token_lock = threading.Lock()

hf_token = os.environ.get("HF_TOKEN") or None


def _hf_token() -> str | None:
    """The Hugging Face token set through the page, read when an engine loads so a new token is used."""
    return hf_token


def load_password() -> bytes:
    """The password from `S2PRO_PASSWORD_FILE`'s first line, else `S2PRO_PASSWORD`.

    Only the file's trailing CR of the first line is removed; every other character is kept.

    Returns:
        The password as bytes.

    Raises:
        RuntimeError: when neither variable is set or the value is empty.
    """
    source = os.environ.get("S2PRO_PASSWORD_FILE")
    if source:
        found = Path(source).read_bytes().split(b"\n", 1)[0].removesuffix(b"\r")
    else:
        found = os.environ.get("S2PRO_PASSWORD", "").encode()
    if not found:
        raise RuntimeError("no password: set S2PRO_PASSWORD_FILE or S2PRO_PASSWORD")
    return found


def _scrypt(value: bytes, salt: bytes) -> bytes:
    """The scrypt hash of `value` with a 16-byte `salt`: n=2**14, r=8, p=1, 32 bytes out."""
    return hashlib.scrypt(value, salt=salt, n=2**14, r=8, p=1, dklen=32)


def load_tokens() -> None:
    """Read the encrypted token store with the configured password; a missing file means no tokens.

    Raises:
        RuntimeError: when the file does not decrypt with the configured password or is not a store.
    """
    global tokens, token_salt
    tokens, token_salt = [], None
    if not TOKENS_FILE.is_file():
        return
    try:
        store = json.loads(TOKENS_FILE.read_text())
        token_salt = b64decode(store["salt"])
        nonce = b64decode(store["nonce"])
        plaintext = AESGCM(_scrypt(password, token_salt)).decrypt(nonce, b64decode(store["ciphertext"]), None)
        tokens = json.loads(plaintext)["tokens"]
    except Exception as error:
        # Any unreadable or undecryptable store stops the service instead of silently losing the tokens
        raise RuntimeError(
            f"the token store cannot be decrypted with the configured password; "
            f"restore it or remove {TOKENS_FILE}") from error


def save_tokens() -> None:
    """Write the store with a fresh nonce, replacing the file atomically; the caller holds `token_lock`."""
    global token_salt
    if token_salt is None:
        token_salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    plaintext = json.dumps({"tokens": tokens}).encode()
    ciphertext = AESGCM(_scrypt(password, token_salt)).encrypt(nonce, plaintext, None)
    store = {"version": 1, "salt": b64encode(token_salt).decode(),
             "nonce": b64encode(nonce).decode(), "ciphertext": b64encode(ciphertext).decode()}
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=TOKENS_FILE.parent, prefix=".tokens-")
    try:
        with os.fdopen(handle, "w") as file:
            json.dump(store, file)
        os.replace(temporary, TOKENS_FILE)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _session_valid(sid: str | None) -> bool:
    """Whether `sid` names a live session; an expired entry is dropped."""
    if not sid:
        return False
    expiry = sessions.get(sid)
    if expiry is None or expiry <= time.monotonic():
        sessions.pop(sid, None)
        return False
    return True


def _bearer_record(authorization: str | None) -> dict | None:
    """The token record an `Authorization: Bearer` header names, or None when absent or unknown."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[len("Bearer "):].strip()
    prefix = token.removeprefix(TOKEN_PREFIX)[:8]
    for record in tokens:
        if hmac.compare_digest(record["prefix"].encode(), prefix.encode()):
            candidate = _scrypt(token.encode(), b64decode(record["salt"]))
            if hmac.compare_digest(candidate, b64decode(record["hash"])):
                return record
    return None


bearer_scheme = HTTPBearer(auto_error=False, description="API token from Settings; send it as Authorization: Bearer vtts_...")
session_scheme = APIKeyCookie(name="sid", auto_error=False, description="Session cookie set by POST /login")


def require_session(sid: str | None = Security(session_scheme)) -> None:
    """Dependency for a session-only endpoint.

    Raises:
        HTTPException: 401 without a live session cookie.
    """
    if not _session_valid(sid):
        raise HTTPException(401, "log in first")


def require_auth(credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
                 sid: str | None = Cookie(default=None)) -> None:
    """Dependency for an endpoint open to the session cookie or a Bearer token.

    Raises:
        HTTPException: 401 without either.
    """
    authorization = f"Bearer {credentials.credentials}" if credentials else None
    if not _session_valid(sid) and _bearer_record(authorization) is None:
        raise HTTPException(401, "log in first or send a Bearer token")


ENGINES = available_engines(VOICES_DIR, _hf_token)
lock = threading.Lock()
upload_lock = threading.Lock()
loaded_engine: str | None = None
state = "loading"
load_error: str | None = None
last_request = time.monotonic()
busy = False

transcriber = engine_nemotron.NemotronTranscriber(_hf_token)
asr_lock = threading.Lock()
asr_state = "down"
asr_error: str | None = None


def seed_voices() -> None:
    """Copy the bundled voices into the writable folder, overwriting bundled files and leaving uploads."""
    if SEED_VOICES_DIR is None or not SEED_VOICES_DIR.is_dir():
        return
    if SEED_VOICES_DIR.resolve() == Path(VOICES_DIR).resolve():
        return
    shutil.copytree(SEED_VOICES_DIR, VOICES_DIR, dirs_exist_ok=True)


def uploaded_voices() -> list[str]:
    """The voices in `VOICES_DIR` that the seed did not provide."""
    if SEED_VOICES_DIR is None:
        return voice_names(VOICES_DIR)
    return [name for name in voice_names(VOICES_DIR)
            if not (SEED_VOICES_DIR / f"{name}.wav").is_file()]


def is_bundled(name: str) -> bool:
    """Whether the voice came with the image, so it cannot be deleted or replaced."""
    return SEED_VOICES_DIR is not None and (SEED_VOICES_DIR / f"{name}.wav").is_file()


class SpeakRequest(BaseModel):
    """Body of POST /speak; `engine` defaults to the service's ENGINE."""

    text: str
    voice: str = "grimaldus"
    engine: str | None = None


class TokenRequest(BaseModel):
    """Body of POST /settings/hf-token; an empty token clears the stored one."""

    token: str


class LoginRequest(BaseModel):
    """Body of POST /login."""

    password: str


class NewTokenRequest(BaseModel):
    """Body of POST /tokens."""

    name: str


def _report_state(phase: str) -> None:
    """Record a load phase an engine reports; `/health` reads it."""
    global state
    state = phase


def _switch_to(engine: Engine) -> None:
    """Make `engine` the resident one, unloading the previous engine; the caller holds `lock`."""
    global loaded_engine, state, load_error, last_request
    if loaded_engine == engine.name:
        return
    start = time.time()
    if loaded_engine is not None:
        ENGINES[loaded_engine].unload()
        loaded_engine = None
    state, load_error = "loading", None
    try:
        engine.load(_report_state)
    except Exception as error:
        state, load_error = "error", f"the {engine.name} engine failed to load: {error}"
        raise
    loaded_engine = engine.name
    state = "ready"
    # The countdown starts when the model is ready: a cold start downloads for minutes before the load ends
    last_request = time.monotonic()
    print(f"engine {engine.name} loaded in {time.time() - start:.0f} s", flush=True)


def _load_default(engine: Engine) -> None:
    """Load the default engine outside the request path, so `/health` answers during the load."""
    with lock:
        try:
            _switch_to(engine)
        except Exception as error:  # recorded in state and load_error; the next request retries the load
            print(f"the default engine failed to load: {error}", flush=True)


def _asr_phase() -> str:
    """The state a transcriber load reports: `downloading` without the Nemotron cache, `loading` with it."""
    return "loading" if models.cache_dir("nemotron").is_dir() else "downloading"


def _start_transcriber_load() -> str:
    """Start the transcriber's load in a background thread, with the state set before the thread runs.

    A `/transcribe` request during the load sees `downloading` or `loading` and answers 503, so no request
    waits for the download and none starts a second load.

    Returns:
        The state the load reports, `downloading` or `loading`; the started thread replaces it.
    """
    global asr_state, asr_error
    phase = _asr_phase()
    asr_state, asr_error = phase, None
    threading.Thread(target=_load_transcriber, daemon=True).start()
    return phase


def _load_transcriber() -> None:
    """Load the transcription model under `asr_lock`, so one load serves every request.

    The state becomes `ready` when the model is loaded and `error` with the reason when the load failed.
    """
    global asr_state, asr_error
    with asr_lock:
        if transcriber.is_loaded():
            asr_state = "ready"
            return
        try:
            transcriber.load()
        except Exception as error:  # recorded in asr_state and asr_error; the next request retries the load
            asr_state, asr_error = "error", str(error)
            print(f"the transcription model failed to load: {error}", flush=True)
            return
        asr_state = "ready"


def _unload_when_idle() -> None:
    """Watcher thread: free the resident engine after IDLE_UNLOAD_SECONDS idle; never during a synthesis."""
    global loaded_engine
    while True:
        time.sleep(WATCH_SECONDS)
        if loaded_engine is None or time.monotonic() - last_request < IDLE_UNLOAD_SECONDS:
            continue
        if not lock.acquire(blocking=False):  # a synthesis or a load holds it
            continue
        try:
            if loaded_engine is None or time.monotonic() - last_request < IDLE_UNLOAD_SECONDS:
                continue
            name = loaded_engine
            ENGINES[name].unload()
            loaded_engine = None
            print(f"engine {name} unloaded after idle time", flush=True)
        finally:
            lock.release()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Read the password and the token store, then start the engine load, the transcription load and the idle
    watcher.

    A missing password, a token store the password cannot decrypt, or a bad ENGINE stops the service here.
    """
    global password
    password = load_password()
    load_tokens()
    seed_voices()
    default = get_engine(ENGINES, DEFAULT_ENGINE)
    threading.Thread(target=_load_default, args=(default,), daemon=True).start()
    if transcriber.available():
        _start_transcriber_load()
    threading.Thread(target=_unload_when_idle, daemon=True).start()
    yield


app = FastAPI(title="Voice TTS", lifespan=lifespan)


@app.post("/login")
def login(request: LoginRequest, response: Response) -> dict:
    """Open a session when the password matches; a wrong or empty password is 401."""
    if not request.password or not hmac.compare_digest(request.password.encode(), password):
        raise HTTPException(401, "wrong password")
    sid = secrets.token_urlsafe(32)
    sessions[sid] = time.monotonic() + SESSION_SECONDS
    response.set_cookie("sid", sid, max_age=SESSION_SECONDS, httponly=True, samesite="strict", path="/")
    return {"authenticated": True}


@app.post("/logout")
def logout(response: Response, _: None = Depends(require_session),
           sid: str | None = Cookie(default=None)) -> dict:
    """End the session and clear its cookie."""
    sessions.pop(sid, None)
    response.delete_cookie("sid", path="/")
    return {"authenticated": False}


@app.get("/session")
def session_state(sid: str | None = Cookie(default=None)) -> dict:
    """Whether the request carries a live session cookie; public."""
    return {"authenticated": _session_valid(sid)}


@app.get("/tokens")
def list_tokens(_: None = Depends(require_session)) -> dict:
    """The tokens' names, prefixes and creation times; never a token or a hash."""
    return {"tokens": [{"name": record["name"], "prefix": record["prefix"],
                        "created": record["created"]} for record in tokens]}


@app.post("/tokens", status_code=201)
def add_token(request: NewTokenRequest, _: None = Depends(require_session)) -> dict:
    """Create a named API token and return its plaintext, which is shown only here.

    Raises:
        HTTPException: 422 for a bad name, 409 when the name is already in use.
    """
    if not TOKEN_NAME.fullmatch(request.name):
        raise HTTPException(422, "the token name must match ^[a-z0-9][a-z0-9_-]{0,39}$")
    with token_lock:
        if any(record["name"] == request.name for record in tokens):
            raise HTTPException(409, f"a token named {request.name!r} already exists")
        token = TOKEN_PREFIX + secrets.token_urlsafe(32)
        salt = secrets.token_bytes(16)
        record = {"name": request.name, "prefix": token.removeprefix(TOKEN_PREFIX)[:8],
                  "salt": b64encode(salt).decode(),
                  "hash": b64encode(_scrypt(token.encode(), salt)).decode(),
                  "created": datetime.now(UTC).isoformat(timespec="seconds")}
        tokens.append(record)
        save_tokens()
    return {"name": record["name"], "token": token, "prefix": record["prefix"],
            "created": record["created"]}


@app.delete("/tokens/{name}")
def delete_token(name: str, _: None = Depends(require_session)) -> dict:
    """Revoke a token by name.

    Raises:
        HTTPException: 404 for an unknown name.
    """
    with token_lock:
        for index, record in enumerate(tokens):
            if record["name"] == name:
                del tokens[index]
                save_tokens()
                return {"deleted": name}
    raise HTTPException(404, f"unknown token {name!r}")


@app.get("/")
def index() -> FileResponse:
    """The web page."""
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/settings")
def settings(_: None = Depends(require_session)) -> dict:
    """The page's settings: whether a token is set, the default engine and the text limit; never the token."""
    return {"hf_token_set": hf_token is not None, "default_engine": DEFAULT_ENGINE,
            "max_text_chars": MAX_TEXT_CHARS}


@app.post("/settings/hf-token")
def set_hf_token(request: TokenRequest, _: None = Depends(require_session)) -> dict:
    """Set the Hugging Face token for this process's session; an empty token clears it. Never returns it."""
    global hf_token
    hf_token = request.token.strip() or None
    return {"hf_token_set": hf_token is not None}


@app.get("/models")
def list_models(_: None = Depends(require_session)) -> dict:
    """The model caches the service knows, each with its folder, size and whether the model is loaded."""
    loaded = {"s2pro": loaded_engine == "s2pro", "nemotron": transcriber.is_loaded()}
    return {"models": [models.describe(name, loaded[name]) for name in models.MODELS]}


@app.delete("/models/{name}")
def delete_model(name: str, _: None = Depends(require_session)) -> dict:
    """Delete a model's cache; a loaded model is unloaded first, so the next use downloads the weights again.

    Raises:
        HTTPException: 404 for a name the service does not know, 500 when the unload fails or the cache
        cannot be removed.
    """
    global loaded_engine, asr_state, asr_error
    if name not in models.MODELS:
        raise HTTPException(404, f"unknown model {name!r}; the models are {list(models.MODELS)}")
    if name == "s2pro":
        with lock:
            if loaded_engine == "s2pro":
                try:
                    ENGINES["s2pro"].unload()
                except Exception as error:
                    raise HTTPException(500, f"the s2pro engine could not be unloaded: {error}") from error
                loaded_engine = None
    else:
        with asr_lock:
            if transcriber.is_loaded():
                try:
                    transcriber.unload()
                except Exception as error:
                    raise HTTPException(500, f"the nemotron transcriber could not be unloaded: {error}") from error
                asr_state, asr_error = "down", None
    try:
        freed = models.delete(name)
    except OSError as error:
        raise HTTPException(500, str(error)) from error
    return {"deleted": name, "freed_bytes": freed}


@app.get("/health")
def health() -> dict:
    """Always 200: the engine's load state and error, the seconds to its idle unload, and the transcriber's."""
    left = max(0.0, IDLE_UNLOAD_SECONDS - (time.monotonic() - last_request))
    return {"status": "ok", "loaded": loaded_engine is not None, "state": state, "error": load_error,
            "engine": loaded_engine, "busy": busy,
            "seconds_until_unload": round(left) if loaded_engine is not None else None,
            "asr": {"available": transcriber.available(), "loaded": transcriber.is_loaded(),
                    "state": asr_state, "error": asr_error}}


@app.get("/voices")
def voices(_: None = Depends(require_auth)) -> dict:
    """Each installed engine and the voices it can speak, and the uploaded voices."""
    return {"voices": {name: engine.voices() for name, engine in ENGINES.items()},
            "uploaded": uploaded_voices()}


@app.post("/voices", status_code=201)
def add_voice(name: str = Form(...), text: str = Form(...), file: UploadFile = File(...),
              _: None = Depends(require_auth)) -> dict:
    """Clone a voice from a reference WAV and its transcript.

    Raises:
        HTTPException: 422 for a bad name, transcript, audio or duration; 409 when the name already exists;
        413 when the file is over `MAX_UPLOAD_BYTES`.
    """
    if not VOICE_NAME.fullmatch(name):
        raise HTTPException(422, "the voice name must match ^[a-z0-9][a-z0-9_-]{0,39}$")
    transcript = text.strip()
    if not 1 <= len(transcript) <= MAX_TRANSCRIPT_CHARS:
        raise HTTPException(422, f"the transcript has {len(transcript)} characters; "
                                 f"it must be 1 to {MAX_TRANSCRIPT_CHARS}")
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"the reference is over {MAX_UPLOAD_BYTES} bytes")
    try:
        audio, rate = soundfile.read(io.BytesIO(data), dtype="float32", always_2d=True)
    except Exception as error:
        raise HTTPException(422, f"the reference is not a readable audio file: {error}") from error
    seconds = len(audio) / rate
    if not UPLOAD_MIN_SECONDS <= seconds <= UPLOAD_MAX_SECONDS:
        raise HTTPException(422, f"the reference is {seconds:.1f} s; "
                                 f"it must be {UPLOAD_MIN_SECONDS:.0f} to {UPLOAD_MAX_SECONDS:.0f} s")
    wav_path = Path(VOICES_DIR) / f"{name}.wav"
    txt_path = Path(VOICES_DIR) / f"{name}.txt"
    with upload_lock:
        if is_bundled(name) or (wav_path.exists() and txt_path.exists()):
            raise HTTPException(409, f"the voice {name!r} already exists; delete it before uploading it again")
        try:
            txt_path.write_text(transcript)
            soundfile.write(wav_path, audio.mean(axis=1), rate, subtype="PCM_16")
        except Exception as error:
            wav_path.unlink(missing_ok=True)
            txt_path.unlink(missing_ok=True)
            raise HTTPException(422, f"the voice could not be written: {error}") from error
    return {"name": name}


@app.delete("/voices/{name}")
def delete_voice(name: str, _: None = Depends(require_auth)) -> dict:
    """Delete an uploaded voice.

    Raises:
        HTTPException: 404 for an unknown name, 409 for a bundled voice.
    """
    if is_bundled(name):
        raise HTTPException(409, f"the voice {name!r} came with the image and cannot be deleted")
    if name not in voice_names(VOICES_DIR):
        raise HTTPException(404, f"unknown voice {name!r}")
    with upload_lock:
        (Path(VOICES_DIR) / f"{name}.wav").unlink(missing_ok=True)
        (Path(VOICES_DIR) / f"{name}.txt").unlink(missing_ok=True)
    return {"deleted": name}


@app.post("/speak")
def speak(request: SpeakRequest, _: None = Depends(require_auth)) -> FileResponse:
    """Speak the text with the named engine and voice and return the MP3 (`audio/mpeg`).

    Raises:
        HTTPException: 404 for an unknown engine or voice, 422 for empty or too long text, 500 when the
        engine cannot load or speak.
    """
    global loaded_engine, last_request, busy
    text = request.text.strip()
    if not text:
        raise HTTPException(422, "text is empty")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(422, f"text has {len(text)} characters; the limit is {MAX_TEXT_CHARS}")
    try:
        engine = get_engine(ENGINES, request.engine or DEFAULT_ENGINE)
    except UnknownEngineError as error:
        raise HTTPException(404, str(error)) from error
    if request.voice not in engine.voices():
        raise HTTPException(404, f"unknown voice {request.voice!r} for engine {engine.name}; "
                                 f"available: {engine.voices()}")
    with lock:
        busy = True
        try:
            _switch_to(engine)
            audio, rate = engine.speak(text, request.voice)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except Exception as error:
            # A failed synthesis may leave the engine unusable: free it, so the next request loads a fresh one
            loaded_engine = None
            engine.unload()
            if isinstance(error, EngineError):
                raise HTTPException(500, str(error)) from error
            raise
        finally:
            busy = False
            last_request = time.monotonic()
    folder = tempfile.mkdtemp()
    mp3 = write_render(Path(folder) / "speech.mp3", audio, rate)
    return FileResponse(mp3, media_type="audio/mpeg", filename="speech.mp3",
                        background=BackgroundTask(lambda: (mp3.unlink(), Path(folder).rmdir())))


@app.post("/transcribe")
def transcribe(file: UploadFile = File(...), language: str = Form(asr.AUTO_LANGUAGE),
               wording: str = Form("readable"), context: str = Form(""),
               _: None = Depends(require_auth)) -> dict:
    """Transcribe an uploaded recording with Nemotron 3.5 Transcribe and return its text.

    The model loads in the background at start, so the first recording does not wait for its 67.5 GB
    download: a request during the download or the load answers 503 with `Retry-After`. A request that
    finds the state `down`, or `error` with no worker running, starts the load in the background and answers the same way.

    Args:
        file: the recording; any format ffmpeg decodes, such as mp3, m4a, wav, flac or ogg.
        language: "as spoken" for automatic detection, or one of the 40 languages with ASR support.
        wording: "readable" omits fillers and accidental repetitions; "verbatim" keeps them.
        context: names and terms the recording uses, at most `MAX_CONTEXT_CHARS` characters.

    Returns:
        `{"text", "language", "wording"}`.

    Raises:
        HTTPException: 413 for an upload over `asr.MAX_UPLOAD_BYTES`, 422 for a recording, language,
        wording or context the model cannot take, 503 when the transcription environment is missing or
        the model is downloading or loading, and 500 when the model cannot load or transcribe.
    """
    global asr_state, asr_error
    data = file.file.read(asr.MAX_UPLOAD_BYTES + 1)
    if len(data) > asr.MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"the recording is over {asr.MAX_UPLOAD_BYTES} bytes")
    try:
        samples, _ = asr.decode_audio(data)
        prompt = asr.build_prompt(language, wording, context)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if len(context) > MAX_CONTEXT_CHARS:
        raise HTTPException(422, f"the context has {len(context)} characters; "
                                 f"the limit is {MAX_CONTEXT_CHARS}")
    if not transcriber.available():
        raise HTTPException(503, f"the transcription environment is missing: "
                                 f"{transcriber.python_path()}")
    phase = asr_state
    if phase == "down" or (phase == "error" and not transcriber.is_loaded()):
        phase = _start_transcriber_load()
    if phase in ("downloading", "loading"):
        raise HTTPException(503, f"the transcription model is {phase}",
                            headers={"Retry-After": "30"})
    with asr_lock:
        try:
            if not transcriber.is_loaded():
                asr_state, asr_error = "loading", None
                transcriber.load()
            asr_state, asr_error = "ready", None
            texts = [transcriber.transcribe_window(samples[start:end], prompt)
                     for start, end in asr.window_bounds(samples)]
        except EngineError as error:
            asr_state, asr_error = "error", str(error)
            raise HTTPException(500, str(error)) from error
    return {"text": " ".join(texts), "language": language, "wording": wording}
