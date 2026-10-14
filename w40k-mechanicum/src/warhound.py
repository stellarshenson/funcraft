"""The Warhound Titan of the saint scene: an assembly kit of 15 printable parts (in/models/warhound/, units mm, from
the owner's Wardog_titan_fix.zip), put together, painted and posed into one model. Blender 4.5.

The kit holds each part as its own STL, laid out apart for printing: no part is in its place. The method is that of
the Marauder of mech-design (src/marauder.py): look at the parts, measure the joints on the meshes, move every part
by a rigid motion onto the part it hangs from.

    blender -b -P src/warhound.py -- kit                        # the parts as supplied: wip/preview/warhound-kit-<view>.png
    blender -b -P src/warhound.py -- parts <stem> <name> ...    # some parts as supplied: wip/preview/warhound-<stem>-<view>.png
    blender -b -P src/warhound.py -- build [part ...]           # the model, and wip/preview/warhound-built-<view>.png
    blender -b -P src/warhound.py -- lookdev                    # painted, with its joints: wip/preview/warhound-look-<view>.png

The kit faces -y with z up; the mech's left is +x. Joints measured on the meshes (circle and sphere fits, kit mm):

    body           the reference
    waist          its top ring (r 3.69) in the socket under the body (r 3.73); a shift, no turn
    leg            its hip wheel (bore r 2.30) on the pin at the end of the waist's hip drum (r 2.0, axis x); the
                   leg lies on its side in the kit with the bore outward, so it turns half round about z, then about
                   the hip axis until its ankle ball stands under the hip: a raptor's leg, the knee behind, the lower
                   leg forward and its armour plate in front
    foot           its cup (r 3.1) on the leg's ankle ball (r 3.3), sole level, toes forward. The right foot is
                   printed upright: it is laid on the mirrored left foot (ICP, median gap 0.25)
    gun            its cup on the shoulder ball (r 2.3) at the body's side, barrels forward: the plasma blastgun
                   on the right arm and the vulcan mega-bolter on the left, as in the owner's picture
    head           its neck (r 2.8) in the round socket of the body's front face (r 3.11)
    leg armour     laid on the front of the lower leg where most of its inner face touches the leg
                   (wip/warhound/fit_armour.py)
    top cover      the carapace plate along the body's spine, its wide end forward over the head

Joints. The kit joins its parts with snap-on balls and pins; the owner: "make the connections not snap-ons but
industrial". Every joint gets a housing of steel: the hips a hub with a flange and a ring of bolts on the outer face of
the leg's wheel, the shoulders a collar with bolts between body and gun, the ankles a bolted collar over the foot's
cup, the waist a bolted ring under the body, the neck a collar at the body's front.

Paint. The household's three enamels as on the mechs of mech-design (src/paint.py, `_surface`): Mars red carapace
and plates, bone on the carapace cover, black on the waist, legs, feet and guns; faces in small flat patches are
machinery in gunmetal; the housings are dark steel with bright bolts. Every part keeps all its triangles: decimated to a quarter, its flat plates crumpled into facets.
"""
import bpy, os, sys, math, json, colorsys
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "in", "models", "warhound")
PREVIEW = os.path.join(ROOT, "wip", "preview")
NAMES = ["body", "waist", "head", "top_cover", "leg_left", "leg_right", "leg_armour_left", "leg_armour_right",
         "foot_left", "foot_right", "plasma", "laser", "gigaflamer", "megabolter"]


def load(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(PARTS, f"{name}.stl"))
    ob = bpy.context.object
    ob.name = name
    return ob


def tint(ob, k, n):
    m = bpy.data.materials.new(ob.name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colorsys.hsv_to_rgb(k / n, 0.75, 0.45 if ob.name.endswith("right") else 0.9), 1)
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


def _look(forward, up):
    f = forward.normalized()
    r = f.cross(up).normalized()
    u = r.cross(f)
    return Matrix((r, u, -f)).transposed().to_euler()


