# Voice TTS service

An HTTP API over a registry of text-to-speech engines; S2 Pro is the engine in the image, and it speaks in the winning grimaldus voice by default. The method, the measures and the S2 Pro non-commercial licence are in `../references/fish-audio-s2-pro.md`.

The service is `leftenant-voice-tts-service` and the image is `leftenant-voice-tts`, tagged `latest` in `service/compose.yml`; the model is only the implementation. The page and the API need a password, and the API token store is encrypted with it.

## API

| Request | Body | Result |
|---|---|---|
| `GET /` | - | the web page, `text/html` |
| `POST /login` | `{"password": "..."}` | 200 sets the `sid` cookie; 401 for a wrong or empty password |
| `POST /logout` | - | `{"authenticated": false}`; ends the session and clears the cookie |
| `GET /session` | - | `{"authenticated": bool}` |
| `GET /tokens` | - | `{"tokens": [{"name", "prefix", "created"}]}`; never a token or a hash |
| `POST /tokens` | `{"name": "..."}` | 201 `{"name", "token", "prefix", "created"}`; the token is shown only here |
| `DELETE /tokens/{name}` | - | `{"deleted": name}`; 404 unknown |
| `POST /speak` | `{"text": "...", "voice": "grimaldus", "engine": "s2pro"}` | the MP3, `audio/mpeg` |
| `GET /health` | - | `{"status", "loaded", "state", "error", "engine", "busy", "seconds_until_unload"}`, always 200 |
| `GET /voices` | - | `{"voices": {"s2pro": ["grimaldus"], "auk-flash": ["grimaldus"]}, "uploaded": [...]}` |
| `GET /settings` | - | `{"hf_token_set", "default_engine", "max_text_chars"}`; never the token |
| `POST /settings/hf-token` | `{"token": "..."}` | `{"hf_token_set"}`; an empty token clears it |
| `POST /voices` | multipart: `name`, `text`, `file` | 201 `{"name"}`; the new voice is usable at once |
| `DELETE /voices/{name}` | - | `{"deleted": name}`; 404 unknown, 409 bundled |

- The `engine` field is optional; without it the request uses `ENGINE` from the environment (default `s2pro`)
- 404: an unknown engine, and the body lists the installed ones; or an unknown voice, and the body lists that engine's voices
- 422: empty text, text over `MAX_TEXT_CHARS`, or a missing `text` field
- `uploaded` in `GET /voices` lists the voices that did not come with the image, when `SEED_VOICES_DIR` is set; with no seed every voice is listed
- One synthesis runs at a time; a second request waits for the first
- One engine is resident at a time: a request for another engine unloads the resident one first, because S2 Pro (about 19 GiB) and AuK-Flash (about 18 GiB) do not fit one 24 GB card together
- `state` is the load phase: `downloading` while the weights are fetched from Hugging Face, `loading` while the model is built, `ready` when the last load succeeded, and `error` when it failed, with the message in `error`
- `loaded` says whether the model is in GPU memory right now: after the idle unload it is `false` while `state` stays `ready`, because the next request reloads from the local cache
- A request that finds the last load failed retries it; a failed load answers 500 with the message instead of waiting

## Authentication

The service starts only with a password. Without one it exits at start with `no password: set S2PRO_PASSWORD_FILE or S2PRO_PASSWORD`, and the container healthcheck stays red.

- `S2PRO_PASSWORD_FILE` names a file and its first line is the password: the trailing CR of a CRLF is removed and nothing else is stripped
- `S2PRO_PASSWORD` is the password when no file is named
- The password lives in this process's memory only; it is never written to a log, a response or a file
- Under compose the password is a secret: the compose secret reads `/home/lab/.cache/voice-tts/password.txt` on the Docker host, because the daemon cannot see the lab project folder; the file is mounted at `/run/secrets/s2pro_password` and `S2PRO_PASSWORD_FILE` points at it. The file is seeded on the Docker host through a one-shot container, so it stays out of Git, `compose.yml` and every image layer
- `POST /login` opens a session with cookie `sid`: `HttpOnly`, `SameSite=Strict`, `Path=/`, 12 hours. Sessions are held in memory and end with a restart
- `POST /logout` ends the session and clears the cookie; `GET /session` reports whether the request carries one
- API tokens are created, listed and revoked in Settings. A token starts `vtts_` and is shown once, at creation; the store keeps only its prefix, creation date and a salted scrypt hash
- The token store is `/data/tokens.json` on the data volume (`TOKENS_FILE`). It is one AES-GCM ciphertext whose key is `scrypt(password, salt, n=2**14, r=8, p=1, dklen=32)`; every save uses a fresh nonce and replaces the file atomically
- A store that does not decrypt with the configured password stops the service with `the token store cannot be decrypted with the configured password; restore it or remove <path>`. Removing it starts an empty store, so changing the password means removing it first
- API clients send `Authorization: Bearer <token>` on `/speak` and `/voices`
- `/docs` is the Swagger UI, `/redoc` the ReDoc view and `/openapi.json` the schema; all three are public; the API token can be entered under Authorize for `/speak` and `/voices`

