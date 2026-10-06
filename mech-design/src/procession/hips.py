"""Hips that rock in the walk: a trial on top of the rig of src/rig.py,
switched by frame.HIP_ROCK. With HIP_ROCK = 0 nothing here runs and the rig
is that of banner 03. Blender 4.5.

src/rig.py has one bone, `body`, for everything above the legs. `split`
adds a bone `hips` under it, at the midpoint of the two hip joints and
pointing forward, hangs the thighs and the knee poles on it, and moves the
weight of the pelvis from `body` to it. The pelvis is what `body` holds
below the waist and between the outer edges of the legs; arms that hang
beside it stay with `body`. The mesh is not cut: across the waist the
weight passes from one bone to the other over 2 * BAND of height.

`rock` turns `hips` about the forward axis, once per gait cycle: the hip of
the swinging leg rises and the hip of the standing leg sinks. It also turns
`hips` about the upright axis, so that the side of the leading leg goes
forward: the pelvis of a walker does that, and it lengthens the step. The
foot controllers hang on the root, so the feet stay where the walk puts them.

WAIST is the height at which the torso begins, read off each chassis's
cross-sections: the Mad Cat's narrow stem under its pod, the Atlas's narrow
section over its hip skirt, the underside of the BattleMaster's torso. A
model of separate rigid parts names its pelvis itself (the `pelvis` entry of
its chassis in src/mechrig.py): the Marauder's lower torso.

    blender -b -P src/procession/hips.py -- <chassis>     # wip/preview/procession/hips-<chassis>.png: who holds what
"""
import bpy, os, sys, math
import numpy as np
from mathutils import Vector, Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F

R = F.mechwalk
WAIST = {"madcat": 7.5, "atlas": 7.9, "battlemaster": 7.5}
BAND = 0.3                         # half the height over which the weight passes from hips to body
EDGE = 0.3                         # the same, sideways, at the outer edge of the legs


def split(mesh, rig, name):
    """Add the bone `hips` to `rig` and give it the pelvis of `mesh`."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    hips = eb.new("hips")
    hips.head, hips.tail, hips.parent = eb["body"].head, eb["body"].head + Vector((0, 1.0, 0)), eb["body"]
    for s in "LR":
        eb[f"thigh.{s}"].parent = eb[f"pole.{s}"].parent = hips
    bpy.ops.object.mode_set(mode="OBJECT")

    n = len(mesh.data.vertices)
    co = np.empty(n * 3)
    mesh.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    ed = np.empty(len(mesh.data.edges) * 2, dtype=np.int64)
    mesh.data.edges.foreach_get("vertices", ed)
    body = mesh.vertex_groups["body"]
    w = np.zeros(n)
    for v in mesh.data.vertices:
        for g in v.groups:
            if g.group == body.index:
                w[v.index] = g.weight
    pelvis = F.mechrig.CHASSIS[name].get("pelvis")
    if pelvis:
        share = pelvis(mesh, co)
    else:
        x_out = R.JOINTS[name]["corridor"][1]
        ax, z = np.abs(co[:, 0]), co[:, 2]
        share = R._smooth((WAIST[name] + BAND - z) / (2 * BAND)) * R._smooth((x_out + EDGE - ax) / (2 * EDGE))
        # a separate piece that lies wholly beyond the legs' outer edge is an arm
        piece = R._components(ed.reshape(-1, 2), np.ones(n, bool))
        inner = np.full(n, np.inf)
        np.minimum.at(inner, piece, ax)
        share[inner[piece] > x_out - EDGE] = 0.0
    q = np.round(w * share, 2)
    hg = mesh.vertex_groups.new(name="hips")
    for val in np.unique(q[q > 0.005]):
        hg.add(np.nonzero(q == val)[0].tolist(), float(val), "REPLACE")
    left = np.round(w - q, 2)
    for val in np.unique(left[q > 0.005]):
        body.add(np.nonzero((left == val) & (q > 0.005))[0].tolist(), float(val), "REPLACE")
    print(f"HIPS {name}: {int((q > 0.5).sum())} vertices with the hips, {int((left > 0.5).sum())} with the body")


def rock(rig, name, phase, degrees, turn=0.0):
    """Turn the hips for gait phase `phase`. The left foot stands at phase
    0.3 and the right leg swings: there the right hip is highest. The left
    foot lands in front at phase 0: there the left side of the pelvis is
    `turn` degrees forward."""
    pb = rig.pose.bones["hips"]
    pb.rotation_mode = "XYZ"                               # the bone points forward: its y is the forward axis, its z the upright one
    pb.rotation_euler = Euler((0.0, -math.radians(degrees) * math.cos(math.tau * (phase - 0.3)), -math.radians(turn) * math.cos(math.tau * phase)))


if __name__ == "__main__":
    name = sys.argv[sys.argv.index("--") + 1]
    F.mechrig.clear_scene()
    mesh = F.mechrig.load(name)
    rig = R.build(mesh, name)
    split(mesh, rig, name)
    # every face in the colour of the bone that holds most of it; hips red, body grey
    tint = {"hips": (0.9, 0.1, 0.1), "body": (0.5, 0.5, 0.5), "thigh": (0.1, 0.3, 0.9), "shin": (0.1, 0.7, 0.3), "foot": (0.9, 0.7, 0.1)}
    names = [g.name for g in mesh.vertex_groups]
    top = np.array([max(v.groups, key=lambda g: g.weight).group for v in mesh.data.vertices])
    mats = {}
    for k, c in tint.items():
        m = bpy.data.materials.new(k)
        m.diffuse_color = (*c, 1)
        mesh.data.materials.append(m)
        mats[k] = len(mats)
    slot = np.array([mats[names[g].split(".")[0]] for g in top])
    first = np.empty(len(mesh.data.polygons), np.int64)
    mesh.data.polygons.foreach_get("loop_start", first)
    lv = np.empty(len(mesh.data.loops), np.int64)
    mesh.data.loops.foreach_get("vertex_index", lv)
    mesh.data.polygons.foreach_set("material_index", slot[lv[first]])
    rock(rig, name, 0.3, 8.0)                          # exaggerated, to show the hinge
    s = bpy.context.scene
    s.render.engine = "BLENDER_WORKBENCH"
    s.display.shading.color_type = "MATERIAL"
    s.render.resolution_x, s.render.resolution_y = 900, 1100
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type, cam.data.ortho_scale = "ORTHO", 15.0
    bpy.context.collection.objects.link(cam)
    s.camera = cam
    top_z = F.mechrig.CHASSIS[name]["height"]
    for view, loc, rot in (("front", (0, 40, top_z / 2), (90, 0, 180)), ("side", (40, 0, top_z / 2), (90, 0, 90))):
        cam.location, cam.rotation_euler = loc, Euler([math.radians(a) for a in rot], "XYZ")
        F.render(os.path.join(F.PREVIEW, f"hips-{name}-{view}.png"))
    print("HIPS_DONE")
