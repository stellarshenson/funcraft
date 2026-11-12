VENV    := .venv-ming
PY      := $(VENV)/bin/python
CODE    := resources/models/Ming-3.0-tts
MODEL   := inclusionAI/Ming-3.0-tts-0.5B
REV     := 7247f4c94a5b2e987404ed28a5cfec41b1a4ca61
CODEREV := a39b80660bdc5a4394d5e1d41af6dbfd9c443a54
TORCH   := https://download.pytorch.org/whl/cu128
FLASH   := https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3+cu12torch2.7cxx11abiTRUE-cp311-cp311-linux_x86_64.whl

TOOLS      := .venv-tools
TPY        := $(TOOLS)/bin/python
ASR        := nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B
ASR_REV    := c17667641642c4265ff2b7037dd101b7d4567634
TRANSFORMERS := git+https://github.com/huggingface/transformers@826edb70cd5b7b4e5b8b66f396f90b88898fdec1
SRC_dijkstra := resources/assets/The Witcher 3 - Sigismund Dijkstra - All Voice Lines - All Dialogue.mp3
SRC_vesemir  := resources/assets/The Witcher 3 Wild Hunt - Vesemir Voice Lines.mp3
SRC_setrakian := resources/assets/Strain-Setrakian About love, love is our grace.mp3
SRC_grimaldus := resources/assets/Helsreach - Grimaldus Wall Speech.mp3
SRC_doctor   := resources/assets/The Doctor's Speech The Zygon Inversion Doctor Who.mp3
VOICES     := dijkstra vesemir setrakian grimaldus doctor
# Recordings with music or effects under the voice: separated with Demucs before segmenting
DEMUCS_VOICES := setrakian grimaldus doctor

.PHONY: install install-tools smoke voices speak test test-functional mp3

# Python 3.11 as in the model's Docker image; torch cu128 carries the sm_120 kernels of the RTX PRO 4000
# flash-attn: prebuilt wheel for torch 2.7, CUDA 12 and Python 3.11; it runs on sm_120 (checked with a real attention call)
install:
	test -d $(VENV) || uv venv --python 3.11 $(VENV)
	uv pip install --python $(PY) torch==2.7.1 torchaudio==2.7.1 --index-url $(TORCH)
	mkdir -p wip $(dir $(CODE))
	test -d $(CODE)/.git || git clone https://github.com/inclusionAI/Ming-3.0-tts $(CODE)
	git -C $(CODE) checkout -q $(CODEREV)
	grep -v '^torch' $(CODE)/requirements.txt > wip/requirements-ming.txt
	uv pip install --python $(PY) -r wip/requirements-ming.txt
	uv pip install --python $(PY) $(FLASH)
	$(PY) src/fetch_model.py $(MODEL) $(REV)

smoke:
	mkdir -p wip/logs
	$(PY) src/smoke.py 2>&1 | tee wip/logs/smoke.log

# Speech recognition, speaker model and audio tools; Nemotron needs transformers from source
install-tools:
	test -d $(TOOLS) || uv venv --python 3.11 $(TOOLS)
	uv pip install --python $(TPY) torch==2.7.1 torchaudio==2.7.1 --index-url $(TORCH)
	uv pip install --python $(TPY) $(TRANSFORMERS) accelerate huggingface_hub imageio-ffmpeg soundfile scipy \
		speechbrain sentencepiece librosa scikit-learn demucs
	$(TOOLS)/bin/hf download $(ASR) --revision $(ASR_REV)
	$(TOOLS)/bin/hf download speechbrain/spkrec-ecapa-voxceleb

# Clean segments and reference clips of every voice, from the recordings in resources/assets/.
# Nemotron runs on GPU 2 (needs about 64 GB free there); the speaker model runs on GPU 0.
voices:
	mkdir -p wip/logs
	$(foreach v,$(VOICES),$(TPY) src/decode_audio.py "$(SRC_$(v))" wip/voices/$(v) &&) true
	$(foreach v,$(DEMUCS_VOICES),$(TPY) src/separate_voice.py $(v) || test -f wip/voices/$(v)/mixed-44k.wav &&) true
	PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True $(TPY) src/transcribe.py 2 $(VOICES) 2>&1 | tee wip/logs/transcribe.log
	for v in $(VOICES); do \
		CUDA_VISIBLE_DEVICES= $(TPY) src/align.py $$v && $(TPY) src/embed.py $$v && $(TPY) src/build_voice.py $$v || exit 1; \
	done
	PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True $(TPY) src/verify_segments.py 2 $(VOICES) 2>&1 | tee wip/logs/verify.log
	python3 src/prune_segments.py $(VOICES)

# Usage: make speak VOICE=<name> TEXT="<text>" OUT=<path>   or   make speak VOICE=<name> FILE=<path> OUT=<path>
# Whole-text controls, all optional: EMOTION=<e>   or   SPEED=<s> PITCH=<p> VOLUME=<v>   (README, Controls)
speak:
	$(PY) src/speak.py --voice $(VOICE) $(if $(FILE),--text-file "$(FILE)",--text "$(TEXT)") --out "$(OUT)" \
		$(if $(EMOTION),--emotion $(EMOTION)) $(if $(SPEED),--speed $(SPEED)) $(if $(PITCH),--pitch $(PITCH)) $(if $(VOLUME),--volume $(VOLUME))
	$(MAKE) mp3

# The service's unit suite (s2pro.mk): no GPU and no model; `make -f s2pro.mk install-test` once
test:
	$(MAKE) -f s2pro.mk test

# The service's functional suite (s2pro.mk): the real service on a GPU, then the image
test-functional:
	$(MAKE) -f s2pro.mk test-functional

# Every render under out/ is an MP3: converts each WAV there (MP3DIR, default out) with the quality of ffmpeg -q:a 2,
# scaled down to a -1 dBFS peak so the MP3 decoder's overshoot stays under full scale, checks the lengths agree within
# 0.2 s, and moves the WAV to the trash. Needs ffmpeg with libmp3lame, ffprobe and trash-put.
MP3DIR ?= out
MP3_PEAK_DB := -1
mp3:
	@find $(MP3DIR) -name '*.wav' -not -path '*/.ipynb_checkpoints/*' | while IFS= read -r wav; do \
		peak=$$(ffmpeg -nostdin -i "$$wav" -af volumedetect -f null - 2>&1 | awk -F': ' '/max_volume/ {print $$2+0; exit}'); \
		gain=$$(awk -v p="$$peak" -v t="$(MP3_PEAK_DB)" 'BEGIN { g = t - p; if (g > 0) g = 0; printf "%.2f", g }'); \
		mp3="$${wav%.wav}.mp3"; \
		ffmpeg -nostdin -loglevel error -y -i "$$wav" -af "volume=$${gain}dB" -codec:a libmp3lame -q:a 2 "$$mp3" || exit 1; \
		a=$$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$$wav"); \
		b=$$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$$mp3"); \
		awk -v a="$$a" -v b="$$b" 'BEGIN { d = a - b; exit !(d < 0.2 && d > -0.2) }' || { echo "length differs: $$wav $$a s, $$mp3 $$b s"; exit 1; }; \
		trash-put "$$wav" && echo "$$mp3"; \
	done
