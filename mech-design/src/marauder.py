"""The Marauder: an assembly kit of 19 printable parts, put together into one
model for the pipeline of the other chassis. Blender 4.5.

The kit (in/models/marauder/parts/) holds each part of the mech as its own
STL, laid flat and apart: no part is in its place. The parts join through
ball joints and pins. Their centres are measured from the meshes (a sphere or
a circle fitted to the triangles whose normals agree with it) and stand in
JOINT, in the kit's units and for the left parts; the right parts are their
mirror images. In the kit the mech faces -Y and its left side is +X.

`build` leaves the hull where it is and moves every other part by a rigid
motion that puts its joint on the joint of the part it hangs from:

    hull           the reference
    head           the cockpit: its square stem goes into the square hole of the hull's front face
    cannon         its square hole goes over the peg on the right of the hull top
    shoulder plate lowered onto the hull over the shoulder
    lower torso    its waist ball in the cup under the hull
    upper leg      its cup on the hip ball; leans back by THIGH_BACK
    lower leg      its cup on the knee ball; leans forward by SHIN_FORWARD, so the knee points back
    foot           its clip on the ankle pin; level
    arm block      its ball in the shoulder cup; hangs down, swung forward by ARM_FORWARD
    gun, barrels   the gun's ball in the cup of the arm block; hang below it, barrels level and forward

A ball joint leaves the angles free: THIGH_BACK, SHIN_FORWARD and
ARM_FORWARD are chosen for the stance of a Marauder, and the first two add
up to the angle at which the knee ball's stem leaves the middle of its cup.

`build` writes in/models/marauder.stl, the whole model in the kit's units
and facing -Y, and in/models/marauder.json: the leg joints for the rig and
the centre of every part with the bone that holds it, in the frame of
src/mechrig.py (metres, facing +Y, feet on z = 0, HEIGHT tall).

    blender -b -P src/marauder.py -- kit                        # the parts as supplied: wip/preview/marauder-kit-<view>.png
    blender -b -P src/marauder.py -- parts <stem> <name> ...    # some parts as supplied: wip/preview/marauder-<stem>-<view>.png
    blender -b -P src/marauder.py -- build                      # the model, and wip/preview/marauder-built-<view>.png
"""
import bpy, os, sys, math, json, colorsys
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "in", "models", "marauder", "parts")
PREVIEW = os.path.join(ROOT, "wip", "preview")
MODELS = os.path.join(ROOT, "in", "models")
HEIGHT = 12.4                      # metres from the soles to the top of the cannon
THIGH_BACK, SHIN_FORWARD, ARM_FORWARD = 30.0, 32.0, 35.0     # degrees from the plumb line
# centres of the joints, kit units, left parts; cup and ball of one joint have the same radius within 0.1
JOINT = dict(
    waist_cup=(0.05, -14.24, -41.45),        # hull, opens down
    waist_ball=(0.06, -47.84, 9.93),         # lower torso
    hip_ball=(31.47, -47.71, -12.25),        # lower torso
    hip_cup=(31.42, -85.19, -11.26),         # upper leg, opens inward
    knee_ball=(39.24, -32.60, -11.69),       # upper leg
    knee_cup=(39.24, -88.27, -32.78),        # lower leg
    ankle_pin=(39.67, -143.90, -10.03),      # lower leg, a pin along X
    ankle_clip=(39.67, -147.0, -3.9),        # foot
    shoulder_cup=(41.05, -16.16, -26.80),    # hull, opens outward
    shoulder_ball=(41.00, -25.35, -10.58),   # arm block
    elbow_cup=(63.57, -24.35, 22.25),        # arm block
    elbow_ball=(63.59, -79.42, 32.48),       # gun; its stem leaves towards +Y
)
HEAD = dict(stem=(0.0, -0.8), base=49.0, hole=-17.15, mouth=-61.0)   # stem axis (x, y) and height of the cap's base; hull: height of the hole, y of its mouth
CANNON = (0.0, -54.49, 12.45)      # the cannon's hole to the peg at (-23.69, -4.39), its underside onto the peg's platform
PLATE = (0.0, 0.0, -7.0)           # the shoulder plates lie 5 to 8 above the hull in the kit
SOLE, TOE = -16.92, -189.11        # the foot: height of its sole, y of the tip of its toes
# the kit's parts; `right-foot.stl` is the right foot before its repair: 1044 open edges and 46 loose shells, where
# `right-foot-repaired.stl` is one closed shell with the volume of the left foot. It is not used
NAMES = ["torso", "lower-torso", "head", "ac5-cannon",
         "left-upper-leg", "left-lower-leg", "left-foot", "left-hand", "left-gun", "left-gun-barrels", "left-soulder-armor",
         "right-upper-leg", "right-lower-leg", "right-foot", "right-hand", "right-gun", "right-gun-barrels", "right-soulder-armor"]


