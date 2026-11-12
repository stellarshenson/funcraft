# Audio8-TTS-Realistic-Air (Edge0, 0.6B) for the tts-trial. Usage:
#   make -f audio8.mk install
#   tmp/workflows/gpu2-queue.sh .venv-audio8/bin/python wip/tts-trial/audio8-air/speak_audio8.py --smoke|--status
AVENV  := .venv-audio8
APY    := $(AVENV)/bin/python
AMODEL := Edge0/Audio8-TTS-Realistic-Air
AREV   := 23c305cc013fde378edb459f538317043c993a74
ATORCH := https://download.pytorch.org/whl/cu128

.PHONY: install

# Versions as the model card smoke-tested them: torch 2.8.0, transformers 4.57.3 (custom code, trust_remote_code)
install:
	test -d $(AVENV) || uv venv --python 3.12 $(AVENV)
	uv pip install --python $(APY) torch==2.8.0 torchaudio==2.8.0 --index-url $(ATORCH)
	uv pip install --python $(APY) --extra-index-url $(ATORCH) transformers==4.57.3 soundfile safetensors huggingface_hub numpy
	$(AVENV)/bin/hf download $(AMODEL) --revision $(AREV)
