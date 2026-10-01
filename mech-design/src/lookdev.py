"""Look-development stills: each chassis painted, standing, in a neutral studio.

Run:
    blender -b -P src/lookdev.py [-- madcat atlas battlemaster]

Writes wip/preview/lookdev/<chassis>-<view>.png. These are for judging the paint
and the glass before anything is animated, so the light is even and the
background plain.
"""

import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
import paint as P
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "wip", "preview", "lookdev")

# name, azimuth from the front (deg, +x side positive), elevation (deg)
VIEWS = [("front34", 32, 7), ("front", 0, 4), ("side", 90, 4), ("rear34", 145, 12)]

# cockpit close-up target (x, y, z) in model units
HEAD = {"madcat": (0.0, 2.2, 9.4), "atlas": (0.0, 0.9, 12.15), "battlemaster": (0.0, 0.3, 10.4)}


def look(cam, target, az, el, dist):
    t = Vector(target)
    a, e = math.radians(az), math.radians(el)
    cam.location = t + dist * Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()


def area(name, loc, target, energy, size, colour=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA")
    l.energy, l.size, l.color = energy, size, colour
    o = bpy.data.objects.new(name, l)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(o)


def studio(H):
    bpy.ops.mesh.primitive_plane_add(size=400)
    floor = bpy.context.object
    m = bpy.data.materials.new("floor")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.052, 0.058, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
    floor.data.materials.append(m)

    # a sky that brightens towards the top gives the glass and metal something
    # to reflect; a flat colour reflects as nothing
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0.010, 0.011, 0.014, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.30, 0.33, 0.38, 1)
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    L.new(mr.outputs["Result"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], N["Background"].inputs["Color"])

    c = (0, 0, H * 0.55)
    area("key", (-16, 22, 20), c, 16000, 12, (1.0, 0.94, 0.86))
    area("fill", (20, 18, 6), c, 5000, 16, (0.85, 0.90, 1.0))
    area("rim", (14, -18, 16), c, 14000, 10, (0.80, 0.88, 1.0))
    area("top", (0, 0, 30), c, 5000, 20)


def render_setup(samples):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for d in pr.devices:
        d.use = d.type == "CUDA"
    s.render.resolution_x, s.render.resolution_y = 800, 1000
    s.view_settings.view_transform = "AgX"
    for look_name in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):
        try:
            s.view_settings.look = look_name
            break
        except TypeError:
            continue


def main(names):
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        cfg = R.CHASSIS[name]
        R.clear_scene()
        mech = R.load(name)
        mech.name = name
        P.paint(mech, name)
        bpy.context.view_layer.objects.active = mech
        mech.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(31))

        H = cfg["height"]
        studio(H)
        render_setup(96)
        cd = bpy.data.cameras.new("cam")
        cam = bpy.data.objects.new("cam", cd)
        bpy.context.collection.objects.link(cam)
        bpy.context.scene.camera = cam

        cd.lens = 70
        for view, az, el in VIEWS:
            look(cam, (0, 0, H * 0.5), az, el, H * 2.45)
            bpy.context.scene.render.filepath = os.path.join(OUT, f"{name}-{view}.png")
            bpy.ops.render.render(write_still=True)
            print("LOOKDEV", name, view, flush=True)

        cd.lens = 90
        look(cam, HEAD[name], 24, 6, 7.5)
        bpy.context.scene.render.filepath = os.path.join(OUT, f"{name}-head.png")
        bpy.ops.render.render(write_still=True)
        print("LOOKDEV", name, "head", flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv or list(P.SCHEMES))