def load(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(PARTS, f"{name}-repaired.stl"))
    ob = bpy.context.object
    ob.name = name
    return ob


def tint(ob, k, n):
    """One colour per part: the hue from the part's place in the list, the
    right side darker than the left."""
    m = bpy.data.materials.new(ob.name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colorsys.hsv_to_rgb(k / n, 0.75, 0.45 if ob.name.startswith("right") else 0.9), 1)
    b.inputs["Roughness"].default_value = 0.6
    ob.data.materials.append(m)


def setup(samples=24, side=1100):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = samples
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for d in pr.devices:
        d.use = d.type == "CUDA"
    s.render.resolution_x = s.render.resolution_y = side
    s.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("w")
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.78, 0.82, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.9


def views(obs, stem, dirs):
    """Orthographic pictures of the objects `obs`: for every (label, direction
    the camera looks from, up) of `dirs`, wip/preview/<stem>-<label>.png. A sun
    shines from behind the camera's shoulder."""
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)])
    hi = Vector([max(p[k] for p in pts) for k in range(3)])
    mid, size = (lo + hi) / 2, (hi - lo).length
    cd = bpy.data.cameras.new("c")
    cd.type, cd.ortho_scale, cd.clip_end = "ORTHO", 1.02 * size, 10 * size
    cam = bpy.data.objects.new("cam", cd)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy, sun.data.angle = 3.0, math.radians(20)
    for o in (cam, sun):
        bpy.context.collection.objects.link(o)
    bpy.context.scene.camera = cam
    for label, d, up in dirs:
        d, up = Vector(d).normalized(), Vector(up)
        cam.location = mid + d * 3 * size
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        if abs(d.dot(up)) < 0.99:                         # turn the camera so that `up` is up in the picture
            cam.rotation_euler = _look(-d, up)
        side = d.cross(up).normalized() if abs(d.dot(up)) < 0.99 else Vector((1, 0, 0))
        sun.rotation_euler = (-(d + 0.5 * side + 0.6 * up)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.render.filepath = os.path.join(PREVIEW, f"{stem}-{label}.png")
        bpy.ops.render.render(write_still=True)
    json.dump(dict(centre=list(mid), scale=1.02 * size), open(os.path.join(PREVIEW, f"{stem}.json"), "w"))
    print("VIEWS", stem, "centre", [round(v, 1) for v in mid], "ortho scale", round(1.02 * size, 1))


def _look(forward, up):
    """Rotation of a camera that looks along `forward` with `up` up."""
    from mathutils import Matrix
    f = forward.normalized()
    r = f.cross(up).normalized()
    u = r.cross(f)
    return Matrix((r, u, -f)).transposed().to_euler()


def kit():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obs = [load(n) for n in NAMES]
    for k, o in enumerate(obs):
        tint(o, k % 11, 11)
    setup()
    views(obs, "marauder-kit", [("x", (1, 0, 0), (0, 0, 1)), ("y", (0, -1, 0), (0, 0, 1)), ("z", (0, 0, 1), (0, 1, 0)),
                                ("iso", (1, -1, 0.7), (0, 0, 1))])


SIX = [("xp", (1, 0, 0), (0, 0, 1)), ("xm", (-1, 0, 0), (0, 0, 1)), ("yp", (0, 1, 0), (0, 0, 1)), ("ym", (0, -1, 0), (0, 0, 1)),
       ("zp", (0, 0, 1), (0, 1, 0)), ("zm", (0, 0, -1), (0, 1, 0))]


ISO = [("i1", (1, -1, 0.8), (0, 0, 1)), ("i2", (-1, -1, 0.8), (0, 0, 1)), ("i3", (1, 1, 0.8), (0, 0, 1)), ("i4", (-1, 1, 0.8), (0, 0, 1)),
       ("i5", (1, -1, -0.8), (0, 0, 1)), ("i6", (-1, 1, -0.8), (0, 0, 1))]


def parts(stem, names):
    """Some parts of the kit where their files put them, from the six axis
    directions: xp is the view from +X, and so on. A stem that ends in "+"
    adds six views from the corners."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obs = [load(n) for n in names]
    for k, o in enumerate(obs):
        tint(o, NAMES.index(o.name) % 11, 11)
    setup()
    views(obs, f"marauder-{stem}", SIX + ISO if stem.endswith("+") else SIX)


def turn(degrees):
    """Rotation about X that takes +Y towards +Z."""
    return Matrix.Rotation(math.radians(degrees), 4, "X")


def lean(a, b, towards):
    """The rotation about X that turns the direction from joint a to joint b,
    seen in the Y-Z plane, to the angle `towards` (degrees from +Y to +Z)."""
    return turn(towards - math.degrees(math.atan2(b[2] - a[2], b[1] - a[1])))


def motions():
    """For every part of the kit its 4 x 4 matrix from the kit to the model,
    and the place of the left leg's joints in the model."""
    J = {k: Vector(v) for k, v in JOINT.items()}
    T = Matrix.Translation
    M = {"torso": Matrix.Identity(4)}
    M["head"] = T((0.0, HEAD["mouth"] + HEAD["base"], HEAD["hole"] - HEAD["stem"][1])) @ turn(90.0)     # the stem points into the hull
    M["ac5-cannon"] = T(CANNON)
    M["lower-torso"] = T(J["waist_cup"] - J["waist_ball"])
    hip = M["lower-torso"] @ J["hip_ball"]
    # in the kit the mech faces -Y: back is +Y. Hip to knee: back and down. Knee to ankle: forward and down
    thigh = T(hip) @ lean(J["hip_cup"], J["knee_ball"], -90.0 + THIGH_BACK) @ T(-J["hip_cup"])
    knee = thigh @ J["knee_ball"]
    shin = T(knee) @ lean(J["knee_cup"], J["ankle_pin"], -90.0 - SHIN_FORWARD) @ T(-J["knee_cup"])
    ankle = shin @ J["ankle_pin"]
    foot = T(ankle - J["ankle_clip"])
    arm = T(J["shoulder_cup"]) @ turn(180.0 - ARM_FORWARD) @ T(-J["shoulder_ball"])
    elbow = arm @ J["elbow_cup"]
    gun = T(elbow) @ Matrix.Rotation(math.pi, 4, "Z") @ turn(-90.0) @ T(-J["elbow_ball"])      # stem down, barrels to -Y
    mirror = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
    for part, m in (("upper-leg", thigh), ("lower-leg", shin), ("foot", foot), ("hand", arm), ("gun", gun), ("gun-barrels", gun),
                    ("soulder-armor", T(PLATE))):
        M[f"left-{part}"], M[f"right-{part}"] = m, mirror @ m @ mirror
    toe = foot @ Vector((J["ankle_clip"].x, TOE, SOLE))
    return M, dict(hip=hip, knee=knee, ankle=ankle, toe=toe)


BONES = ["body", "thigh.L", "thigh.R", "shin.L", "shin.R", "foot.L", "foot.R"]      # the bones of src/rig.py that hold whole parts
BONE = {"upper-leg": "thigh", "lower-leg": "shin", "foot": "foot"}                   # every other part goes with the body
KEEP = 0.12                        # share of its triangles that a part keeps; a part of fewer than FEW keeps them all
FEW = 8000


def build():
    """Assemble the kit, write the model and its joint file, and show it."""
    import bmesh
    import numpy as np
    from mathutils import kdtree
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M, leg = motions()
    obs, whole = [], bmesh.new()
    for k, n in enumerate(NAMES):
        o = load(n)
        o.data.transform(M[n])
        # the kit has 2.1 million triangles, most of them on balls and rounded edges; the other chassis have 0.1 million
        d = o.modifiers.new("d", "DECIMATE")
        d.ratio = max(KEEP, min(1.0, FEW / len(o.data.polygons)))
        o.data = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        o.modifiers.clear()
        whole.from_mesh(o.data)
        tint(o, k % 11, 11)
        obs.append(o)
    setup()
    views(obs, "marauder-built", [("front", (0, -1, 0), (0, 0, 1)), ("left", (1, 0, 0), (0, 0, 1)), ("top", (0, 0, 1), (0, -1, 0)),
                                  ("iso", (1, -1.2, 0.5), (0, 0, 1)), ("back", (-0.8, 1, 0.6), (0, 0, 1))])
    me = bpy.data.meshes.new("marauder")
    whole.to_mesh(me)
    whole.free()
    model = bpy.data.objects.new("marauder", me)
    bpy.context.collection.objects.link(model)
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.wm.stl_export(filepath=os.path.join(MODELS, "marauder.stl"), export_selected_objects=True)

    # the model as src/mechrig.py loads it: half a turn about Z, feet on z = 0, centred on x and y, HEIGHT tall
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import mechrig, rig as R
    register(joints=False)
    pts = np.array([v.co for v in me.vertices])
    lo, hi = np.array([-pts[:, 0].max(), -pts[:, 1].max(), pts[:, 2].min()]), np.array([-pts[:, 0].min(), -pts[:, 1].min(), pts[:, 2].max()])
    s = HEIGHT / (hi[2] - lo[2])

    def frame(p):
        return [round(float(v), 4) for v in (s * (-p[0] - (lo[0] + hi[0]) / 2), s * (-p[1] - (lo[1] + hi[1]) / 2), s * (p[2] - lo[2]))]

    tree, owner = kdtree.KDTree(sum(len(o.data.vertices) for o in obs)), []
    for k, o in enumerate(obs):
        for v in o.data.vertices:
            tree.insert(frame(v.co), len(owner))
            owner.append(k)
    tree.balance()
    loaded = mechrig.load("marauder")
    n = len(loaded.data.vertices)
    co = np.empty(n * 3)
    loaded.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    ed = np.empty(len(loaded.data.edges) * 2, dtype=np.int64)
    loaded.data.edges.foreach_get("vertices", ed)
    shell = R._components(ed.reshape(-1, 2), np.ones(n, bool))
    shells = []
    for k in np.unique(shell):
        at = np.flatnonzero(shell == k)
        part = obs[owner[tree.find(co[at[0]])[1]]].name
        side = "L" if part.startswith("left") else "R"
        kind = part.split("-", 1)[1] if part.startswith(("left", "right")) else part
        shells.append(dict(part=part, bone=f"{BONE[kind]}.{side}" if kind in BONE else "body", vertices=int(len(at)),
                           centre=[round(float(v), 4) for v in co[at].mean(0)]))
    boxes = {}
    for o in obs:
        q = np.array([frame(v.co) for v in o.data.vertices])
        boxes[o.name] = [[round(float(v), 2) for v in q.min(0)], [round(float(v), 2) for v in q.max(0)]]
    joints = {k: frame(p) for k, p in leg.items()}                       # the kit's left leg: on -x in the frame, the rig's side L
    json.dump(dict(height=HEIGHT, scale=s, joints=joints, shells=shells, boxes=boxes), open(os.path.join(MODELS, "marauder.json"), "w"), indent=1)
    print("BUILT", len(obs), "parts,", len(me.polygons), "triangles,", len(shells), "shells,", round(hi[2] - lo[2], 1), "kit units tall, 1 unit =",
          round(s, 4), "m; joints", joints)
    for name, b in boxes.items():
        print("BOX", f"{name:22s}", b)


def register(joints=True):
    """Enter the Marauder into the tables of the other chassis: the model file
    (src/mechrig.py), the paint of banner 03 (src/paint.py) and, from the
    joint file that `build` wrote, the leg joints (src/rig.py)."""
    import mechrig, rig as R, paint as P
    mechrig.CHASSIS["marauder"] = dict(file="marauder.stl", height=HEIGHT, yaw=math.pi, label=label, skin=skin, dress=dress,   # the kit faces -Y
                                       pelvis=pelvis)
    # olive hull and legs, dark arms and feet, a red cockpit and cannon. The colour of a face follows from its part
    P.SCHEMES["marauder"] = dict(
        colours=dict(primary=(0.16, 0.17, 0.09), secondary=(0.035, 0.036, 0.038), accent=(0.30, 0.020, 0.012)),
        regions=[(lambda c, n: part_at(c).endswith(("hand", "gun", "gun-barrels", "foot")), "secondary"),
                 (lambda c, n: part_at(c) in ("head", "ac5-cannon"), "accent")],
        # the windscreen: the framed field on the front face of the cockpit, filled from a grid of points on it (its triangles are large)
        glass=dict(seeds=[(x / 10, GLASS[1] + k * (GLASS[2] - GLASS[1]) / 8) for x in range(-2, 3) for k in range(1, 8)], angle=12.0,
                   bound=lambda c: part_at(c) == "head" and abs(c.x) < GLASS[0] and GLASS[1] < c.z < GLASS[2] and c.y > GLASS[3],
                   inset=0.02, depth=-0.015, glow=0.5))
    if not joints:
        return
    d = json.load(open(os.path.join(MODELS, "marauder.json")))["joints"]
    side = dict(hip=tuple(d["hip"][1:]), knee=tuple(d["knee"][1:]), ankle=tuple(d["ankle"][1:]), toe=(d["toe"][1], 0.15))
    x = abs(d["ankle"][0])
    # pole -1: the knee points back, as the Mad Cat's. corridor and split serve the soft skin of src/rig.py, which `skin` replaces
    R.JOINTS["marauder"] = dict(x={"L": -x, "R": x}, pole=-1.0, corridor=(0.8, 4.2), split=d["hip"][2], L=side, R=side)


# The kit is made for printing: a flat disc closes every muzzle. Centre (x, z) and radius of each disc in the loaded
# model; the two of the gun pod are those of the +x side and hold for the other pod mirrored. BORE: how deep `muzzles`
# sinks a disc into its barrel
MUZZLES = dict(pod=((3.851, 6.643, 0.188), (3.850, 7.241, 0.150)), cannon=((1.403, 11.610, 0.105),))
BORE = 0.7
# the missile rack on the hatch of the lower torso: the hatch's centre and normal in the loaded model, columns and
# rows of tubes, the distance between two tubes and a tube's radius
RACK = dict(at=(0.0, 1.850, 6.860), normal=(0.0, 0.991, -0.137), cells=(5, 3), pitch=0.2, radius=0.075)
# The kit is a snap-on toy: a ball on a stem joins each leg to the lower torso and each arm to the hull. `housings`
# hides it in a heavy joint: a hub on the joint's turning axis, which runs sideways through (y, z) of `at`, with a
# bolted flange on each of the two faces it joins (their x on the +x side; the other side is the mirror image) and
# ribs between them. A drum on the turning axis keeps its look when the limb turns. pelvis: the joint hangs on the
# lower torso, which rocks with the hips
JOINTS = dict(hip=dict(at=(0.2993, 6.7264), faces=(1.54, 1.92), radius=0.40, pelvis=1),
              shoulder=dict(at=(0.43, 8.99), faces=(2.55, 2.81), radius=0.32, pelvis=0))
GLASS = (0.33, 9.02, 10.10, 3.85)   # the windscreen in the loaded model: half width, lowest and highest z, least y
FINDER = []                        # the loaded model's vertices as a search tree, and the part of each


def part_at(point):
    """The name of the part whose vertex lies nearest to `point` of the loaded model."""
    tree, part = FINDER
    return NAMES[part[tree.find(point)[1]]]


def label(mesh):
    """Mark every vertex of the loaded model with the bone of its part: the
    int attribute `bone`, an index into BONES. The parts are separate shells;
    each shell is found among the shells of the joint file by its centre.
    Runs before the paint, which changes the mesh but keeps the attribute,
    and gives `part_at` its search tree."""
    import numpy as np
    from mathutils import kdtree
    import rig as R
    shells = json.load(open(os.path.join(MODELS, "marauder.json")))["shells"]
    centres = np.array([sh["centre"] for sh in shells])
    n = len(mesh.data.vertices)
    co = np.empty(n * 3)
    mesh.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    ed = np.empty(len(mesh.data.edges) * 2, dtype=np.int64)
    mesh.data.edges.foreach_get("vertices", ed)
    shell = R._components(ed.reshape(-1, 2), np.ones(n, bool))
    bone, part = np.zeros(n, np.int32), np.zeros(n, np.int32)
    for k in np.unique(shell):
        at = shell == k
        dist = np.linalg.norm(centres - co[at].mean(0), axis=1)
        assert dist.min() < 0.01, f"a shell of {int(at.sum())} vertices is not in marauder.json: run src/marauder.py build"
        found = shells[int(dist.argmin())]
        bone[at], part[at] = BONES.index(found["bone"]), NAMES.index(found["part"])
    mesh.data.attributes.new("bone", "INT", "POINT").data.foreach_set("value", bone)
    tree = kdtree.KDTree(n)
    for k in range(n):
        tree.insert(co[k], k)
    tree.balance()
    FINDER[:] = [tree, part]


def pelvis(mesh, co):
    """The share of each vertex of `mesh` (rows of `co`) that rocks with the
    hips of src/procession/hips.py: all of the lower torso and of what
    `dress` hung on it, and none of the other parts."""
    import numpy as np
    hung = np.zeros(len(co), np.int32)
    if "pelvis" in mesh.data.attributes:
        mesh.data.attributes["pelvis"].data.foreach_get("value", hung)
    return np.array([float(h or part_at(c) == "lower-torso") for h, c in zip(hung, co)])


def _plain(name, colour, metal=0.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colour, 1)
    b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = metal, rough
    return m


def dress(mesh):
    """What the Marauder gets after its paint: open muzzles, missiles in
    the rack of its lower torso, and heavy joints at hips and shoulders. The
    added parts become part of `mesh`. Their vertices carry no `bone` mark,
    which reads as 0: the body; the int attribute `pelvis` marks those that
    hang on the lower torso."""
    bore = _plain("marauder_bore", (0.004, 0.004, 0.004), rough=0.9)
    muzzles(mesh, bore)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in (rack(bore), housings()):
        ob.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()


def _object(name, bm, mats, pelvis):
    """The mesh that `bm` holds as an object of the scene, with the materials
    `mats`. pelvis: the mark of each vertex, one number or a list."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    mark = [pelvis] * len(me.vertices) if isinstance(pelvis, int) else pelvis
    me.attributes.new("pelvis", "INT", "POINT").data.foreach_set("value", mark)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def muzzles(mesh, bore):
    """Sink the disc that closes each muzzle BORE deep into its barrel and
    give the hole the material `bore`."""
    import bmesh
    mesh.data.materials.append(bore)
    slot = len(mesh.data.materials) - 1
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    front = [(f, f.calc_center_median()) for f in bm.faces if f.normal.y > 0.9]
    front = [(f, c) for f, c in front if c.y > 3.0]
    for x, z, r in [(side * x, z, r) for x, z, r in MUZZLES["pod"] for side in (1, -1)] + list(MUZZLES["cannon"]):
        disc = [f for f, c in front if math.hypot(c.x - x, c.z - z) < r]
        walls = bmesh.ops.inset_region(bm, faces=disc, thickness=0.004, depth=-BORE)["faces"]
        for f in disc + walls:
            f.material_index = slot
        print(f"MUZZLE at x {x:.2f} z {z:.2f}: {len(disc)} faces sunk")
    bm.to_mesh(mesh.data)
    bm.free()


def rack(bore):
    """The missiles of the lower torso: a plate on its hatch, on it a brass
    tube per missile, 6 cm tall and open, with a black floor, and in each
    tube a missile: a bone body and a red nose whose point reaches just out
    of the tube. Returns the object."""
    import bmesh
    mats = [_plain("marauder_rack", (0.05, 0.05, 0.055), metal=1.0, rough=0.45), _plain("marauder_brass", (0.6, 0.42, 0.16), metal=1.0, rough=0.35),
            bore, _plain("marauder_missile", (0.62, 0.55, 0.42), rough=0.45), _plain("marauder_warhead", (0.35, 0.03, 0.02), rough=0.4)]
    (cols, rows), pitch, r = RACK["cells"], RACK["pitch"], RACK["radius"]
    bm = bmesh.new()

    def add(slot, op, **kw):
        first = len(bm.faces)
        op(bm, **kw)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[first:]:
            f.material_index = slot

    T = Matrix.Translation
    # in the rack's own frame: x across, y up the hatch, z out of it
    add(0, bmesh.ops.create_cube, size=1.0, matrix=T((0, 0, 0.025)) @ Matrix.Diagonal((cols * pitch + 0.04, rows * pitch + 0.04, 0.05, 1.0)))
    for i in range(cols):
        for j in range(rows):
            at = T(((i - (cols - 1) / 2) * pitch, (j - (rows - 1) / 2) * pitch, 0.0))
            for wall in (r + 0.012, r):                      # the tube's outer and inner wall, from the plate at z = 0.05 to 0.11
                add(1, bmesh.ops.create_cone, cap_ends=False, segments=20, radius1=wall, radius2=wall, depth=0.06, matrix=at @ T((0, 0, 0.08)))
            add(2, bmesh.ops.create_circle, cap_ends=True, segments=20, radius=r, matrix=at @ T((0, 0, 0.052)))
            add(3, bmesh.ops.create_cone, cap_ends=True, segments=20, radius1=0.6 * r, radius2=0.6 * r, depth=0.035, matrix=at @ T((0, 0, 0.0695)))
            add(4, bmesh.ops.create_cone, cap_ends=True, segments=20, radius1=0.6 * r, radius2=0.004, depth=0.05, matrix=at @ T((0, 0, 0.112)))
    ob = _object("marauder_rack", bm, mats, 1)
    n = Vector(RACK["normal"]).normalized()
    u = Vector((1.0, 0.0, 0.0))
    ob.matrix_world = Matrix.Translation(RACK["at"]) @ Matrix((u, u.cross(n) * -1.0, n)).transposed().to_4x4()
    return ob


def housings():
    """The heavy joints of JOINTS at both hips and both shoulders, as one
    object: per joint a steel hub, two flanges with ten bolts each and three
    ribs between them."""
    import bmesh
    mats = [_plain("marauder_joint", (0.08, 0.08, 0.09), metal=1.0, rough=0.5), _plain("marauder_bolt", (0.5, 0.5, 0.52), metal=1.0, rough=0.35)]
    bm = bmesh.new()
    pelvis = []

    def drum(slot, mark, centre, radius, depth, segments=32):
        first, verts = len(bm.faces), len(bm.verts)
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=depth,
                              matrix=Matrix.Translation(centre) @ Matrix.Rotation(math.pi / 2, 4, "Y"))      # its axis lies along x
        bm.faces.ensure_lookup_table()
        for f in bm.faces[first:]:
            f.material_index = slot
        pelvis.extend([mark] * (len(bm.verts) - verts))

    for J in JOINTS.values():
        (y, z), (near, far), r = J["at"], J["faces"], J["radius"]
        for side in (1, -1):
            mark = J["pelvis"]
            drum(0, mark, (side * (near + far) / 2, y, z), r, far - near + 0.2)
            for face, wide, look in ((near, r + 0.16, 1), (far, r + 0.12, -1)):
                drum(0, mark, (side * face, y, z), wide, 0.08)
                for k in range(10):                          # bolt heads on the flange's side that looks into the gap
                    a = math.tau * k / 10
                    drum(1, mark, (side * (face + look * 0.055), y + (wide - 0.06) * math.cos(a), z + (wide - 0.06) * math.sin(a)), 0.035, 0.03, segments=6)
            for k in (1, 2, 3):
                drum(0, mark, (side * (near + (far - near) * k / 4), y, z), r + 0.04, 0.03)
    return _object("marauder_joints", bm, mats, pelvis)


def skin(mesh, rig):
    """Give every part wholly to its bone: the parts are rigid, and the soft
    skin of src/rig.py would bend them at the joints."""
    import numpy as np
    bone = np.empty(len(mesh.data.vertices), np.int32)
    mesh.data.attributes["bone"].data.foreach_get("value", bone)
    mesh.vertex_groups.clear()
    for k, name in enumerate(BONES):
        mesh.vertex_groups.new(name=name).add(np.flatnonzero(bone == k).tolist(), 1.0, "REPLACE")
    print("SKIN marauder:", ", ".join(f"{name} {int((bone == k).sum())}" for k, name in enumerate(BONES)))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "kit" in argv:
        kit()
    elif "parts" in argv:
        parts(argv[1], argv[2:])
    elif "build" in argv:
        build()