### Access

| Access | Endpoints |
|---|---|
| public | `GET /`, `GET /health`, `POST /login`, `GET /session` |
| session only | `GET /settings`, `POST /settings/hf-token`, `GET/POST /tokens`, `DELETE /tokens/{name}`, `POST /logout` |
| session or Bearer | `POST /speak`, `GET /voices`, `POST /voices`, `DELETE /voices/{name}` |

`GET /health` stays public for the Docker healthcheck. Every other refusal is 401 with a message.

## Web page

`http://127.0.0.1:8000/` serves one self-contained page that opens on a password form; after login it shows four sections:

- Status: polls `GET /health` every 2 s and shows the load state, the resident engine, whether a synthesis is busy, the seconds to the idle unload and the error text; a progress bar without a percentage while the model downloads or loads. It reports only and never starts a load, a download or a wipe
- Settings: sets or clears the Hugging Face token, and lists the API tokens with their name, prefix and creation date beside a Revoke button and a create form. A new token is displayed once in a `<code>` block and not again. The Hugging Face token is held in the service process's memory for the container session, is never written to disk and is never returned by any endpoint; a restart forgets it
- Voice: engine and voice selection, a reference upload that clones a voice on the spot, and the uploaded voices with a Delete button
- Generate: speaks the text, plays the MP3 in the page and offers it as `speech.mp3`

The page keeps neither the password nor a token in browser storage. A wrong password shows the service's message and no section; logout returns to the form.

### Upload limits

- name: `^[a-z0-9][a-z0-9_-]{0,39}$`
- transcript: 1 to 1000 characters
- reference WAV: 25 MB at most, 3 to 30 s, any channel count averaged to mono, stored as PCM_16 at its source rate
- a bundled name is 409 and cannot be deleted or replaced; a name with a complete `.wav` + `.txt` pair already in the voices folder is 409 - delete an uploaded voice before reusing its name; a lone leftover `.wav` or `.txt` is overwritten by the retry

## Engines

An engine is a model that implements the five calls in `service/engine.py`: `load()`, `unload()`, `speak(text, voice) -> (float32 samples, rate)`, `voices()` and a `name`. `service/registry.py` lists the engines installed on the machine; the API layer does not change when one is added.

| Engine | Model | Runs | Notes |
|---|---|---|---|
| `s2pro` | Fish Audio S2 Pro, revision `1de9996` | in the service's interpreter (`.venv-fish`) | the default; non-commercial licence |
| `auk-flash` | Tencent AuK-Flash, revision `575b92f` | child process in `.venv-auk` (Python 3.10) over `wip/tts-trial/auk/speak_auk.py` | `make -f auk.mk install`; not in the Docker image |

- AuK-Flash licence: the AuK weights are MIT; its text encoder, Qwen2.5-Omni-3B, is non-commercial
- The `auk-flash` engine appears only where `.venv-auk/bin/python` exists; its environment and weights live on the host, and in the Docker image neither is present, so that name is unknown there and the 404 lists the installed engines
- A third model needs `service/engine_<name>.py` (the engine class), one line in `service/registry.py`, and, if it runs in another Python environment, its own worker script; `service/app.py` needs no change
- The S2 Pro engine reads the page's token when it loads and passes it to both Hugging Face calls, so a token set in the page serves the next load without a restart
- The S2 Pro engine encodes a voice once and keys that cache on the WAV's modification time: a voice deleted and uploaded again under the same name is re-encoded on its next use

## Run natively

```bash
make -f s2pro.mk install-service   # once: FastAPI, uvicorn and cryptography in .venv-fish
S2PRO_PASSWORD=... make -f s2pro.mk serve   # GPU=0, PORT=8000, ENGINE=s2pro, IDLE_UNLOAD_SECONDS=3600
```

