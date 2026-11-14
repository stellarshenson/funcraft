# voice TTS service: an HTTP API over the S2 Pro engine, built from the project folder:
#   docker build -f service/Dockerfile -t IMAGE .
# The weights are not in the image: the first start downloads them from Hugging Face into the cache at
# /data/huggingface, which the data volume holds across restarts together with the voices and the tokens.
FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive VOICES_DIR=/data/voices HF_HOME=/data/huggingface SEED_VOICES_DIR=/app/seed-voices \
    PYTHONPATH=/app/src/fish:/app/src PYTHONUNBUFFERED=1 CUDA_DEVICE_ORDER=PCI_BUS_ID ENGINE=s2pro
# portaudio19-dev, gcc and python3-dev: fish-speech depends on pyaudio, which builds from source
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ffmpeg libsndfile1 gcc portaudio19-dev python3 python3-dev python3-venv curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# torch 2.8.0 for CUDA 12.8 carries the Blackwell (sm_120) kernels; fish-speech at the commit .venv-fish pins
ARG TORCH_INDEX=https://download.pytorch.org/whl/cu128
ARG FISH_REV=0f8a12e8a651062fdee9c33a894bdccd3a8513f1
RUN uv venv --python 3.12 /opt/venv
ENV PATH=/opt/venv/bin:$PATH VIRTUAL_ENV=/opt/venv
RUN uv pip install torch==2.8.0 torchaudio==2.8.0 --index-url $TORCH_INDEX
RUN git clone https://github.com/fishaudio/fish-speech /opt/fish-speech \
    && git -C /opt/fish-speech checkout -q $FISH_REV \
    && uv pip install --extra-index-url $TORCH_INDEX -e /opt/fish-speech \
    && uv pip install fastapi uvicorn python-multipart cryptography

# The Transformers pin override is deliberate: fish-speech pins transformers==5.19.0, which does not carry the
# transformers.models.nemotron3_5_transcribe module the Nemotron 3.5 Transcribe model needs. This dev build
# (5.23.0.dev0 at 826edb70) is the measured transcription runtime and it also serves the S2 Pro speech path,
# so one venv holds both engines and no second copy of torch is needed. torch and torchaudio stay at 2.8.0.
# Weights are not in the image; the first use downloads them into /data/huggingface.
# DEF-ASR-6: nemotron_worker.py loads the model with device_map="cuda:0", which Transformers refuses without accelerate.
RUN uv pip install "transformers @ git+https://github.com/huggingface/transformers@826edb70cd5b7b4e5b8b66f396f90b88898fdec1" librosa accelerate

WORKDIR /app
COPY src/audio_out.py src/speak_text.py src/
COPY src/fish/speak_s2pro.py src/fish/
COPY service/*.py service/
COPY service/static service/static
# The bundled voices are the read-only seed; /data/voices is the writable copy the page uploads into
COPY service/voices /app/seed-voices
RUN mkdir -p /data/voices

# Runtime settings app.py reads: a default for each, so `docker run` without -e behaves as service/README.md says
ENV IDLE_UNLOAD_SECONDS=3600 MAX_TEXT_CHARS=3000

EXPOSE 8000
# /health answers before the model is loaded, so the probe marks the container healthy during the load
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=300s \
    CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "app:app", "--app-dir", "/app/service", "--host", "0.0.0.0", "--port", "8000"]
