BLENDER ?= $(HOME)/.local/opt/blender-4.5.9-linux-x64/blender
PYTHON  ?= /opt/conda/bin/python3.14
CHASSIS ?= madcat

.PHONY: banner banner-shake banner-offset frames gif lookdev rig rigcheck weights measure cuts gait clean

banner: frames gif

frames:
	rm -rf wip/frames && mkdir -p wip/frames
	$(BLENDER) -b -P src/gen04_banner_models.py

gif:
	$(PYTHON) src/assemble.py

banner-shake:
	rm -rf wip/frames-shake
	$(BLENDER) -b -P src/gen04_banner_models.py -- shake out=frames-shake
	$(PYTHON) src/assemble.py wip/frames-shake out/04-banner-shake.gif

banner-offset:
	rm -rf wip/frames-offset
	$(BLENDER) -b -P src/gen04_banner_models.py -- shake offset out=frames-offset
	$(PYTHON) src/assemble.py wip/frames-offset out/05-banner-offset.gif

lookdev:
	$(BLENDER) -b -P src/lookdev.py
	$(PYTHON) src/sheet.py

rig:
	$(BLENDER) -b -P src/rigtest.py
	$(PYTHON) src/rigsheet.py

rigcheck:
	$(BLENDER) -b -P src/rigcheck.py

weights:
	$(BLENDER) -b -P src/weightview.py

measure:
	for m in madcat atlas battlemaster; do $(BLENDER) -b -P src/measure.py -- $$m; done

cuts:
	$(BLENDER) -b -P src/cuttest.py -- $(CHASSIS)

gait:
	$(BLENDER) -b -P src/striptest.py -- $(CHASSIS)

clean:
	rm -rf wip/frames wip/frames-* src/__pycache__ src/_probe.py