`serve` needs the fish-speech checkout and `.venv-fish` (`make -f fish.mk install`) and `ffmpeg` on PATH: `src/audio_out.py` encodes every MP3 with it, and `serve` stops at start with a message when it is missing. It also needs `S2PRO_PASSWORD` or `S2PRO_PASSWORD_FILE` in its environment; without one it stops with `no password: set S2PRO_PASSWORD_FILE or S2PRO_PASSWORD`. The Docker image carries ffmpeg. The weights download from Hugging Face into the local cache on the first start unless `make -f s2pro.mk install` already fetched them.

The bundled voices seed from `service/voices` into the writable `wip/s2pro-voices`, where uploads land, so the page cannot delete or replace the bundled voice.

```bash
curl -s -X POST http://127.0.0.1:8000/login -H 'Content-Type: application/json' \
  -d '{"password": "..."}' -c cookies.txt
curl -s -b cookies.txt -X POST http://127.0.0.1:8000/speak -H 'Content-Type: application/json' \
  -d '{"text": "Brothers, we stand upon the wall and we do not yield.", "voice": "grimaldus"}' -o speech.mp3
```

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `S2PRO_PASSWORD_FILE` | unset | file whose first line is the service password; wins over `S2PRO_PASSWORD` |
| `S2PRO_PASSWORD` | unset | the service password when no file is named; with neither the service does not start |
| `TOKENS_FILE` | `Path(VOICES_DIR).parent / "tokens.json"` | the encrypted API token store; `/data/tokens.json` in the image |
| `VOICES_DIR` | `/data/voices` | the writable folder of `<voice>.wav` + `<voice>.txt` pairs, shared by the engines and written by the page's upload |
| `SEED_VOICES_DIR` | unset | read-only folder of bundled voices copied into `VOICES_DIR` at start; a voice that is not there is an upload |
| `ENGINE` | `s2pro` | engine that serves a request without an `"engine"` field |
| `MAX_TEXT_CHARS` | `3000` | longest text accepted; a longer text is 422 |
| `IDLE_UNLOAD_SECONDS` | `3600` | idle time before the model leaves GPU memory; the next request loads it again |
| `HF_TOKEN` | unset | Hugging Face token for the weight download; the public `fishaudio/s2-pro` needs none; the page can set it for the session instead |
| `HF_HOME` | `/data/huggingface` | the Hugging Face cache root; the weights land in its `hub` subfolder, and the image's data volume holds it across restarts |
| `GPU` | `0` | GPU index of `serve` and `docker-run` |
| `PORT` | `8000` | host port of `serve` and `docker-run` |

## Tests

```bash
make -f s2pro.mk install-test   # once: pytest and httpx in .venv-fish
make test                       # unit suite: engine selection, stubs only; no GPU, no model
make test-functional            # real service on the GPU queue, then the image; downloads on a fresh volume
```

## GPU memory and speed

- About 19 GiB while loaded: fits the RTX PRO 4000 24 GB (GPU 0), not a 16 GB card
- About 0.5 GiB after the idle unload, the CUDA context alone; measured 474 MiB natively and 380 MiB in the container
- The default engine loads in the background at start, so `/health` answers while the model loads
- Native: load 52 s at start; after an unload the next request takes 56 s, the model load and its speech together
- In the container the first start downloaded 11.0 GB from Hugging Face in 169 s and was ready 473 s after start; a start on the warm volume was ready in 282 s with no download. The record is `tmp/workflows/hf-pull/hf-pull.json`
- Real-time factor about 2.5 to 3: 95 s of speech takes about 4 minutes

## Docker image

```bash
make -f s2pro.mk docker-build      # about 10 min, 18.7 GB in the image store
S2PRO_PASSWORD=... make -f s2pro.mk docker-run   # GPU 0, port 8000; the data volume holds the weights, the voices and the tokens
```

