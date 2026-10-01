"""Render the cog-and-skull medallion as a flat gold image with a transparent
background, for the banner textures.

Run:
    blender -b -P src/emblem.py

Writes resources/assets/emblem.png (1024 x 1024).
"""
import bpy, os, math
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "in", "models", "originals", "ornament-mechanicus-symbol", "TP_Symbol_-_all.stl")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=SRC)
ob = bpy.context.selected_objects[0]
ob.rotation_euler = (0, math.pi, 0)          # upside down as downloaded
bpy.context.view_layer.update()
m = bpy.data.materials.new("gold")
m.use_nodes = True
b = m.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.85, 0.62, 0.26, 1)
b.inputs["Metallic"].default_value = 1.0
b.inputs["Roughness"].default_value = 0.35
ob.data.materials.append(m)

pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
c, d = (lo + hi) / 2, hi - lo

s = bpy.context.scene
s.render.engine = "CYCLES"
s.cycles.device = "GPU"
s.cycles.samples = 64
pr = bpy.context.preferences.addons["cycles"].preferences
pr.compute_device_type = "CUDA"
pr.get_devices()
for dv in pr.devices:
    dv.use = dv.type == "CUDA"
s.render.resolution_x = s.render.resolution_y = 1024
s.render.film_transparent = True
s.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w")
s.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.45, 0.4, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
sun = bpy.data.lights.new("sun", "SUN")
sun.energy = 4.0
so = bpy.data.objects.new("sun", sun)
so.rotation_euler = (math.radians(-55), math.radians(-25), 0)     # from above-left, towards +Y face
s.collection.objects.link(so)
cd = bpy.data.cameras.new("cam")
cd.type = "ORTHO"
cd.ortho_scale = max(d.x, d.z) * 1.02
cam = bpy.data.objects.new("cam", cd)
s.collection.objects.link(cam)
s.camera = cam
cam.location = c + Vector((0, d.length * 2, 0))                     # the relief faces +Y
cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
s.render.filepath = os.path.join(ROOT, "resources", "assets", "emblem.png")
bpy.ops.render.render(write_still=True)