def views(obs, stem, dirs):
    """Orthographic pictures of the objects `obs`: for every (label, direction the camera looks from, up) of `dirs`,
    wip/preview/<stem>-<label>.png, with the centre and scale in <stem>.json for measuring on them."""
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
        cam.rotation_euler = _look(-d, up)
        side = d.cross(up).normalized()
        sun.rotation_euler = (-(d + 0.5 * side + 0.6 * up)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.render.filepath = os.path.join(PREVIEW, f"{stem}-{label}.png")
        bpy.ops.render.render(write_still=True)
    json.dump(dict(centre=list(mid), scale=1.02 * size), open(os.path.join(PREVIEW, f"{stem}.json"), "w"))
    print("VIEWS", stem, "centre", [round(v, 1) for v in mid], "ortho scale", round(1.02 * size, 1))


SIX = [("xp", (1, 0, 0), (0, 0, 1)), ("xm", (-1, 0, 0), (0, 0, 1)), ("yp", (0, 1, 0), (0, 0, 1)), ("ym", (0, -1, 0), (0, 0, 1)),
       ("zp", (0, 0, 1), (0, 1, 0)), ("zm", (0, 0, -1), (0, 1, 0))]
ISO = [("i1", (1, -1, 0.8), (0, 0, 1)), ("i2", (-1, -1, 0.8), (0, 0, 1)), ("i3", (1, 1, 0.8), (0, 0, 1)), ("i4", (-1, 1, 0.8), (0, 0, 1))]


def kit():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obs = [load(n) for n in NAMES]
    for k, o in enumerate(obs):
        tint(o, k, len(NAMES))
    setup()
    views(obs, "warhound-kit", [("z", (0, 0, 1), (0, 1, 0)), ("y", (0, -1, 0), (0, 0, 1)), ("iso", (1, -1, 0.7), (0, 0, 1))])


def parts(stem, names):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obs = [load(n) for n in names]
    for o in obs:
        tint(o, NAMES.index(o.name), len(NAMES))
    setup()
    views(obs, f"warhound-{stem}", SIX + ISO)


HIP = (16.52, 37.66)                     # waist: the hip drum's axis (y, z), along x
WAIST = (0.19, 39.22, 0.12)              # the waist's shift into the body's socket
LEGS = {"left": dict(wheel=(13.27, 35.18, 30.32), ball=(9.15, 4.63, 22.82), side=5.8),          # inner face of the
        "right": dict(wheel=(-22.07, 27.06, 27.65), ball=(-17.95, -3.36, 18.87), side=-14.6)}   # wheel, x of the waist's end
CUPS = {"foot_left": (10.28, 34.23, 8.98), "foot_right": (-20.09, 1.82, -3.05)}
RIGHT_FOOT = ((1.0, 0.0009, 0.0039), (0.0039, -0.0503, -0.9987), (-0.0007, 0.9987, -0.0503))   # onto the mirrored left foot
SHOULDER = {"right": (-22.63, 49.68, 54.09), "left": (14.01, 49.68, 54.09)}
GUNS = {"right": ("plasma", (82.05, 1.33, 38.24)), "left": ("megabolter", (66.42, 2.24, 42.73))}
NECK, SOCKET = (31.79, -13.28, 41.0), (-4.28, 35.73, 54.22)
ARMOUR = {"left": (0.0, -6.5, -1.5), "right": (0.0, 0.5, -3.0)}    # kit mm: the plate laid on the leg (wip/warhound/fit_armour.py)
COVER = ((47.17, 32.2, 75.54), (-4.3, 36.0, 63.7))   # the cover's inner face at its front end -> the front of the spine
AHEAD = 1.0                              # mm: the ankle stands this far before the hip


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def motion(anchor, target, R=None):
    """The rigid motion that turns by R about `anchor` and puts it on `target`."""
    return Matrix.Translation(Vector(target)) @ (R or Matrix.Identity(4)) @ Matrix.Translation(-Vector(anchor))


def assemble():
    """The motion of every part, as {name: Matrix}, in the body's frame (kit mm)."""
    M = {"body": Matrix.Identity(4), "waist": Matrix.Translation(Vector(WAIST))}
    hip = Vector((0, HIP[0] + WAIST[1], HIP[1] + WAIST[2]))
    for side, g in LEGS.items():
        target = Vector((g["side"] + WAIST[0], hip.y, hip.z))
        best = None
        for k in range(-1800, 1800):
            th = k / 10
            m = motion(g["wheel"], target, rot("X", th) @ rot("Z", 180))
            b = m @ Vector(g["ball"])
            if b.z < target.z and (best is None or abs(b.y - (target.y - AHEAD)) < best[0]):
                best = (abs(b.y - (target.y - AHEAD)), th, m)
        M["leg_" + side] = best[2]
        M["leg_armour_" + side] = best[2] @ Matrix.Translation(Vector(ARMOUR[side]))
        print("LEG", side, "turned", best[1], "degrees about the hip; ankle at", [round(v, 2) for v in best[2] @ Vector(g["ball"])])
    for side in ("left", "right"):
        ball = M["leg_" + side] @ Vector(LEGS[side]["ball"])
        R = Matrix.Identity(4) if side == "left" else Matrix.Scale(-1, 4, (1, 0, 0)) @ Matrix(RIGHT_FOOT).to_4x4() @ Matrix.Scale(-1, 4, (1, 0, 0))
        M["foot_" + side] = motion(CUPS["foot_" + side], ball, R)
    for side, (gun, cup) in GUNS.items():
        # the cup opens towards +y and the barrels point to +z: barrels forward (-y), cup towards the body
        R = Matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0))).to_4x4() if side == "left" else Matrix(((0, 1, 0), (0, 0, -1), (-1, 0, 0))).to_4x4()
        M[gun] = motion(cup, SHOULDER[side], R)
    M["head"] = motion(NECK, SOCKET, rot("X", 90))
    M["top_cover"] = motion(COVER[0], COVER[1], rot("X", 90))
    return M


