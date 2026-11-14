"""The cloth object of a plate scene (wip/scene3d/<name>_drape.npz, src/goldwork.py) alone, seen from the scene's
camera and from four other places, to check that it is a draped surface: wip/preview/frames3d/drape-<name>-views.png.

    CUDA_VISIBLE_DEVICES=1 blender -b -P src/muster/drapeview.py -- forge
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
name = sys.argv[sys.argv.index("--") + 1]
stem = os.path.join(ROOT, "wip", "scene3d", name)
d = np.load(stem + "_drape.npz")
bpy.ops.wm.read_factory_settings(use_empty=True)
V, q = d["V"], d["quads"]
me = bpy.data.meshes.new("drape")
me.vertices.add(len(V))
me.vertices.foreach_set("co", V.ravel())
me.loops.add(q.size)
me.loops.foreach_set("vertex_index", q.ravel())
me.polygons.add(len(q))
me.polygons.foreach_set("loop_start", np.arange(0, q.size, 4))
me.polygons.foreach_set("loop_total", np.full(len(q), 4))
me.uv_layers.new(name="uv").data.foreach_set("uv", d["uv"][q.ravel()].ravel())
me.uv_layers.new(name="chart").data.foreach_set("uv", d["chart"][q.ravel()].ravel())
me.update()
me.polygons.foreach_set("use_smooth", np.ones(len(q), bool))
ob = bpy.data.objects.new("drape", me)
bpy.context.collection.objects.link(ob)
m = bpy.data.materials.new("drape")
m.use_nodes = True
N, L = m.node_tree.nodes, m.node_tree.links
b = N["Principled BSDF"]
tex = N.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(stem + "_clean.png")
work = d["work"].astype(np.float32)
h, w = work.shape[:2]
img = bpy.data.images.new("work", w, h, float_buffer=True, is_data=True)
img.pixels.foreach_set(np.concatenate([work[::-1], np.ones((h, w, 1), np.float32)], 2).ravel())
t2 = N.new("ShaderNodeTexImage")
t2.image, t2.extension = img, "CLIP"
um = N.new("ShaderNodeUVMap")
um.uv_map = "chart"
L.new(um.outputs["UV"], t2.inputs["Vector"])
sep = N.new("ShaderNodeSeparateColor")
L.new(t2.outputs["Color"], sep.inputs["Color"])
mix = N.new("ShaderNodeMix")
mix.data_type = "RGBA"
L.new(sep.outputs["Red"], mix.inputs["Factor"])
L.new(tex.outputs["Color"], mix.inputs["A"])
mix.inputs["B"].default_value = (0.9, 0.6, 0.15, 1)
L.new(mix.outputs["Result"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.7
me.materials.append(m)
mid = Vector(V.mean(0).tolist())
s = bpy.context.scene
s.world = bpy.data.worlds.new("w")
s.world.use_nodes = True
s.world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.35, 0.35, 1)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.0
bpy.context.collection.objects.link(sun)
cd = bpy.data.cameras.new("cam")
cd.lens = 85
cam = bpy.data.objects.new("cam", cd)
bpy.context.collection.objects.link(cam)
s.camera = cam
s.render.engine = "CYCLES"
s.cycles.device = "GPU"
s.cycles.samples = 48
pr = bpy.context.preferences.addons["cycles"].preferences
pr.compute_device_type = "CUDA"
pr.get_devices()
for dv in pr.devices:
    dv.use = dv.type == "CUDA"
s.render.resolution_x, s.render.resolution_y = 560, 900
s.view_settings.view_transform = "Standard"
out = []
dist = mid.length
for tag, yaw, pitch in (("camera", 0, 0), ("left60", -60, 0), ("right60", 60, 0), ("left85", -85, 0), ("above50", 0, 50)):
    back = Vector((0, -1, 0))                                  # from the cloth towards the scene's camera
    to = (-mid).normalized()
    a, p = math.radians(yaw), math.radians(pitch)
    dirn = Vector((to.x * math.cos(a) - to.y * math.sin(a), to.x * math.sin(a) + to.y * math.cos(a), to.z))
    dirn = (dirn * math.cos(p) + Vector((0, 0, 1)) * math.sin(p)).normalized()
    cam.location = mid + dirn * dist
    cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
    sun.rotation_euler = ((cam.location - mid) + Vector((-1.0, 0, 0.6))).to_track_quat("Z", "Y").to_euler()
    path = os.path.join(ROOT, "wip", "preview", "frames3d", f"drape-{name}-{tag}.png")
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
    out.append(path)
print("VIEWS " + " ".join(out))
