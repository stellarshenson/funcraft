# DEFINE (AMAAI-Lab accent add-on for F5-TTS) beside plain F5-TTS. Usage:
#   make -f define.mk install
#   tmp/workflows/gpu2-queue.sh make -f define.mk render MODE=plain OUT=out/trial/status-grimaldus-f5.wav
DVENV  := .venv-define
DPY    := $(DVENV)/bin/python
DWORK  := wip/tts-trial/define
DCODE  := $(DWORK)/code
DREPO  := https://github.com/AMAAI-Lab/define
DCODEREV := eba0e2e4567a97c0a11d1716946a207a6763a7a1
DSPACE := amaai-lab/define
DSPACEREV := 5d0c6deac47561f149f4dda835dafe4fcfeb5a84
F5REPO := SWivid/F5-TTS
F5FILE := F5TTS_v1_Base/model_1250000.safetensors
DTORCH := https://download.pytorch.org/whl/cu128
MODE   ?= plain
TEXT   ?= tmp/workflows/ming-status/status-plain.txt
OUT    ?= $(DWORK)/render-$(MODE).wav

.PHONY: install render

# Python 3.11 as the README says; torch 2.8.0 for CUDA 12.8 (sm_120). The checkpoint accentbridge.pt is in the Hugging Face Space
# (the README points to Google Drive); the other weights download into the local Hugging Face cache on first use
install:
	test -d $(DVENV) || uv venv --python 3.11 $(DVENV)
	test -d $(DCODE)/.git || git clone $(DREPO) $(DCODE)
	git -C $(DCODE) checkout -q $(DCODEREV)
	uv pip install --python $(DPY) torch==2.8.0 torchaudio==2.8.0 --index-url $(DTORCH)
	uv pip install --python $(DPY) --extra-index-url $(DTORCH) -r $(DCODE)/requirements.txt
	$(DVENV)/bin/hf download $(DSPACE) accentbridge.pt --repo-type space --revision $(DSPACEREV)
	$(DVENV)/bin/hf download $(F5REPO) $(F5FILE)
	$(DVENV)/bin/hf download charactr/vocos-mel-24khz
	$(DVENV)/bin/hf download facebook/wav2vec2-xls-r-300m

# MODE plain (stock F5-TTS) or scottish (DEFINE, exemplar doctor.wav); run through tmp/workflows/gpu2-queue.sh
render:
	mkdir -p $(dir $(OUT))
	$(DPY) $(DWORK)/render.py --mode $(MODE) --text-file $(TEXT) --out $(OUT)
	$(MAKE) -f Makefile mp3
