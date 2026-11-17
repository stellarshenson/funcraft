# Fish Audio S2 Pro trial. .venv-fish (fish.mk) already runs S2 Pro: the code checkout reads the model type from config.json.
#   make -f fish.mk install    (once, builds .venv-fish)
#   make -f s2pro.mk install   (downloads the gated weights; the token comes from the vault and is never printed)
SMODEL := fishaudio/s2-pro
SREV   := 1de9996b6be38b745688de084d87a5633f714e4e
SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

.PHONY: install
install:
	test -x .venv-fish/bin/hf
	@HF_TOKEN=$$(jupyterlab-passkey vault get huggingface/api) .venv-fish/bin/hf download $(SMODEL) --revision $(SREV)

# Speak a text file in a cloned voice (the winning method, src/fish/speak_s2pro.py), through the GPU queue.
#   make -f s2pro.mk speak VOICE=grimaldus FILE=texts/x.txt OUT=out/x.mp3 FGPU=2
# FGPU 2 waits in tmp/workflows/gpu2-queue.sh (one job at a time); another index runs directly on that card.
VOICE ?= grimaldus
FGPU  ?= 2

.PHONY: speak
speak:
	test -n "$(FILE)" -a -n "$(OUT)"
	mkdir -p logs
	$(if $(filter 2,$(FGPU)),tmp/workflows/gpu2-queue.sh,env CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$(FGPU)) \
	  .venv-fish/bin/python src/fish/speak_s2pro.py $(FILE) $(OUT) --voice $(VOICE) 2>&1 | tee logs/speak-s2pro.log

# Service (service/README.md): an HTTP API over the engine registry. The GPU defaults to 0.
#   make -f s2pro.mk install-service   (adds fastapi, uvicorn, python-multipart and cryptography to .venv-fish)
#   make -f s2pro.mk serve             (native run; PORT, GPU, ENGINE, IDLE_UNLOAD_SECONDS, S2PRO_PASSWORD)
#   make -f s2pro.mk docker-build | docker-run | docker-tag | docker-push | docker-prune
#   make -f s2pro.mk install-test      (adds pytest and httpx to .venv-fish)
#   make -f s2pro.mk test              (unit suite, no GPU and no model)
REGISTRY ?= registry.nas.stellars-tech.eu:8443
IMAGE    ?= $(REGISTRY)/konrad.jelen/leftenant-voice-tts
VERSION  ?= $(shell cat service/VERSION)
GPU      ?= 0
PORT     ?= 8000
ENGINE   ?= s2pro
IDLE_UNLOAD_SECONDS ?= 3600

.PHONY: install-service install-test check-ffmpeg serve test test-functional docker-build docker-run docker-tag docker-push docker-prune
install-service:
	uv pip install --python .venv-fish/bin/python fastapi uvicorn python-multipart cryptography

install-test:
	uv pip install --python .venv-fish/bin/python pytest httpx

test:
	PYTHONPATH=service:src/fish:src .venv-fish/bin/python -m pytest tests/unit -q

# The functional suite: first the page in headless google-chrome against the service with stub engines (no GPU;
# BROWSER_PYTHON needs playwright and pytest, which the system python3 carries), then the real service on the GPU the
# queue gives it, then the image where the daemon allows GPU containers. Takes minutes; stops at the first failure
# and leaves no process or container behind. Needs ffprobe.
BROWSER_PYTHON ?= python3

test-functional:
	$(BROWSER_PYTHON) -m pytest tests/functional/test_browser.py -q -x
	PYTHONPATH=service:src/fish:src tmp/workflows/gpu-queue.sh 20000 .venv-fish/bin/python -m pytest \
	  tests/functional/test_native.py tests/functional/test_webapp.py tests/functional/test_container.py \
	  tests/functional/test_leftover.py -q -x

