"""Load the downloaded models into the scene: import, join into one object,
turn to face +Y, scale to a height, and put the origin at the bottom centre.

Every model here faces -Y as downloaded unless its entry says otherwise, so
`turn` is the extra rotation (degrees about X, Y, Z) that makes it face +Y
(towards the camera). Loaded meshes are cached, so repeated props are linked
copies that share one mesh.
"""
import bpy, math, os
import numpy as np
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "in", "models", "originals")

# name: (files, turn in degrees (x, y, z)[, importer options])
SOURCES = {
    "priest": (["tech-priest-techno-gothic/techno-gothic-priest-stl.stl"], (0, 0, 180)),
    "datasmith": (["tech-priest-info-artisan/Martian Info-Artisan - 3591216/files/Datasmith.stl"], (0, 0, 180)),
    "hooded": (["tech-priest-statue/Tech Priest statue - 4786550/files/statue_Ad_Mech.stl"], (0, 0, 180)),
    "servo_skull": (["servo-skull-plasmastorm-NC/Servo_Skull_Cables.stl"], (0, 0, 180)),
    "skull": (["servo-skull-base-human-skull-cc0/skull_w_jaw.stl"], (0, 0, 180)),
    "fan": (["gpu-rtx3060-3070-fans/Geforce RTX 3060 & 3070 - 4889698/files/Right_Fan.stl"], (-90, 0, 0)),
    "thurible": (["censer-thurible/Thurible_Censer Prop with Insert for Mini Smoke Machine - 7318933/files/Thurible__Base.stl",
                  "censer-thurible/Thurible_Censer Prop with Insert for Mini Smoke Machine - 7318933/files/Thurible__Lid.stl"], (0, 0, 0)),
    "candelabra": (["candles-brass-candleholders/brass_candleholders_2k_gltf/brass_candleholders_2k.gltf"], (0, 0, 0)),
    "statue": (["gothic-statue-polyhaven/gothic_statue_2k_gltf/gothic_statue_2k.gltf"], (0, 0, 180)),
    # upside down as downloaded (teeth at the top): half a turn about Y
    "medallion": (["ornament-mechanicus-symbol/TP_Symbol_-_all.stl"], (0, 180, 0)),
    "lancet": (["gothic-window-stained-glass/Gothic Window - 815120/files/Stained_Glass.stl"], (0, 0, 180)),
    "wall_a": (["gothic-scifi-ruin-terrain4print-NC/corner-1-bottom-A.stl"], (0, 0, 180)),
    "wall_b": (["gothic-scifi-ruin-terrain4print-NC/corner-2-bottom-C.stl"], (0, 0, 180)),
    # version 2: Mechanicus priests, servitors, the praying congregation, decor
    "magus": (["tech-priest-magus-wholan-NC/Admech_Magus_1.stl"], (0, 0, 180)),
    "shock_priest": (["tech-priest-shock-priest-NC/shock-priests-unsupported-shock-priest-3.stl"], (0, 0, 180)),
    "dominus": (["tech-priest-dominus-mangaratiba-NC/DOMINUS_FIX_fix.stl"], (0, 0, 180)),
    "magos": (["tech-priest-female-magos-NC/Female_Magos_Whole.stl"], (0, 0, 180)),
    "servitor": (["servitor-johnthemaker/servitor.stl"], (0, 0, 90)),
    "servitor_rack": (["servitor-storage-recharging-NC/Completetesthang.stl"], (0, 0, 90)),
    "kneel_monk": (["praying-monk-kneeling-treezii/praying-monk.obj"], (0, 0, 90), {"up_axis": "Z", "forward_axis": "Y"}),
    "kneel_cloak": (["praying-kneeling-figure-josepedro-NC/madonna-v2.stl"], (0, 0, -90)),
    "kneel_saint": (["praying-kneeling-saint-NC/Praying_saint_ver_4.stl"], (0, 0, 180)),
    "kneel_hooded": (["praying-kneeling-cult-bodyguard/LOCUS_PRAYING.stl"], (0, 0, 180)),
    "pray_cultist": (["praying-cultist-yasashii-NC/Cultist_04_54mm.stl"], (0, 0, 180)),
    "pray_hooded": (["praying-standing-hooded-jesus-may3d-NC/jesus-in-prayer_1778879932_generate.stl"], (0, 0, 180)),
    "statue_young": (["statue-priests-terrain4print-NC/statue-young-priest-rough.stl"], (0, 0, 180)),
    "statue_old": (["statue-priests-terrain4print-NC/statue-old-priest-rough.stl"], (0, 0, 180)),
    "statue_dark": (["statue-priests-terrain4print-NC/statue-dark-priest-rough.stl"], (0, 0, 180)),
    "statue_skeleton": (["statue-priests-terrain4print-NC/statue-skeleton-priest-rough.stl"], (0, 0, 180)),
    "cherub_brazier": (["decor-cherub-brazier-helforged/Cherub_and_Brazier_Final.stl"], (0, 0, 180)),
    "banner_cherubs": (["decor-banner-cherubs-NC/banner_cherubs.stl"], (0, 0, 180)),
    "guardians": (["decor-guardians-of-omnissiah-NC/guardiansofomnissiah1.stl"], (0, 0, 180)),
    "reliquary": (["decor-gothic-reliquary/gothic-reliquary.stl"], (90, 0, 0)),
}

_cache = {}


def _import(path, opts=None):
    before = set(bpy.data.objects)
    low = path.lower()
    if low.endswith(".stl"):
        bpy.ops.wm.stl_import(filepath=path)
    elif low.endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=path, **(opts or {}))
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def _join(objs, name):
    meshes = [o for o in objs if o.type == "MESH"]
    for o in meshes:                                  # bake parent transforms in
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    for o in objs:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.name = name
    return ob


def _co(ob):
    n = len(ob.data.vertices)
    a = np.empty(n * 3)
    ob.data.vertices.foreach_get("co", a)
    return a.reshape(n, 3)


def load(name, height, stack=False):
    """A new object showing model `name`, `height` units tall, facing +Y,
    origin at the bottom centre. `stack` puts each file on top of the one
    before (a lid on its bowl)."""
    key = (name, height)
    if key in _cache:
        ob = _cache[key].copy()                       # linked: shares the mesh
        bpy.context.collection.objects.link(ob)
        return ob
    files, turn, *rest = SOURCES[name]
    parts = []
    for f in files:
        p = _join(_import(os.path.join(M, f), rest[0] if rest else None), name)
        if stack and parts:
            a, b = _co(parts[-1]), _co(p)
            shift = (a[:, 0].mean() - b[:, 0].mean(), a[:, 1].mean() - b[:, 1].mean(),
                     a[:, 2].max() - b[:, 2].min() - 0.02 * np.ptp(b[:, 2]))
            p.data.transform(Matrix.Translation(shift))
        parts.append(p)
    ob = _join(parts, name) if len(parts) > 1 else parts[0]
    rx, ry, rz = (math.radians(a) for a in turn)
    ob.data.transform(Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X"))
    c = _co(ob)
    lo, hi = c.min(0), c.max(0)
    s = height / (hi[2] - lo[2])
    ob.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
    ob.data.update()
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    _cache[key] = ob
    return ob


def dims(ob):
    return Vector(np.ptp(_co(ob), axis=0))
