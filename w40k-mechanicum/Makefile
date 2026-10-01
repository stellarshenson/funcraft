BLENDER ?= $(HOME)/.local/opt/blender-4.5.9-linux-x64/blender
PYTHON ?= python3
export CUDA_VISIBLE_DEVICES ?= 1

.PHONY: banner frames gif assets previews clean

banner: frames gif

frames:
	rm -rf wip/frames && mkdir -p wip/frames
	$(BLENDER) -b -P src/mechanicum.py

gif:
	$(PYTHON) src/assemble.py

assets:
	$(BLENDER) -b -P src/emblem.py
	$(PYTHON) src/textures.py

previews:
	$(BLENDER) -b -P src/preview_models.py

clean:
	rm -rf wip/frames
