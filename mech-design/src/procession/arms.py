"""Arms that swing a little in the walk, on top of the rig of src/rig.py, for
the chassis of frame.ARM_SWING. The Mad Cat is not among them: its weapon
pods are fixed mounts. Blender 4.5.

src/rig.py has one bone, `body`, for everything above the legs. `split`
adds the bones `arm.L` and `arm.R` under it, at the shoulder joints and
pointing sideways, and moves the weight of each arm from `body` to its bone.
The mesh is not cut at the shoulder. What is arm is read off views of each
chassis with a grid of half a metre (SHOULDER): the surface |x| = edge(z)
parts arm from torso, nothing below `floor` is arm, and a separate piece of
the mesh that lies wholly beyond `pieces` is arm whatever its height (the
Atlas's forearms). Across the parting surface the weight passes from one
bone to the other over 2 * BAND; that is close to the joint, where a swing
of a few degrees moves the surface by a few centimetres.

`swing` turns each arm about the sideways axis through its shoulder, once
per gait cycle and against the leg of its side: when the left foot lands in
front, the left arm is furthest back.

An arm with an `elbow` entry has a second bone, `forearm.<side>`, under its
arm bone: it turns about the elbow's hinge by its own angle, a little later
than the arm, as a hanging forearm does. The BattleMaster's lowered left arm
has one.

Where that hinge is, and what is forearm, is read off the model itself. The
BattleMaster's two arms are the same parts in two poses: mirrored in x, the
left arm lies on the right one after one rigid motion where it is upper arm
and after another where it is forearm (TWIN). The two motions differ by a
turn of 19.11 degrees about one line, with no slide along it: that line is
the hinge. A face is upper arm or forearm by the motion that lays its
vertices on vertices of the other arm; the faces that neither places (the
hand, which differs between the arms) take the part of the faces they are
joined to. Upper arm and forearm are two rigid bodies, so the mesh is cut
along the edges where their faces meet: no face stretches across the hinge.

In front of the hinge a piston runs from the upper arm to the forearm, a
separate piece of the mesh. It has the bone `piston.<side>`, which turns
about the piston's upper end so that it keeps pointing at the place on the
forearm where the rod ends; the end ring of the rod has the bone
`rod.<side>` under it and slides along the piston to stay at that place.
Between the model's two arms the piston differs in the same way: it is
0.25 m longer in the right arm, whose elbow is 19 degrees straighter.

    blender -b -P src/procession/arms.py -- <chassis>     # wip/preview/procession/arms-<chassis>-<view>.png: who holds what
"""
import bpy, bmesh, os, sys, math
import numpy as np
from mathutils import Vector, Euler, Matrix
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F

R = F.mechwalk
# pivot: the shoulder joint of the +x side (the other side is its mirror image); edge: (z, |x|) points of the surface
# that parts arm from torso, straight between them and level beyond them; floor: no arm below this height
SHOULDER = {
    "atlas": dict(pivot=(3.0, -1.1, 11.3), edge=((11.0, 3.15), (11.4, 2.65)), floor=9.3, pieces=3.2),
    # the left arm hangs beside the hips: below the torso the surface lies beyond the legs. Its elbow: side, a point
    # of the hinge and the hinge's direction, degrees the forearm swings to each side about it, the share of a gait
    # cycle by which it follows the arm, and the piston: the centres of its upper end and of the end ring of its rod
    "battlemaster": dict(pivot=(3.4, -1.5, 10.6), edge=((7.2, 3.0), (7.6, 2.6)), floor=4.5,
                         elbow=dict(side="L", pivot=(-3.6, -2.028, 7.222), axis=(0.9806, 0.0816, -0.1784), swing=12.0, lag=0.12,
                                    rod=dict(top=(-3.399, -1.273, 8.494), end=(-3.840, -1.376, 7.160)))),
    # separate parts: the arm block, the gun and its barrels are the pieces beyond 2.2; nothing else is arm
    "marauder": dict(pivot=(2.52, 0.43, 8.99), edge=((0.0, 99.0), (1.0, 99.0)), floor=0.0, pieces=2.2),
}
BAND = 0.1                         # half the width over which the weight passes from body to arm
# the two motions that lay the arm with the elbow, mirrored in x, on the other arm: rows of a 3 x 4 matrix, metres.
# Least-squares fits; 1705 vertices of the upper arm and 723 of the forearm then lie within 3 mm of a vertex there
TWIN = {"battlemaster": dict(
    upper=((0.96552, -0.20137, 0.16499, -1.62041), (0.24331, 0.47265, -0.84700, 6.57428), (0.09257, 0.85794, 0.50535, 5.80638)),
    fore=((0.97330, -0.19133, 0.12682, -1.35229), (0.22759, 0.73245, -0.64166, 5.67475), (0.02988, 0.65338, 0.75644, 3.80379)))}
