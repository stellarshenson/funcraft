"""Run before src/scenes.py: every render takes the seed $SEED, and each written frame is copied into
wip/frames-saint-seed$SEED/, so two seeds of one frame show the render's noise. Run seed 0 last: it is the seed of
the normal render, and the frame in wip/frames-saint/ is overwritten.

    SEED=1 blender -b -P src/warhound/seedtest.py -P src/scenes.py -- saint 10
"""
import os, shutil, bpy
from bpy.app.handlers import persistent

SEED = os.environ.get("SEED", "0")


@persistent
def seeded(scene, *_):
    scene.cycles.seed = int(SEED)


@persistent
def keep(scene, *_):
    src = bpy.path.abspath(scene.render.filepath)
    out = src.replace("frames-saint", "frames-saint-seed" + SEED)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copy2(src, out)
    print("SEED", SEED, "copied to", out, "seed", scene.cycles.seed, flush=True)


bpy.app.handlers.render_pre.append(seeded)
bpy.app.handlers.render_write.append(keep)
