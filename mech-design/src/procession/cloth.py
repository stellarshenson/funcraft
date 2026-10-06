"""Cloth banners that hang between the legs of a mech, on a brass rod under
its pelvis, and move a little with the wind of its walk and with its gait.
Blender 4.5.

CLOTHS lists the chassis that have one. The Marauder's is crimson velvet
with gold embroidery: resources/assets/cloth-banner.png and its gold thread
in cloth-banner_gold.png (banner_4 of w40k-mechanicum, cut out of its white
margin). The Mad Cat's is red velvet embroidered with bone thread, with a
forked lower end: cloth-madcat.png and its thread in cloth-madcat_silk.png,
which src/procession/clothart.py paints. A golden tassel hangs on a cord
from each of its two lower corners. Its rod hangs under the lowest part of the pelvis,
between the thighs: a first place 3 m further forward, under the nose, left
it in front of the mech.

A cloth is a grid of its own, not part of the mech's mesh. `shape` gives the
place of every point of the grid: the cloth does not stretch, so the place
follows from the angle that the cloth has to the vertical at every point
down its length. That angle is the sum of three parts:

    lean     the wind of the walk lays the lower end back, by LEAN degrees
    swing    every step of the mech swings it, by SWING degrees, and the
             swing runs down the cloth as a wave: two per gait cycle
    ripple   the wind sends RIPPLES waves per loop down and across it, of
             RIPPLE degrees

and the lower end goes SIDE metres to each side once per gait cycle, with
the hips. A tassel hangs at the angle that the cloth would have a little
further down, LAG of a gait cycle later. Every part is a function of the
gait phase or of the place in the loop, so frame FRAMES shows what frame 0
shows.

`hang` builds the cloth of a rigged mech, binds it and its rod to the bone
of the pelvis and adds its motion to the scene's movers. `build` alone
gives the cloth at rest, for a still.

    blender -b -P src/procession/scene.py -- ... cloth=1                 # the scene with the cloths
    blender -b -P src/procession/livery.py -- <chassis> full cloth       # a still with the cloth
"""
import bpy, bmesh, os, sys, math
import numpy as np
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F

GOLD = (0.95, 0.66, 0.24)
# at: the middle of the cloth's upper edge on the mech at rest; width; picture: a file stem in resources/assets, whose
# shape gives the length; thread: what the embroidery is made of, which names its mask <picture>_<thread>.png (gold
# is metal, silk is not); tassels: a golden tassel hangs from each lower corner
CLOTHS = {
    "marauder": dict(at=(0.0, 1.66, 5.92), width=1.3, picture="cloth-banner", thread="gold"),
    "madcat": dict(at=(0.0, -0.6, 6.0), width=1.0, picture="cloth-madcat", thread="silk", tassels=True),
}
NX, NZ = 24, 64                    # the grid: quads across and down
LEAN, SWING, RIPPLE = 7.0, 3.0, 2.0    # degrees, see above
RIPPLES = 3
SIDE = 0.04
CORD = 0.10                        # metres of cord over a tassel
LAG = 0.04
_TASSEL = []


def _length(spec):
    w, h = bpy.data.images.load(os.path.join(F.ROOT, "resources", "assets", spec["picture"] + ".png"), check_existing=True).size
    return spec["width"] * h / w


def _angle(t, u, phase, loop):
    """Radians that the cloth has to the vertical at the share `t` down its length and `u` across it."""
    return (math.radians(LEAN) * t ** 0.7
            + math.radians(SWING) * t ** 0.5 * np.sin(math.tau * (2.0 * phase - 0.35 * t))
            + math.radians(RIPPLE) * t * np.sin(math.tau * (RIPPLES * loop - 1.5 * t + 0.4 * u)))


def shape(spec, phase=0.0, loop=0.0):
    """The points of the cloth's grid, row by row from the rod down, for the
    gait phase `phase` and the place `loop` in the loop (both 0..1)."""
    x0, y0, z0 = spec["at"]
    u = np.linspace(0.0, 1.0, NX + 1)[None, :]             # across, from the viewer's left
    t = np.linspace(0.0, 1.0, NZ + 1)[:, None]             # down the cloth
    step = _length(spec) / NZ
    angle = _angle(t, u, phase, loop)
    back = np.cumsum(np.sin(angle) * step, axis=0) - np.sin(angle) * step      # the sum over the rows above
    down = np.cumsum(np.cos(angle) * step, axis=0) - np.cos(angle) * step
    fold = (0.03 + 0.10 * t) * np.sin(3.0 * math.pi * u)   # folds that run down the cloth and deepen towards its lower edge
    x = x0 + spec["width"] * (0.5 - u) + SIDE * t ** 1.5 * math.sin(math.tau * (phase - 0.4))     # +x is on the viewer's left
    return np.stack([x, y0 + fold - back, z0 - down], axis=-1).reshape(-1, 3)


def _tassel():
    """A tassel that hangs from the origin on CORD metres of cord, with a
    round head, a band round its neck and a skirt of threads: its points and
    its faces."""
    if not _TASSEL:
        bm = bmesh.new()
        T = Matrix.Translation
        bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=0.012, radius2=0.012, depth=CORD, matrix=T((0, 0, -CORD / 2)))
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.055, matrix=T((0, 0, -CORD - 0.05)))
        bmesh.ops.create_cone(bm, cap_ends=False, segments=12, radius1=0.043, radius2=0.043, depth=0.035, matrix=T((0, 0, -CORD - 0.115)))
        skirt = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.078, radius2=0.040, depth=0.30, matrix=T((0, 0, -CORD - 0.28)))["verts"]
        for v in skirt:                                    # every second thread of the skirt lies deeper
            if round(math.atan2(v.co.y, v.co.x) / (math.tau / 24)) % 2:
                v.co.x, v.co.y = 0.80 * v.co.x, 0.80 * v.co.y
        bm.verts.index_update()
        _TASSEL[:] = np.array([v.co for v in bm.verts]), [[v.index for v in f.verts] for f in bm.faces]
        bm.free()
    return _TASSEL