# The service always answers with an MP3, and src/audio_out.py encodes it with ffmpeg (the image carries it).
check-ffmpeg:
	@command -v ffmpeg >/dev/null || { echo "serve needs ffmpeg on PATH: src/audio_out.py encodes the MP3 with it" >&2; exit 1; }

serve: check-ffmpeg
	CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$(GPU) ENGINE=$(ENGINE) IDLE_UNLOAD_SECONDS=$(IDLE_UNLOAD_SECONDS) \
	  VOICES_DIR=wip/s2pro-voices SEED_VOICES_DIR=service/voices \
	  PYTHONPATH=src/fish:src .venv-fish/bin/python -m uvicorn app:app --app-dir service --host 127.0.0.1 --port $(PORT)

# The daemon here refuses `image load` (the buildx container driver's export), so the classic builder
# writes the tag straight into the image store. DOCKER_BUILDKIT=1 would use the container driver again.
docker-build:
	DOCKER_BUILDKIT=0 docker build -f service/Dockerfile -t $(IMAGE):$(VERSION) .

# One data volume holds both folders: the weights Hugging Face downloads on the first start at
# /data/huggingface, the writable voice folder at /data/voices, and the encrypted token store at
# /data/tokens.json, so page uploads and API tokens survive a restart.
# HF_TOKEN, S2PRO_PASSWORD and S2PRO_PASSWORD_FILE are passed through only when the host environment sets them
# (fishaudio/s2-pro is public and needs no token; the service needs a password).
docker-run:
	docker run --rm --name leftenant-voice-tts-service --gpus device=$(GPU) -p 127.0.0.1:$(PORT):8000 -e ENGINE=$(ENGINE) -e IDLE_UNLOAD_SECONDS=$(IDLE_UNLOAD_SECONDS) \
	  -e HF_TOKEN -e S2PRO_PASSWORD -e S2PRO_PASSWORD_FILE -v leftenant-voice-tts-service-data:/data $(IMAGE):$(VERSION)

docker-tag:
	docker tag $(IMAGE):$(VERSION) $(IMAGE):latest

# Only latest is pushed. The token goes to docker login on stdin, never on argv; a temporary DOCKER_CONFIG keeps it out of ~/.docker/config.json
docker-push: docker-tag
	@D=$$(mktemp -d); trap 'rm -rf "$$D"' EXIT; \
	jupyterlab-passkey vault get gitlab/api | DOCKER_CONFIG=$$D docker login $(REGISTRY) -u konrad.jelen --password-stdin && \
	DOCKER_CONFIG=$$D docker push $(IMAGE):latest && \
	DOCKER_CONFIG=$$D docker logout $(REGISTRY)

# Deletes every tag except latest in the GitLab registry. The token reaches curl only through a temporary config file.
GITLAB_API := https://gitlab.nas.stellars-tech.eu:8443/api/v4
REGISTRY_PROJECT := $(GITLAB_API)/projects/konrad.jelen%2Fleftenant-voice-tts/registry/repositories
docker-prune:
	@C=$$(mktemp); trap 'shred -u "$$C"' EXIT; T=$$(jupyterlab-passkey vault get gitlab/api); \
	printf 'header = "PRIVATE-TOKEN: %s"\ninsecure\nsilent\n' "$$T" > "$$C"; \
	for R in $$(curl -K "$$C" "$(REGISTRY_PROJECT)" | python3 -c 'import json,sys; print(*[r["id"] for r in json.load(sys.stdin)])'); do \
	  for N in $$(curl -K "$$C" "$(REGISTRY_PROJECT)/$$R/tags?per_page=100" | python3 -c 'import json,sys; print(*[t["name"] for t in json.load(sys.stdin) if t["name"] != "latest"])'); do \
	    echo "$$N $$(curl -K "$$C" -o /dev/null -w '%{http_code}' -X DELETE "$(REGISTRY_PROJECT)/$$R/tags/$$N")"; \
	  done; \
	done
