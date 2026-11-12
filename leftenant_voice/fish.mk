# Fish Audio Drama 3 beside Ming. Usage:
#   make -f fish.mk install
#   make -f fish.mk speak VOICE=dijkstra FILE=texts/fish/inspiring-speech-fish.txt OUT=out/fish/inspiring-speech-dijkstra-fish.mp3
FVENV  := .venv-fish
FPY    := $(FVENV)/bin/python
FCODE  := src/fish/fish-speech
FREPO  := https://github.com/fishaudio/fish-speech
FCODEREV := 0f8a12e8a651062fdee9c33a894bdccd3a8513f1
FMODEL := fishaudio/drama-3
FREV   := 78e5ab79e49aa9a25abe8799eff2c4d73a1c3216
FTORCH := https://download.pytorch.org/whl/cu128
FGPU   ?= 1
LOG    ?= wip/fish/logs/speak-$(VOICE).log

FSNAP  := $(HOME)/.cache/huggingface/hub/models--fishaudio--drama-3/snapshots/$(FREV)
FNAS   := /mnt/nas-shared/models/fishaudio--drama-3

.PHONY: install speak nas mp3

# Python 3.12 and torch 2.8.0 for CUDA 12.8 (sm_120) as the repository pins; pyaudio needs apt portaudio19-dev
install:
	test -d $(FVENV) || uv venv --python 3.12 $(FVENV)
	test -d $(FCODE)/.git || git clone $(FREPO) $(FCODE)
	git -C $(FCODE) checkout -q $(FCODEREV)
	uv pip install --python $(FPY) torch==2.8.0 torchaudio==2.8.0 --index-url $(FTORCH)
	uv pip install --python $(FPY) --extra-index-url $(FTORCH) -e $(FCODE)
	$(FVENV)/bin/hf download $(FMODEL) --revision $(FREV)

# Needs VOICE (a name under wip/fish/refs/), FILE (text) and OUT (an MP3 under out/); runs on GPU $(FGPU); the log goes to LOG
speak:
	test -n "$(VOICE)" -a -n "$(FILE)" -a -n "$(OUT)"
	mkdir -p $(dir $(OUT)) $(dir $(LOG))
	CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$(FGPU) $(FPY) src/fish/speak_fish.py \
		--voice $(VOICE) --file $(FILE) --out $(OUT) 2>&1 | tee $(LOG)
	$(MAKE) -f Makefile mp3

# The rule of Makefile: every render under out/ is an MP3
mp3:
	$(MAKE) -f Makefile mp3

# Archive the weights on the NAS as flat files. The NFS mount is soft and reports stale sizes, and a stalled write returns an I/O error,
# so each file is compared byte by byte and rewritten with direct 16 MiB writes from the block of the first difference, until it matches
nas:
	mkdir -p $(FNAS)
	for f in $$(ls $(FSNAP)); do \
		for i in $$(seq 1 200); do \
			out=$$(cmp $(FSNAP)/$$f $(FNAS)/$$f 2>&1) && break; \
			blocks=$$(( ($$(echo "$$out" | grep -o 'byte [0-9]*' | head -1 | cut -d' ' -f2 | grep . || echo 1) - 1) / 16777216 )); \
			echo "pass $$i $$f from block $$blocks"; \
			dd if=$(FSNAP)/$$f of=$(FNAS)/$$f bs=16M skip=$$blocks seek=$$blocks oflag=direct conv=notrunc status=none || sleep 20; \
		done; \
		cmp $(FSNAP)/$$f $(FNAS)/$$f || exit 1; \
	done
	touch wip/fish/nas.verified