NEAR = 0.005                       # a vertex lies on the other arm if it comes this close to one of its vertices
REACH = 0.3                        # the rod's end ring: the piston's vertices this close to its centre


def _shares(mesh, S):
    """What `split` reads off the mesh: the vertices, the separate piece of
    each, the weight w that `body` holds of each and the share q of it that
    goes to the arms."""
    n = len(mesh.data.vertices)
    co = np.empty(n * 3)
    mesh.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    body = mesh.vertex_groups["body"]
    w = np.zeros(n)
    for v in mesh.data.vertices:
        for g in v.groups:
            if g.group == body.index:
                w[v.index] = g.weight
    ax, z = np.abs(co[:, 0]), co[:, 2]
    zs, xs = zip(*S["edge"])
    share = R._smooth((ax - np.interp(z, zs, xs) + BAND) / (2 * BAND)) * R._smooth((z - S["floor"] + BAND) / (2 * BAND))
    ed = np.empty(len(mesh.data.edges) * 2, dtype=np.int64)
    mesh.data.edges.foreach_get("vertices", ed)
    piece = R._components(ed.reshape(-1, 2), np.ones(n, bool))
    if "pieces" in S:
        inner = np.full(n, np.inf)
        np.minimum.at(inner, piece, ax)
        share[inner[piece] > S["pieces"]] = 1.0
    return co, piece, w, np.round(w * share, 2)


def _cut(mesh, co, arm, name):
    """Cut the arm with the elbow (the vertex mask `arm`) into upper arm and
    forearm. Returns the mask of the forearm's vertices in the cut mesh. A
    separate piece that neither motion places stays with the upper arm."""
    other = np.nonzero(co[:, 0] * co[arm, 0].mean() < 0)[0]
    kd = KDTree(len(other))
    for k in other:
        kd.insert(co[k], k)
    kd.balance()
    idx = np.nonzero(arm)[0]
    part = np.zeros(len(co), int)                            # per vertex: 1 lies on the other arm as upper arm, 2 as forearm
    for p, key in ((1, "upper"), (2, "fore")):
        T = np.array(TWIN[name][key])
        moved = (co[idx] * (-1, 1, 1)) @ T[:, :3].T + T[:, 3]
        part[idx[[kd.find(v)[2] < NEAR for v in moved]]] = p
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    body = {}                                                # per face of the arm: 1, 2, or 0 while not known
    for f in bm.faces:
        if all(arm[v.index] for v in f.verts):
            marks = [part[v.index] for v in f.verts if part[v.index]]
            body[f] = max(marks, key=marks.count) if marks else 0
    grow = [f for f in body if body[f]]
    while grow:                                              # the rest: the part of the faces they are joined to
        reached = []
        for f in grow:
            for e in f.edges:
                for g in e.link_faces:
                    if body.get(g) == 0:
                        body[g] = body[f]
                        reached.append(g)
        grow = reached
    bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if {body.get(f) for f in e.link_faces} == {1, 2}])
    bm.verts.index_update()
    fore = np.zeros(len(bm.verts), bool)
    fore[[v.index for f in body if body[f] == 2 for v in f.verts]] = True
    both = sum(1 for v in bm.verts if {body.get(f) for f in v.link_faces} >= {1, 2})
    print(f"ELBOW {name}: {len(bm.verts) - len(co)} vertices added by the cut, {both} still shared by both parts")
    bm.to_mesh(mesh.data)
    bm.free()
    return fore