def points(spec, phase=0.0, loop=0.0):
    """Every point of the cloth's mesh: the grid of `shape`, then the points
    of the tassel at each lower corner."""
    grid = shape(spec, phase, loop)
    if not spec.get("tassels"):
        return grid
    out, p = [grid], _tassel()[0]
    for u in (0.0, 1.0):
        a = float(_angle(1.12, u, phase - LAG, loop))      # the angle of the cloth a little further down than it reaches
        hung = np.stack([p[:, 0], p[:, 1] * math.cos(a) + p[:, 2] * math.sin(a), -p[:, 1] * math.sin(a) + p[:, 2] * math.cos(a)], axis=-1)
        out.append(grid[NZ * (NX + 1) + round(u * NX)] + hung)
    return np.concatenate(out)


def _velvet(m, colour, alpha, thread, metal):
    """Make `m` velvet of the colour socket `colour`: it takes the light and
    shines only where the socket `thread` says there is embroidery, which
    stands over the pile; `metal`: the thread is gold."""
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    L.new(colour, b.inputs["Base Color"])
    L.new(alpha, b.inputs["Alpha"])
    b.inputs["Sheen Weight"].default_value = 0.5
    b.inputs["Sheen Tint"].default_value = (0.6, 0.05, 0.04, 1)
    rough = N.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = 1.0, 0.35 if metal else 0.5
    L.new(thread, rough.inputs["Value"])
    L.new(rough.outputs["Result"], b.inputs["Roughness"])
    if metal:
        L.new(thread, b.inputs["Metallic"])
    L.new(thread, b.inputs["Specular IOR Level"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.6, 0.01
    L.new(thread, bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])


def _material(name, spec):
    m = bpy.data.materials.new(f"{name}_cloth")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    at = N.new("ShaderNodeUVMap")
    at.uv_map = "uv"
    A = os.path.join(F.ROOT, "resources", "assets")
    tex, thread = N.new("ShaderNodeTexImage"), N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(A, spec["picture"] + ".png"), check_existing=True)
    thread.image = bpy.data.images.load(os.path.join(A, f"{spec['picture']}_{spec['thread']}.png"), check_existing=True)
    thread.image.colorspace_settings.name = "Non-Color"
    tex.extension = thread.extension = "CLIP"
    for t in (tex, thread):
        L.new(at.outputs["UV"], t.inputs["Vector"])
    _velvet(m, tex.outputs["Color"], tex.outputs["Alpha"], thread.outputs["Color"], spec["thread"] == "gold")
    return m


def _metal(name, colour, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value, b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = (*colour, 1), 1.0, rough
    return m


def build(name):
    """The cloth of chassis `name` at rest and its rod, as two objects of the
    scene, where a mech at the origin has them."""
    spec = CLOTHS[name]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("uv")
    verts = [bm.verts.new(p) for p in points(spec)]
    for k in range(NZ):
        for i in range(NX):
            corners = ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))
            f = bm.faces.new([verts[a * (NX + 1) + b] for a, b in corners])
            for loop, (a, b) in zip(f.loops, corners):
                loop[uv].uv = (b / NX, 1.0 - a / NZ)
            f.smooth = True
    first = (NX + 1) * (NZ + 1)
    for _ in range(2 if spec.get("tassels") else 0):
        p, faces = _tassel()
        for face in faces:
            f = bm.faces.new([verts[first + i] for i in face])
            f.material_index, f.smooth = 1, True
        first += len(p)
    me = bpy.data.meshes.new(f"{name}_cloth")
    bm.to_mesh(me)
    bm.free()
    for m in (_material(name, spec), _metal(f"{name}_tassel", GOLD, 0.45)):
        me.materials.append(m)
    cloth = bpy.data.objects.new(f"{name}_cloth", me)

    x0, y0, z0 = spec["at"]
    w = spec["width"]
    bm = bmesh.new()
    T = Matrix.Translation
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.04, radius2=0.04, depth=w + 0.24,
                          matrix=T((x0, y0 + 0.02, z0 - 0.03)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    for side in (-1, 1):
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.075, matrix=T((x0 + side * (w / 2 + 0.14), y0 + 0.02, z0 - 0.03)))
        # a strap from the rod up into the pelvis
        bmesh.ops.create_cube(bm, size=1.0, matrix=T((x0 + side * 0.4 * w, y0 - 0.02, z0 + 0.08)) @ Matrix.Diagonal((0.08, 0.05, 0.3, 1.0)))
    me = bpy.data.meshes.new(f"{name}_rod")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(_metal(f"{name}_rod", (0.6, 0.42, 0.16), 0.3))
    rod = bpy.data.objects.new(f"{name}_rod", me)
    for ob in (cloth, rod):
        bpy.context.collection.objects.link(ob)
    return cloth, rod


def hang(scene, rig, name, offset):
    """Give the mech of `rig`, which stands at the origin and at rest, its
    cloth, and add the cloth's motion to the movers of `scene`. `offset`:
    the frames the mech walks ahead."""
    cloth, rod = build(name)
    for ob in (cloth, rod):
        F.bone_child(ob, rig, "hips" if F.HIP_ROCK else "body")
    spec = CLOTHS[name]

    def sway(i):
        phase = ((i + offset) % F.GAIT_FRAMES) / F.GAIT_FRAMES
        cloth.data.vertices.foreach_set("co", points(spec, phase, i / F.FRAMES).ravel())
        cloth.data.update()

    scene.movers.append(sway)
