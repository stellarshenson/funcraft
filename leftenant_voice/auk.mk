# AuK and AuK-Flash (Tencent, 1.5B) zero-shot cloning trial. Usage:
#   make -f auk.mk install
#   make -f auk.mk speak MODEL=auk OUT=out/trial/status-grimaldus-auk.wav     (MODEL: auk or auk-flash; run through gpu2-queue.sh)
AVENV  := .venv-auk
APY    := $(AVENV)/bin/python
AWORK  := wip/tts-trial/auk
ACODE  := $(AWORK)/AuK
AREPO  := https://github.com/Tencent-Hunyuan/AuK
ACODEREV := 0d40366b1039e37c6cad008ab4713f6ad6d954b7
ATORCH := https://download.pytorch.org/whl/cu128
AUK_REV   := 790742b71a4430120daf2b2099192abae449eb9f
FLASH_REV := 575b92f0895f75180bf2cbd35f2e176c5732b8ed
QWEN_REV  := f75b40e3da2003cdd6e1829b1f420ca70797c34e
OUT    ?= out/trial/status-grimaldus-$(MODEL).wav
LOG    ?= wip/logs/tts-trial-$(MODEL)-speak.log

.PHONY: install speak

# Python 3.10 and torch 2.7 for CUDA 12.8 (sm_120) inside the repository's pins <2.8; weights go to the Hugging Face cache
install:
	test -d $(AVENV) || uv venv --python 3.10 $(AVENV)
	test -d $(ACODE)/.git || git clone $(AREPO) $(ACODE)
	git -C $(ACODE) checkout -q $(ACODEREV)
	uv pip install --python $(APY) "torch>=2.7,<2.8" "torchaudio>=2.7,<2.8" "torchvision>=0.22,<0.23" --index-url $(ATORCH)
	uv pip install --python $(APY) --extra-index-url $(ATORCH) -e $(ACODE) soundfile
	$(AVENV)/bin/hf download tencent/AuK --revision $(AUK_REV)
	$(AVENV)/bin/hf download tencent/AuK-Flash --revision $(FLASH_REV)
	$(AVENV)/bin/hf download Qwen/Qwen2.5-Omni-3B --revision $(QWEN_REV)

# Needs MODEL (auk or auk-flash); the GPU is chosen by the caller (gpu2-queue.sh)
speak:
	test -n "$(MODEL)"
	mkdir -p $(dir $(OUT)) $(dir $(LOG))
	$(APY) $(AWORK)/speak_auk.py --model $(MODEL) --out $(OUT) $(ARGS) 2>&1 | tee $(LOG)
	$(MAKE) -f Makefile mp3
