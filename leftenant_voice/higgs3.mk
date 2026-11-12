# Higgs TTS 3 (4B, Boson AI) served by SGLang-Omni, in its own venv. Usage:
#   make -f higgs3.mk install
#   make -f higgs3.mk serve        (runs on the GPU the caller fixed with CUDA_VISIBLE_DEVICES)
HVENV  := .venv-higgs3
HPY    := $(HVENV)/bin/python
HMODEL := bosonai/higgs-tts-3-4b
HREV   := 239f63fb7b02b1aa085f98d9efae5e35cc5523e8
HSGL   := sglang-omni==0.2.0
HPORT  ?= 8013
HSNAP  := $(HOME)/.cache/huggingface/hub/models--bosonai--higgs-tts-3-4b/snapshots/$(HREV)

.PHONY: install serve

# serve points at the pinned local snapshot (a download by revision writes no refs/main for the Hub lookup); --allowed-local-media-path lets requests name the reference WAVs by path
# sglang-omni 0.2.0 from PyPI as its installation page gives; the weights (not gated, no token) go to the local Hugging Face cache
install:
	test -d $(HVENV) || uv venv --python 3.12 $(HVENV)
	uv pip install --python $(HPY) --prerelease=allow "$(HSGL)" huggingface_hub
	$(HVENV)/bin/hf download $(HMODEL) --revision $(HREV)

serve:
	$(HVENV)/bin/sgl-omni serve --model-path $(HSNAP) --model-name $(HMODEL) --port $(HPORT) --allowed-local-media-path $(CURDIR)/wip/fish/refs