- Base `nvidia/cuda:12.8.1-runtime-ubuntu24.04`, torch 2.8.0 for cu128 (the Blackwell kernels), fish-speech at commit `0f8a12e8`, ffmpeg
- The image is `leftenant-voice-tts` (the service name is `leftenant-voice-tts-service`); the `s2pro` engine is its implementation
- The weights are not in the image: the first start downloads 11.0 GB from Hugging Face into `/data/huggingface` (the `HF_HOME` default) in 169 s, and `/health` reports `downloading` then `loading` then `ready`
- The named volume `data` holds `/data`, so a later container on the same volume skips the download and loads from it; `docker volume rm data` forces a fresh download
- `HF_TOKEN` is optional: `fishaudio/s2-pro` is public and needs no token, and a gated model or a rate-limited account can set it
- `S2PRO_PASSWORD` or `S2PRO_PASSWORD_FILE` is required at every start; `docker-run` passes whichever the host sets. The password is in no layer and in no image history
- The image carries the bundled voices in `/app/seed-voices` and copies them into the writable `/data/voices` at start; the page uploads new voices and deletes uploaded ones there
- The same `data` volume holds `/data/voices` and the encrypted token store `/data/tokens.json`, so the seed, the uploads and the API tokens survive a container restart; without it they are the container's own and are lost with the container
- The image declares a `HEALTHCHECK` on `GET /health`, which answers before the model is loaded and needs no login; the container is healthy while the background load runs
- The daemon on this workstation refuses `image load`, so `docker-build` uses the classic builder (`DOCKER_BUILDKIT=0`); a daemon that allows buildx loads accepts `docker build --load` instead
- A GPU container needs the NVIDIA container toolkit on the Docker host

## Docker Compose

```bash
cd service
docker compose pull
read -rsp 'Password: ' PW; echo; printf '%s' "$PW" | docker run --rm -i -v /home/lab/.cache/voice-tts:/seed --entrypoint sh registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:latest -c 'mkdir -p /seed && cat > /seed/password.txt && chmod 600 /seed/password.txt'; unset PW
docker compose up -d --remove-orphans
PORT=$(docker compose port leftenant-voice-tts-service 8000 | cut -d: -f2)
curl -s "http://127.0.0.1:$PORT/health"
```

- The compose service and container are `leftenant-voice-tts-service`; the image is `leftenant-voice-tts:latest`, written in `compose.yml`
- The image and its tag, the container port 8000 published on a daemon-assigned host port, GPU index 0, engine `s2pro`, idle unload 3600 s and text limit 3000 characters are written literally in `compose.yml`; edit that file to change one; no `.env` is read and none is needed
- The password never enters `compose.yml`: the top-level `secrets: s2pro_password` reads `/home/lab/.cache/voice-tts/password.txt` on the Docker host, the service mounts it at `/run/secrets/s2pro_password`, and `S2PRO_PASSWORD_FILE` points there. The seeding step writes that host file through a one-shot container, so the password is never in `compose.yml`, an image layer, a command line or a log
- One named volume, `data`, holds three things: the weights in the Hugging Face cache at `/data/huggingface`, the voice folder at `/data/voices`, and the encrypted token store at `/data/tokens.json`; it is declared with an explicit `name:` so `docker run -v data:/data` uses the same one
- The first start downloads about 11 GB into `/data/huggingface` and later starts reuse it; the image seeds its bundled voices into `/data/voices` at start and the page manages uploads there, both kept across restarts
- `docker compose down` keeps the volume; `docker compose down -v` deletes that one volume, so the next start downloads the weights, seeds the voices again and starts an empty token store
- The container port 8000 is published on a host port the daemon assigns at each start; it can change when the container is recreated, and `docker compose port leftenant-voice-tts-service 8000` prints it; the page is `http://127.0.0.1:<port>/`. The lab session cannot reach the daemon's published ports, so from there test with `docker compose exec leftenant-voice-tts-service curl -s http://localhost:8000/health`
- `HF_TOKEN` is not in `compose.yml`: `fishaudio/s2-pro` is public and needs none. A gated model or a rate-limited account sets the token in Settings on the page, where it lasts the container session; a compose deployment that needs it at start adds `HF_TOKEN: <token>` to `environment` in `compose.yml`
- The healthcheck calls `GET /health`, which answers before the model is loaded and needs no login; the container is healthy while the background load runs
- `compose.yml` has no `build:`; compose pulls the image named in `compose.yml` from the registry and never builds. A local build is `make -f s2pro.mk docker-build`

## Registry

```bash
make -f s2pro.mk docker-tag        # $(IMAGE):$(VERSION) and :latest
make -f s2pro.mk docker-push       # token from the vault on stdin, both tags, logout
```

- `docker-push` uses a temporary `DOCKER_CONFIG`, so the token is never written to `~/.docker/config.json`
- `REGISTRY` defaults to `registry.nas.stellars-tech.eu:8443`
- `IMAGE` defaults to `registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts`
- `compose.yml` names its tag directly; the Makefile's `VERSION` comes from `service/VERSION` and the two agree at a release, where the tag written there is `latest`
- The GitLab project `konrad.jelen/leftenant-voice-tts` must exist with the container registry enabled
