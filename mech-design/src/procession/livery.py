"""The livery of the procession's mechs: the ornament atlas of
src/procession/ornament.py on the armour plates, as colour, metal, roughness
and relief, under the wear of src/paint.py. Blender 4.5.

`paint(mesh, name)` takes the place of paint.py's paint: it charts the
plates (src/procession/plating.py), and gives every face one of these
materials:

    armour      a charted plate: reads the atlas through the UV layer `plate`
    <class>     armour too small for a chart: the plain enamel of its colour class
    machine     machinery and the frame round the glass, as paint.py
    glass       as paint.py

The armour material is paint.py's surface (dirt in the creases, bare metal
on worn edges, rounded edges) with the atlas in place of its one colour and
the atlas's height as relief.

    blender -b -P src/procession/scene.py -- livery=livery ...       # the scene with this livery
    blender -b -P src/procession/livery.py -- <chassis> [full|close] # wip/preview/procession/livery-<chassis>-<view>.png
    blender -b -P src/procession/livery.py -- <chassis> full cloth   # with its cloth banner (src/procession/cloth.py): livery-<chassis>-full-cloth.png
"""
import bpy, os, sys, json, math, random
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F
import plating

P = F.mechpaint
LIVERY = os.path.join(F.WIP, "livery")


def armour(name, relief):
    """paint.py's surface with the atlas of `name` wired in."""
    m = P._surface(f"{name}_armour", (1, 1, 1), 0.5, 0.0, 0.55)
    N, L = m.node_tree.nodes, m.node_tree.links
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "plate"

    def tex(kind, data, interpolation="Linear"):
        t = N.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(LIVERY, f"{name}_{kind}.png"))
        if data:
            t.image.colorspace_settings.name = "Non-Color"
        t.interpolation, t.extension = interpolation, "EXTEND"
        L.new(uv.outputs["UV"], t.inputs["Vector"])
        return t.outputs["Color"]

    def node(kind, operation):
        return next(n for n in N if n.type == kind and n.operation == operation)

    L.new(tex("colour", False), node("VECT_MATH", "SCALE").inputs[0])
    sep = N.new("ShaderNodeSeparateColor")
    L.new(tex("surface", True), sep.inputs["Color"])
    L.new(sep.outputs["Red"], node("MATH", "MAXIMUM").inputs[0])
    L.new(sep.outputs["Green"], node("MATH", "MULTIPLY_ADD").inputs[2])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = relief
    L.new(tex("height", True, "Cubic"), bump.inputs["Height"])
    L.new(next(n for n in N if n.type == "BEVEL").outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], N["Principled BSDF"].inputs["Normal"])
    return m


def paint(mesh, name):
    info = plating.chart(mesh, name)
    meta = json.load(open(os.path.join(LIVERY, f"{name}.json")))
    mats = {"armour": armour(name, meta["relief"])}
    for k, c in meta["enamel"].items():
        mats[k] = P._surface(f"{name}_{k}", c, 0.52, 0.0, 0.55)
    mats["machine"] = P._surface(f"{name}_machine", P.GUNMETAL, 0.36, 0.9, 0.0)
    mats["glass"] = P._glass(f"{name}_glass", P.SCHEMES[name]["glass"]["glow"])
    slot = {k: i for i, k in enumerate(mats)}
    mesh.data.materials.clear()
    for m in mats.values():
        mesh.data.materials.append(m)
    index = np.full(len(mesh.data.polygons), slot["machine"], np.int32)
    index[info["charted"]] = slot["armour"]
    index[info["glass"]] = slot["glass"]
    for f, k in info["plain"].items():
        index[f] = slot[k]
    mesh.data.polygons.foreach_set("material_index", index)
    # paint.py's tone of each patch; a charted plate has its tone in the atlas
    rng, tone, charted = random.Random(name), {}, set(info["charted"])
    panel = mesh.data.attributes.new("panel", "FLOAT", "FACE")
    panel.data.foreach_set("value", [1.0 if f in charted else tone.setdefault(p, rng.uniform(0.90, 1.08))
                                     for f, p in enumerate(info["patch"])])
    mesh.data.update()


if __name__ == "__main__":
    import scene as S
    argv = sys.argv[sys.argv.index("--") + 1:]
    name, view = argv[0], argv[1] if len(argv) > 1 else "full"
    F.mechrig.clear_scene()
    mesh = F.painted(name, paint)
    if "cloth" in argv:
        import cloth
        cloth.build(name)
    bpy.ops.mesh.primitive_plane_add(size=400)
    floor = bpy.data.materials.new("floor")
    floor.diffuse_color = (0.05, 0.05, 0.05, 1)
    bpy.context.object.data.materials.append(floor)
    S.lights((0.55, 0.50, 0.45))
    top = F.mechrig.CHASSIS[name]["height"]
    eye, aim, lens, res = dict(full=((5.0, 40.0, 8.6), (0.0, 0.0, 0.5 * top), 62.0, (1100, 1400)),
                               close=((2.5, 14.0, 0.80 * top), (0.3, 0.0, 0.74 * top), 50.0, (1500, 1000)),
                               joints=((5.5, 15.0, 0.66 * top), (0.2, 0.0, 0.62 * top), 40.0, (1500, 1100)),      # shoulders and hips
                               hang=((1.6, 10.0, 0.40 * top), (0.0, -0.6, 0.36 * top), 105.0, (900, 1400)))[view]  # the Mad Cat's cloth banner
    cam = F.camera()
    cam.data.lens = lens
    cam.location = eye
    cam.rotation_euler = (Vector(aim) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    F.render_setup(samples=48)
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = res
    F.render(os.path.join(F.PREVIEW, f"livery-{name}-{view}{'-cloth' if 'cloth' in argv else ''}.png"))
    print("LIVERY_DONE")
