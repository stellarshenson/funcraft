"""The Warhound's head in its place on the model (rest pose), seen from its right side, each flat patch of faces in a
colour of its own: wip/preview/warhound-head-patches.png. With pixels: the face under each pixel of that picture, its
patch (src/warhound.py patches()), the patch's area, normal and box in kit mm.

    blender -b -P src/warhound/headpick.py                     # the picture
    blender -b -P src/warhound/headpick.py -- 520,410 700,380   # the patches under those pixels
    blender -b -P src/warhound/headpick.py -- poly 26.0 345,370 405,385 ...   # those pixels on the plane x = 26.0 (kit mm)
"""
import colorsys, os, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import warhound as WH

SIDE = 1100
bpy.ops.wm.read_factory_settings(use_empty=True)
mats = WH.materials()
o = WH.painted("head", mats)
M = WH.assemble()["head"]
o.matrix_world = M
bm = bmesh.new()
bm.from_mesh(o.data)
bm.faces.ensure_lookup_table()
area, root = WH.patches(bm)
m = bpy.data.materials.new("patches")
m.use_nodes = True
N = m.node_tree.nodes
at = N.new("ShaderNodeAttribute")
at.attribute_name = "tone"
m.node_tree.links.new(at.outputs["Color"], N["Principled BSDF"].inputs["Base Color"])
col = o.data.color_attributes.new("tone", "FLOAT_COLOR", "CORNER")
rng = np.random.default_rng(1)
hue = {r: rng.random() for r in set(root)}
for f, r in zip(o.data.polygons, root):
    c = colorsys.hsv_to_rgb(hue[r], 0.8, 0.9) if area[f.index] >= WH.PATCH else (0.15, 0.15, 0.15)
    for li in f.loop_indices:
        col.data[li].color = (*c, 1)
o.data.materials.clear()
o.data.materials.append(m)
WH.setup(samples=16, side=SIDE)
pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
lo = Vector([min(p[k] for p in pts) for k in range(3)])
hi = Vector([max(p[k] for p in pts) for k in range(3)])
mid, size = (lo + hi) / 2, (hi - lo).length
d, up = Vector((-1, 0, 0)), Vector((0, 0, 1))
cd = bpy.data.cameras.new("c")
cd.type, cd.ortho_scale, cd.clip_end = "ORTHO", 1.02 * size, 10 * size
cam = bpy.data.objects.new("cam", cd)
bpy.context.collection.objects.link(cam)
cam.location = mid + d * 3 * size
cam.rotation_euler = WH._look(-d, up)
bpy.context.scene.camera = cam
bpy.context.view_layer.update()
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    bpy.context.scene.render.filepath = os.path.join(WH.PREVIEW, "warhound-head-patches.png")
    bpy.ops.render.render(write_still=True)
inv = M.inverted()
R = cam.matrix_world.to_3x3()
if args[:1] == ["poly"]:
    x0, Mi = float(args[1]), inv.to_3x3()
    out = []
    for a in args[2:]:
        u, v = (float(x) for x in a.split(","))
        o0 = inv @ (cam.location + R @ Vector(((u / SIDE - 0.5) * 1.02 * size, (0.5 - v / SIDE) * 1.02 * size, 0)))
        dk = Mi @ (-d)
        p = o0 + dk * ((x0 - o0.x) / dk.x)
        out.append((round(p.y, 2), round(p.z, 2)))
    print("POLY view in kit", [round(c, 3) for c in (Mi @ (-d)).normalized()], out)
    args = []
for a in args:
    u, v = (float(x) for x in a.split(","))
    off = R @ Vector(((u / SIDE - 0.5) * 1.02 * size, (0.5 - v / SIDE) * 1.02 * size, 0))
    hit, loc, nrm, fi, ob, _ = bpy.context.scene.ray_cast(bpy.context.view_layer.depsgraph, cam.location + off, -d * 1.0)
    if not hit:
        print("PICK", a, "nothing")
        continue
    r = root[fi]
    fs = [f for f in bm.faces if root[f.index] == r]
    cs = np.array([f.calc_center_median() for f in fs])
    print("PICK", a, "face", fi, "patch", r, "faces", len(fs), "area mm2", round(area[fi], 2),
          "normal kit", [round(x, 3) for x in bm.faces[fi].normal], "centre kit", [round(x, 2) for x in bm.faces[fi].calc_center_median()],
          "box kit", [round(x, 2) for x in cs.min(0)], [round(x, 2) for x in cs.max(0)])