def split(mesh, rig, name):
    """Add the bones `arm.L` and `arm.R` to `rig` and give them the arms of `mesh`."""
    S = SHOULDER[name]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    for s, sign in (("L", -1.0), ("R", 1.0)):                # L is the -x side
        b = eb.new(f"arm.{s}")
        b.head = Vector((sign * S["pivot"][0], S["pivot"][1], S["pivot"][2]))
        b.tail, b.parent = b.head + Vector((1.0, 0, 0)), eb["body"]
    E = S.get("elbow")
    if E:
        s, top, end = E["side"], Vector(E["rod"]["top"]), Vector(E["rod"]["end"])
        for bone, head, along, parent in ((f"forearm.{s}", Vector(E["pivot"]), Vector(E["axis"]), f"arm.{s}"),
                                          (f"piston.{s}", top, end - top, f"arm.{s}"),
                                          (f"rod.{s}", end, (end - top).normalized(), f"piston.{s}")):
            b = eb.new(bone)
            b.head, b.tail, b.parent = head, head + along, eb[parent]
    bpy.ops.object.mode_set(mode="OBJECT")

    co, piece, w, q = _shares(mesh, S)
    if E:
        fore = _cut(mesh, co, (co[:, 0] < 0 if E["side"] == "L" else co[:, 0] >= 0) & (q > 0.005), name)
        co, piece, w, q = _shares(mesh, S)                   # the cut has added vertices
    body = mesh.vertex_groups["body"]
    for s, side in (("L", co[:, 0] < 0), ("R", co[:, 0] >= 0)):
        upper = q
        if E and E["side"] == s:                             # forearm and piston are rigid parts: all of q or none
            near = np.linalg.norm(co - E["rod"]["end"], axis=1) < REACH
            ids, count = np.unique(piece[side & near], return_counts=True)
            piston = piece == ids[count.argmax()]            # the separate piece whose end ring lies there
            fore &= ~piston
            upper = np.where(fore | piston, 0.0, q)
            for bone, mask in ((f"forearm.{s}", fore), (f"piston.{s}", piston & ~near), (f"rod.{s}", piston & near)):
                g = mesh.vertex_groups.new(name=bone)
                for val in np.unique(q[mask]):
                    g.add(np.nonzero(mask & (q == val))[0].tolist(), float(val), "REPLACE")
            print(f"ELBOW {name}: {int(fore.sum())} vertices with the forearm, {int(piston.sum())} with the piston, {int((piston & near).sum())} of them the rod's end")
        g = mesh.vertex_groups.new(name=f"arm.{s}")
        for val in np.unique(upper[side & (upper > 0.005)]):
            g.add(np.nonzero(side & (upper == val))[0].tolist(), float(val), "REPLACE")
    left = np.round(w - q, 2)
    for val in np.unique(left[q > 0.005]):
        body.add(np.nonzero((left == val) & (q > 0.005))[0].tolist(), float(val), "REPLACE")
    print(f"ARMS {name}: {int((q > 0.5).sum())} vertices with the arms, {int((left > 0.5).sum())} with the body")


def swing(rig, name, phase, degrees):
    """Turn the arms for gait phase `phase`. The left foot lands in front at
    phase 0: there the left arm is furthest back and the right arm furthest
    forward."""
    a = math.radians(degrees) * math.cos(math.tau * phase)
    for s, sign in (("L", -1.0), ("R", 1.0)):
        pb = rig.pose.bones[f"arm.{s}"]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = Euler((0.0, sign * a, 0.0))      # about the bone's own axis, which points along +X
    E = SHOULDER[name].get("elbow")
    if E:
        pb = rig.pose.bones[f"forearm.{E['side']}"]
        pb.rotation_mode = "XYZ"
        sign = -1.0 if E["side"] == "L" else 1.0
        turn = sign * math.radians(E["swing"]) * math.cos(math.tau * (phase - E["lag"]))
        pb.rotation_euler = Euler((0.0, turn, 0.0))          # about the hinge, along which the bone points
        # the piston points from its upper end at the place where the forearm carries the rod's end, and the rod's
        # end slides to that place
        top, end, hinge = Vector(E["rod"]["top"]), Vector(E["rod"]["end"]), Vector(E["pivot"])
        aim = hinge + Matrix.Rotation(turn, 3, Vector(E["axis"])) @ (end - hinge) - top
        pb = rig.pose.bones[f"piston.{E['side']}"]
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = Vector((0.0, 1.0, 0.0)).rotation_difference(rig.data.bones[pb.name].matrix_local.to_3x3().inverted() @ aim)
        rig.pose.bones[f"rod.{E['side']}"].location = (0.0, aim.length - (end - top).length, 0.0)


if __name__ == "__main__":
    name = sys.argv[sys.argv.index("--") + 1]
    F.mechrig.clear_scene()
    mesh = F.mechrig.load(name)
    rig = R.build(mesh, name)
    split(mesh, rig, name)
    # every face in the colour of the bone that holds most of it
    tint = {"arm": (0.9, 0.1, 0.1), "forearm": (0.9, 0.1, 0.9), "piston": (0.1, 0.9, 0.9), "rod": (1.0, 1.0, 0.2), "body": (0.5, 0.5, 0.5), "thigh": (0.1, 0.3, 0.9),
            "shin": (0.1, 0.7, 0.3), "foot": (0.9, 0.7, 0.1)}
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
    swing(rig, name, 0.0, 12.0)                        # exaggerated, to show the joint
    s = bpy.context.scene
    s.render.engine = "BLENDER_WORKBENCH"
    s.display.shading.color_type = "MATERIAL"
    s.render.resolution_x, s.render.resolution_y = 900, 1100
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type, cam.data.ortho_scale = "ORTHO", 15.0
    bpy.context.collection.objects.link(cam)
    s.camera = cam
    top_z = F.mechrig.CHASSIS[name]["height"]
    for view, loc, rot in (("front", (0, 40, top_z / 2), (90, 0, 180)), ("left", (-40, 0, top_z / 2), (90, 0, -90)),
                           ("right", (40, 0, top_z / 2), (90, 0, 90))):
        cam.location, cam.rotation_euler = loc, Euler([math.radians(a) for a in rot], "XYZ")
        F.render(os.path.join(F.PREVIEW, f"arms-{name}-{view}.png"))
    print("ARMS_DONE")
