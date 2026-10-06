BLENDER ?= $(HOME)/.local/opt/blender-4.5.9-linux-x64/blender
PYTHON  ?= /opt/conda/bin/python3.14
CHASSIS ?= madcat

.PHONY: banner banner-shake banner-offset procession procession-hips procession-column procession-marauder marauder welcome frames gif lookdev rig rigcheck weights measure cuts gait clean

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

# banner 07 (PROCESSION.md): the data of its steps 1 to 7 must exist under wip/
procession:
	rm -rf wip/frames-procession
	$(BLENDER) -b -P src/procession/scene.py -- livery=livery
	$(PYTHON) src/assemble.py wip/frames-procession out/07-banner-procession.avif

# banner 08: banner 07 with rocking hips (src/procession/hips.py)
procession-hips:
	rm -rf wip/frames-procession-hips
	$(BLENDER) -b -P src/procession/scene.py -- livery=livery hips=4.5 out=frames-procession-hips
	$(PYTHON) src/assemble.py wip/frames-procession-hips out/08-banner-procession-hips.avif

# banner 09: banner 08 with six more mechs behind the three (REAR in src/procession/frame.py)
procession-column:
	rm -rf wip/frames-procession-column
	$(BLENDER) -b -P src/procession/scene.py -- livery=livery hips=4.5 rear=6 out=frames-procession-column
	$(PYTHON) src/assemble.py wip/frames-procession-column out/09-banner-procession-column.avif

# banner 10: banner 09 with the Marauder in the place of the rear BattleMaster between the Atlas and the Mad Cat, and
# with cloth banners on the Marauder and on the Mad Cat of the three
procession-marauder:
	rm -rf wip/frames-procession-ten
	$(BLENDER) -b -P src/procession/scene.py -- livery=livery hips=4.5 rear=6 marauder=0 cloth=1 out=frames-procession-ten
	$(PYTHON) src/assemble.py wip/frames-procession-ten out/10-banner-procession-marauder.avif

# the fourth chassis: the Marauder, assembled from the kit in in/models/marauder/parts (PROCESSION.md, section 10)
marauder:
	$(BLENDER) -b -P src/marauder.py -- build

# the BEHEMOTH welcome page of GalaxaLab: src/welcome.template.html with the banner embedded, one self-contained file
welcome:
	$(PYTHON) src/welcome.py

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