SCALE = 16.0 / 65.77                     # metres per kit mm: the Warhound 16 m tall
KEEP = 1.0                               # share of each part's triangles kept: at 0.25 the flat plates crumpled into facets
PATCH = 0.5                              # mm^2: a flat patch smaller than this is machinery
PAINT = {"body": "red", "top_cover": "bone", "head": "red", "waist": "black", "leg_left": "black", "leg_right": "black",
         "leg_armour_left": "red", "leg_armour_right": "red", "foot_left": "black", "foot_right": "black",
         "plasma": "black", "megabolter": "black"}
COLOURS = dict(red=((0.20, 0.014, 0.010), 0.45, 0.0, 0.5), bone=((0.46, 0.40, 0.29), 0.5, 0.0, 0.5),
               black=((0.030, 0.031, 0.034), 0.45, 0.2, 0.6), machine=((0.20, 0.205, 0.215), 0.4, 0.8, 0.3),
               steel=((0.07, 0.07, 0.08), 0.5, 1.0, 0.2), bolt=((0.5, 0.5, 0.52), 0.35, 1.0, 0.0))


def materials():
    sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "mech-design", "src"))
    import paint as P
    return {k: P._surface("wh_" + k, *v) for k, v in COLOURS.items()}


def patches(bm):
    """Faces in flat patches (neighbours within 10 degrees) and the area of each face's patch."""
    import bmesh
    bm.faces.ensure_lookup_table()
    parent = list(range(len(bm.faces)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    cos = math.cos(math.radians(10))
    for e in bm.edges:
        if len(e.link_faces) == 2:
            a, b = e.link_faces
            if a.normal.dot(b.normal) > cos:
                ra, rb = root(a.index), root(b.index)
                if ra != rb:
                    parent[ra] = rb
    area = {}
    for f in bm.faces:
        r = root(f.index)
        area[r] = area.get(r, 0.0) + f.calc_area()
    return [area[root(f.index)] for f in bm.faces]


def painted(name, m, mats):
    """The part, moved into place, decimated, every face given its enamel or machinery."""
    import bmesh
    o = load(name)
    o.matrix_world = m
    if KEEP < 1:
        d = o.modifiers.new("keep", "DECIMATE")
        d.ratio = KEEP
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="keep")
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    for k in ("red", "bone", "black", "machine"):
        o.data.materials.append(mats[k])
    bm = bmesh.new()
    bm.from_mesh(o.data)
    area = patches(bm)
    slot = ["red", "bone", "black", "machine"].index(PAINT[name])
    for f, a in zip(bm.faces, area):
        f.material_index = 3 if a < PATCH else slot
    layer = bm.faces.layers.float.new("panel")       # a tone per plate: the patch's area hashed
    for f, a in zip(bm.faces, area):
        f[layer] = 0.85 + 0.3 * ((a * 7919.0) % 1.0)
    bm.to_mesh(o.data)
    bm.free()
    o.data.attributes.active = None
    return o


def housings(M, mats):
    """Steel housings at the joints (kit mm, in place): hubs, collars and flanges with bolt heads."""
    import bmesh
    bm = bmesh.new()
    def drum(slot, centre, axis, radius, depth, segments=32):
        first = len(bm.faces)
        q = Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=depth,
                              matrix=Matrix.Translation(Vector(centre)) @ q)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[first:]:
            f.material_index = slot
    def bolted(centre, axis, radius, depth, bolts, face):
        """A disc and a ring of bolt heads on its face that looks along `face` (+1 or -1 along the axis)."""
        axis = Vector(axis).normalized()
        drum(0, centre, axis, radius, depth)
        u = axis.orthogonal().normalized()
        v = axis.cross(u)
        for k in range(bolts):
            a = math.tau * k / bolts
            p = Vector(centre) + face * axis * (depth / 2 + 0.12) + (radius - 0.45) * (math.cos(a) * u + math.sin(a) * v)
            drum(1, p, axis, 0.28, 0.25, segments=6)
    hip = Vector((0, HIP[0] + WAIST[1], HIP[1] + WAIST[2]))
    for side, sign in (("left", 1), ("right", -1)):
        inner = LEGS[side]["side"] + WAIST[0]
        outer = inner + sign * 8.32                    # the outer face of the leg's wheel
        bolted((outer + sign * 0.4, hip.y, hip.z), (1, 0, 0), 4.3, 0.8, 12, sign)        # flange
        drum(0, (outer + sign * 1.2, hip.y, hip.z), (1, 0, 0), 2.6, 1.2)                # hub
        bolted((outer + sign * 1.9, hip.y, hip.z), (1, 0, 0), 2.0, 0.3, 6, sign)        # hub cap
        for k in (0.25, 0.5, 0.75):                                                     # ribs round the wheel
            drum(0, (inner + sign * 8.32 * k, hip.y, hip.z), (1, 0, 0), 4.15, 0.35)
        sh = Vector(SHOULDER[side])
        bolted(sh - Vector((sign * 1.6, 0, 0)), (1, 0, 0), 3.4, 1.0, 10, sign)          # shoulder collar
        ball = M["leg_" + side] @ Vector(LEGS[side]["ball"])
        rim = M["foot_" + side] @ (Vector(CUPS["foot_" + side]) + Vector((0, 0, 2.9)))
        bolted(rim, (0, 0, 1), 4.0, 1.2, 10, 1)                                          # ankle collar
        bolted(ball + Vector((0, 0, 3.0)), (0, 0, 1), 2.4, 1.6, 6, 1)                    # its gland round the shin
    bolted((-4.3, 55.7, 45.4), (0, 0, 1), 4.6, 0.8, 14, -1)                              # waist ring
    bolted((-4.28, 34.4, 54.22), (0, 1, 0), 3.7, 0.9, 10, -1)                            # neck collar
    me = bpy.data.meshes.new("warhound_joints")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("warhound_joints", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mats["steel"])
    o.data.materials.append(mats["bolt"])
    return o


