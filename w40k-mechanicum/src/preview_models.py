"""Preview the downloaded models: each from the front (-Y), the side (+X) and
above, in grey, with its dimensions and face count printed.

Run:
    blender -b -P src/preview_models.py [-- name ...]

Writes wip/preview/models/<name>.png (three views side by side is done by
preview_sheet in the same run).
"""
import bpy, os, sys, math
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "in", "models", "originals")
OUT = os.path.join(ROOT, "wip", "preview", "models")

SETS = {
    "priest-techno-gothic": ["tech-priest-techno-gothic/techno-gothic-priest-stl.stl"],
    "priest-datasmith": ["tech-priest-info-artisan/Martian Info-Artisan - 3591216/files/Datasmith.stl"],
    "priest-statue": ["tech-priest-statue/Tech Priest statue - 4786550/files/statue_Ad_Mech.stl"],
    "servo-skull": ["servo-skull-plasmastorm-NC/Servo_Skull_Cables.stl"],
    "skull-cc0": ["servo-skull-base-human-skull-cc0/skull_w_jaw.stl"],
    "gpu-3070": ["gpu-rtx3060-3070-fans/Geforce RTX 3060 & 3070 - 4889698/files/" + f
                 for f in ("Body1.stl", "Left.stl", "Right.stl", "Left_Fan.stl", "Right_Fan.stl", "LeftM.stl", "rightM.stl")],
    "gpu-3080": ["gpu-rtx3080-fe/RTX 3080 Founder's Edition - 4590289/files/RTX_3080_FE.stl"],
    "censer": ["censer-thurible/Thurible_Censer Prop with Insert for Mini Smoke Machine - 7318933/files/" + f
               for f in ("Thurible__Base.stl", "Thurible__Lid.stl", "Thurible__Handle.stl")],
    "candleholders": ["candles-brass-candleholders/brass_candleholders_2k_gltf/brass_candleholders_2k.gltf"],
    "symbol": ["ornament-mechanicus-symbol/TP_Symbol_-_all.stl"],
    "rose-window": ["gothic-building-components/Gothic Building Components - 6011872 - part 1 of 2/files/rosace_milano_280x205x7.stl"],
    "stained-glass": ["gothic-window-stained-glass/Gothic Window - 815120/files/Stained_Glass.stl"],
    "gothic-statue": ["gothic-statue-polyhaven/gothic_statue_2k_gltf/gothic_statue_2k.gltf"],
    "ruin-c1-bottom": ["gothic-scifi-ruin-terrain4print-NC/corner-1-bottom-A.stl"],
    "ruin-c1-middle": ["gothic-scifi-ruin-terrain4print-NC/corner-1-middle-A.stl"],
    "ruin-c1-top": ["gothic-scifi-ruin-terrain4print-NC/corner-1-top.stl"],
    "ruin-c2-bottom": ["gothic-scifi-ruin-terrain4print-NC/corner-2-bottom-C.stl"],
    "cathedral-structure": ["gothic-cathedral-structure/Gothic Cathedral Structure - 4302749/files/estructura_simplificada_catedral_gotica_7.stl"],
    "wall-rose": ["gothic-building-components/Gothic Building Components - 6011872 - part 1 of 2/files/Wall_Rose.stl"],
    "qtr-front": ["gothic-building-components/Gothic Building Components - 6011872 - part 1 of 2/files/" + f
                  for f in ("qtr_front1_top.stl", "qtr_front1_bot.stl")],
    "gothic-window": ["gothic-building-components/Gothic Building Components - 6011872 - part 1 of 2/files/Gothic_Window.stl"],
    "univac": ["mainframe-univac/UNIVAC Mainframe Computer - 5448349/files/computer2.stl"],
}


def load(files):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for f in files:
        p = os.path.join(M, f)
        if p.endswith(".stl"):
            bpy.ops.wm.stl_import(filepath=p)
        else:
            bpy.ops.import_scene.gltf(filepath=p)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    grey = bpy.data.materials.new("grey")
    grey.use_nodes = True
    grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.35, 0.37, 1)
    for o in meshes:
        if not o.data.materials:
            o.data.materials.append(grey)
    return meshes


def bounds(meshes):
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def shoot(name, meshes):
    lo, hi = bounds(meshes)
    c, d = (lo + hi) / 2, hi - lo
    faces = sum(len(o.data.polygons) for o in meshes)
    print(f"MODEL {name}: dims x {d.x:.2f} y {d.y:.2f} z {d.z:.2f}, faces {faces}", flush=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = 24
    s.cycles.use_denoising = True
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for dv in pr.devices:
        dv.use = dv.type == "CUDA"
    s.render.resolution_x = s.render.resolution_y = 360
    s.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w")
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.37, 0.42, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 3.0
    so = bpy.data.objects.new("sun", sun)
    so.rotation_euler = (math.radians(50), 0, math.radians(-35))
    s.collection.objects.link(so)
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.clip_end = 1e5
    cam = bpy.data.objects.new("cam", cd)
    s.collection.objects.link(cam)
    s.camera = cam
    R = d.length * 2
    for view, direction in (("front", Vector((0, -1, 0))), ("side", Vector((1, 0, 0))), ("top", Vector((0, 0, 1)))):
        cam.location = c + direction * R
        up = "Y" if view == "top" else "Z"
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y" if view == "top" else "Y").to_euler()
        cd.ortho_scale = max(d) * 1.15
        s.render.filepath = os.path.join(OUT, f"{name}-{view}.png")
        bpy.ops.render.render(write_still=True)


names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(SETS)
for n in names:
    shoot(n, load(SETS[n]))
