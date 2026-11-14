"""The painted Warhound's head close up, from its right side and from the front at its right, in the studio light of
src/warhound.py lookdev: wip/preview/warhound-head-<stem>-side.png and -iso.png.

    CUDA_VISIBLE_DEVICES=1 blender -b -P src/warhound/headlook.py -- <stem>
"""
import os, sys
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import warhound as WH

stem = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
root, obs, _ = WH.model()
for o in obs:
    o.hide_render = o.name != "head"
s = bpy.context.scene
WH.setup(samples=64)
s.view_settings.view_transform = "AgX"
s.view_settings.look = "AgX - Medium High Contrast"
s.world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.37, 0.40, 1)
s.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
WH.views([o for o in obs if o.name == "head"], "warhound-head-" + stem, [("side", (-1, 0, 0), (0, 0, 1)), ("iso", (-1, -1, 0.4), (0, 0, 1))])