def model():
    """The painted Warhound with its housings, parented to an empty `warhound` at its feet: metres, facing -y."""
    mats = materials()
    M = assemble()
    obs = [painted(n, m, mats) for n, m in M.items()]
    obs.append(housings(M, mats))
    lo = min(v.co.z for o in obs for v in o.data.vertices)
    mid = Vector((-4.3, 50.0, lo))
    root = bpy.data.objects.new("warhound", None)
    bpy.context.collection.objects.link(root)
    for o in obs:
        o.data.transform(Matrix.Scale(SCALE, 4) @ Matrix.Translation(-mid))
        o.data.update()
        o.parent = root
    bpy.context.view_layer.update()                  # the bounding boxes follow the moved vertices
    return root, obs


def lookdev():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    root, obs = model()
    s = bpy.context.scene
    setup(samples=64)
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.37, 0.40, 1)
    s.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    views(obs, "warhound-look", [("side", (1, 0, 0), (0, 0, 1)), ("front", (0, -1, 0), (0, 0, 1)), ("iso", (1, -1, 0.5), (0, 0, 1)),
                                 ("back", (-1, 1, 0.4), (0, 0, 1))])


def build(only=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = assemble()
    obs = []
    for name, m in M.items():
        if only and name not in only:
            continue
        o = load(name)
        o.matrix_world = m
        tint(o, NAMES.index(name), len(NAMES))
        obs.append(o)
    lo = min((o.matrix_world @ Vector(c)).z for o in obs for c in o.bound_box)
    print("SOLES at", round(lo, 2), "mm; height", round(max((o.matrix_world @ Vector(c)).z for o in obs for c in o.bound_box) - lo, 2))
    setup()
    views(obs, "warhound-" + ("-".join(only) if only else "built"), [("side", (1, 0, 0), (0, 0, 1)), ("front", (0, -1, 0), (0, 0, 1)), ("iso", (1, -1, 0.5), (0, 0, 1)),
                                  ("back", (-1, 1, 0.4), (0, 0, 1))])


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    {"kit": lambda: kit(), "parts": lambda: parts(args[1], args[2:]), "build": lambda: build(args[1:] or None), "lookdev": lambda: lookdev()}[args[0]]()
