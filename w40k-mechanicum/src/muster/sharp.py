"""A trial of the fine detail of the muster scene: one frame with another filter for the pictures that lie on the
surfaces (Blender: Linear, Closest, Cubic, Smart) and another width of the renderer's pixel filter. The scene itself
is not changed.

    CUDA_VISIBLE_DEVICES=1 blender -b -P src/muster/sharp.py -- <frame> <filter of the pictures> <width of the pixel filter> <out.png>
"""
import os, sys
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import muster as M

frame, how, wide, out = sys.argv[sys.argv.index("--") + 1:]
pose = M.scene()
count = 0
for mat in bpy.data.materials:
    for node in (mat.node_tree.nodes if mat.node_tree else []):
        if node.type == "TEX_IMAGE" and node.interpolation == "Cubic":
            node.interpolation, count = how, count + 1
s = bpy.context.scene
s.cycles.filter_width = float(wide)
pose(int(frame))
s.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
print(f"TRIAL_DONE {count} pictures set to {how}, pixel filter {wide} px, wrote {out}")
