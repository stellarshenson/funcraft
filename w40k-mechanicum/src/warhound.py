"""The Warhound Titan of the saint scene: an assembly kit of 15 printable parts (resources/models/warhound/, units mm, from
the owner's Wardog_titan_fix.zip), put together, painted and posed into one model. Blender 4.5.

The kit holds each part as its own STL, laid out apart for printing: no part is in its place. The method is that of
the Marauder of mech-design (src/marauder.py): look at the parts, measure the joints on the meshes, move every part
by a rigid motion onto the part it hangs from.

    blender -b -P src/warhound.py -- kit                        # the parts as supplied: wip/preview/warhound-kit-<view>.png
    blender -b -P src/warhound.py -- parts <stem> <name> ...    # some parts as supplied: wip/preview/warhound-<stem>-<view>.png
    blender -b -P src/warhound.py -- build [part ...]           # the model, and wip/preview/warhound-built-<view>.png
    blender -b -P src/warhound.py -- lookdev                    # painted, with its joints: wip/preview/warhound-look-<view>.png
    blender -b -P src/warhound.py -- lookdev <stem> '<json>'    # in another pose (keys of POSE): wip/preview/<stem>-<view>.png
    blender -b -P src/warhound.py -- plating                    # the charts of the armour: wip/warhound/warhound.npz
    .venv-moge/bin/python src/warhoundlivery.py                 # the ornament drawn on them: wip/warhound/livery/

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
    leg armour     a greave round the front of the shin: the kit lays it hollow side out; turned half round the
                   shin's line, its hollow side wraps the shin (gap and overlap measured on the meshes)
    top cover      the carapace plate along the body's spine, its wide end forward over the head

Joints. The kit joins its parts with snap-on balls and pins; the owner: "make the connections not snap-ons but
industrial". Every joint gets a housing of steel: the hips a hub with a flange and a ring of bolts on the outer face of
the leg's wheel, the shoulders a collar with bolts between body and gun, the ankles a bolted collar over the foot's
cup, the waist a bolted ring under the body, the neck a collar at the body's front.

Paint. The household's three enamels as on the mechs of mech-design (src/paint.py, `_surface`): Mars red carapace
and plates, bone on the carapace cover, black on the waist, legs, feet and guns; faces in small flat patches are
machinery in gunmetal; the housings are dark steel with bright bolts. Every part keeps all its triangles: decimated to a quarter, its flat plates crumpled into facets.
The lenses of the face and the oval windows on the head's sides are glossy black glass, the grilles behind the windows
black with heat glowing deep inside them (`glow`). The paint carries wear and war damage (`battle`): shell impacts,
dents, scratches, paint flaking to the primer and to the metal, charred patches, soot.
"""
import bpy, os, sys, math, json, colorsys
import numpy as np
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "resources", "models", "warhound")
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
# wheel: the hip; knees: the two hinges below it (y, z; their pins run along x); faces: x of the leg's two flat sides
LEGS = {"left": dict(wheel=(13.27, 35.18, 30.32), knees=((26.08, 32.66), (21.42, 23.16)), ball=(9.15, 4.63, 22.82),
                     side=5.8, faces=(5.3, 12.5)),       # side: inner face of the wheel, x of the waist's end
        "right": dict(wheel=(-22.07, 27.06, 27.65), knees=((18.35, 31.2), (13.18, 21.68)), ball=(-17.95, -3.36, 18.87),
                      side=-14.6, faces=(-21.3, -14.5))}
CUPS = {"foot_left": (10.28, 34.23, 8.98), "foot_right": (-20.09, 1.82, -3.05)}
RIGHT_FOOT = ((1.0, 0.0009, 0.0039), (0.0039, -0.0503, -0.9987), (-0.0007, 0.9987, -0.0503))   # onto the mirrored left foot
SHOULDER = {"right": (-22.63, 49.68, 54.09), "left": (14.01, 49.68, 54.09)}
GUNS = {"right": ("plasma", (82.05, 1.33, 38.24)), "left": ("megabolter", (66.42, 2.24, 42.73))}
NECK, SOCKET = (31.79, -13.28, 41.0), (-4.28, 35.73, 54.22)
# kit mm: the plate shifted along the leg (src/warhound/fit_armour.py), then turned half round the line along the shin
# (x, z) so its hollow side wraps the front of the shin: the kit lays it with its hollow side away from the leg
ARMOUR = {"left": ((0.0, -6.5, -1.5), (9.18, 18.5)), "right": ((0.0, 0.5, -3.0), (-17.93, 16.25))}
COVER = ((47.17, 32.2, 75.54), (-4.3, 36.0, 63.7))   # the cover's inner face at its front end -> the front of the spine
TORSO = (-4.3, 55.7, 45.4)               # the waist ring: the torso turns about its axis
# the stance: per leg how far its ankle stands before the hip (mm) and how far its two knee hinges bend (degrees;
# None: bent so far that the sole stands as low as the other's); the torso's turn and lean, the head's turn and nod
# and each gun's lift (degrees)
POSE = dict(left=dict(ahead=1.0, bend=(0.0, 0.0)), right=dict(ahead=1.0, bend=(0.0, 0.0)),
            torso=(0.0, 0.0), head=(0.0, 0.0), guns=dict(right=0.0, left=0.0))


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def motion(anchor, target, R=None):
    """The rigid motion that turns by R about `anchor` and puts it on `target`."""
    return Matrix.Translation(Vector(target)) @ (R or Matrix.Identity(4)) @ Matrix.Translation(-Vector(anchor))


def about(point, axis, deg):
    """A turn by `deg` about the line through `point` along `axis`."""
    return Matrix.Translation(Vector(point)) @ rot(axis, deg) @ Matrix.Translation(-Vector(point))


def leg(side, ahead, bend):
    """The motions of the leg's three pieces (hip arm, thigh, shin): the knees bent by `bend`, the whole leg turned
    about the hip until its ankle stands `ahead` mm before the hip and below it."""
    g = LEGS[side]
    hip = Vector((0, HIP[0] + WAIST[1], HIP[1] + WAIST[2]))
    target = Vector((g["side"] + WAIST[0], hip.y, hip.z))
    knees = [about((0, *k), "X", b) for k, b in zip(g["knees"], bend)]
    chain = knees[0] @ knees[1]
    best = None
    for step, span in ((1.0, None), (0.05, 1.5)):
        lo, hi = (-180, 180) if span is None else (best[1] - span, best[1] + span)
        for k in range(int(round((hi - lo) / step)) + 1):
            th = lo + k * step
            m = motion(g["wheel"], target, rot("X", th) @ rot("Z", 180))
            b = m @ chain @ Vector(g["ball"])
            if b.z < target.z and (best is None or abs(b.y - (target.y - ahead)) < best[0]):
                best = (abs(b.y - (target.y - ahead)), th, m)
    m = best[2]
    return [m, m @ knees[0], m @ chain]


def legs(pose):
    """Both legs, the second's lower knee bent until its ankle stands as low as the first's: both soles on the ground."""
    out = {}
    for side in ("left", "right"):
        p = pose[side]
        if p["bend"][1] is not None:
            out[side] = leg(side, p["ahead"], p["bend"])
    for side in ("left", "right"):
        p = pose[side]
        if p["bend"][1] is None:
            other = out["left" if side == "right" else "right"]
            z = (other[2] @ Vector(LEGS["left" if side == "right" else "right"]["ball"])).z
            best = None
            for k in range(-160, 161):
                b2 = k * 0.25
                pieces = leg(side, p["ahead"], (p["bend"][0], b2))
                gap = abs((pieces[2] @ Vector(LEGS[side]["ball"])).z - z)
                if best is None or gap < best[0]:
                    best = (gap, b2, pieces)
            print("LEG", side, "lower knee bent", best[1], "degrees; ankles level within", round(best[0], 3), "mm")
            out[side] = best[2]
    return out


def assemble(pose=POSE, legs_done=None):
    """The motion of every part, as {name: Matrix}, in the body's frame (kit mm). A leg is three pieces:
    leg_<side>.0 the hip arm, .1 the thigh, .2 the shin. legs_done: the result of legs(pose), when it is known."""
    lg = legs_done or legs(pose)
    M = {"waist": Matrix.Translation(Vector(WAIST))}
    for side in ("left", "right"):
        for k, m in enumerate(lg[side]):
            M[f"leg_{side}.{k}"] = m
        shift, (x, z) = ARMOUR[side]
        M["leg_armour_" + side] = lg[side][2] @ about((x, 0, z), "Y", 180) @ Matrix.Translation(Vector(shift))
        ball = lg[side][2] @ Vector(LEGS[side]["ball"])
        R = Matrix.Identity(4) if side == "left" else Matrix.Scale(-1, 4, (1, 0, 0)) @ Matrix(RIGHT_FOOT).to_4x4() @ Matrix.Scale(-1, 4, (1, 0, 0))
        M["foot_" + side] = motion(CUPS["foot_" + side], ball, R)
    T = about(TORSO, "Z", pose["torso"][0]) @ about(TORSO, "X", pose["torso"][1])
    M["body"] = T
    for side, (gun, cup) in GUNS.items():
        # the cup opens towards +y and the barrels point to +z: barrels forward (-y), cup towards the body
        R = Matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0))).to_4x4() if side == "left" else Matrix(((0, 1, 0), (0, 0, -1), (-1, 0, 0))).to_4x4()
        M[gun] = T @ about(SHOULDER[side], "X", pose["guns"][side]) @ motion(cup, SHOULDER[side], R)
    M["head"] = T @ about(SOCKET, "Z", pose["head"][0]) @ about(SOCKET, "X", pose["head"][1]) @ motion(NECK, SOCKET, rot("X", 90))
    M["top_cover"] = T @ motion(COVER[0], COVER[1], rot("X", 90))
    return M


SCALE = 16.0 / 65.77                     # metres per kit mm: the Warhound 16 m tall
KEEP = 1.0                               # share of each part's triangles kept: at 0.25 the flat plates crumpled into facets
PATCH = 0.5                              # mm^2: a flat patch smaller than this is machinery
PAINT = {"body": "red", "top_cover": "bone", "head": "red", "waist": "black", "leg_left": "black", "leg_right": "black",
         "leg_armour_left": "red", "leg_armour_right": "red", "foot_left": "black", "foot_right": "black",
         "plasma": "black", "megabolter": "black"}
COLOURS = dict(red=((0.20, 0.014, 0.010), 0.45, 0.0, 0.8), bone=((0.46, 0.40, 0.29), 0.5, 0.0, 0.8),
               black=((0.030, 0.031, 0.034), 0.45, 0.2, 0.8), machine=((0.20, 0.205, 0.215), 0.4, 0.8, 0.3),
               steel=((0.07, 0.07, 0.08), 0.5, 1.0, 0.2), bolt=((0.5, 0.5, 0.52), 0.35, 1.0, 0.0),
               eye=((0.004, 0.004, 0.005), 0.06, 0.0, 0.0))
SLOTS = ["red", "bone", "black", "machine", "eye", "armour", "grille"]
EYES = ((30.13, -15.0), (33.57, -15.0))   # head, kit mm: the lenses in the two round sockets of its face (x, y)
EYE = (0.55, 59.9, 61.0)                 # their radius and the z of the lens between the socket's floor and rim
MID = 31.86                              # head, kit mm: x of its middle plane, the two sides mirror about it
WINDOW = (28.11, -11.49, 52.35)          # head: a face in the oval window on its right side; the whole flat patch is glass
# head: the grille behind the window, (y, z) outline of its opening on the side plate (src/warhound/headpick.py); the
# slats and the wall behind them lie nearer than GRILLE_DEPTH to the middle plane, the side plate and its frame farther
GRILLE = [(-9.45, 45.86), (-9.83, 47.39), (-10.6, 48.54), (-11.75, 49.31), (-12.89, 49.82), (-14.04, 49.95),
          (-15.07, 49.82), (-15.96, 49.44), (-16.6, 48.67), (-16.34, 47.39), (-15.83, 46.24), (-14.68, 45.48),
          (-13.53, 45.35), (-11.75, 45.61), (-10.21, 45.73)]
GRILLE_DEPTH = 5.4
# ornament on the armour (mech-design/src/procession/ornament.py): the parts that carry it, the least area of a plate
# that gets a chart of its own (square metres), the most a chart may bend from its mean direction, the atlas
ORNATE = ("body", "head", "top_cover", "leg_armour_left", "leg_armour_right")
CHART_AREA, BEND, ATLAS, MARGIN = 0.05, math.radians(35), 8192, 6
PLATING = os.path.join(ROOT, "wip", "warhound", "warhound.npz")
LIVERY = os.path.join(ROOT, "wip", "warhound", "livery")


def materials():
    sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "mech-design", "src"))
    import paint as P
    mats = {k: P._surface("wh_" + k, *v) for k, v in COLOURS.items()}
    mats["armour"] = armour(P) if os.path.exists(os.path.join(LIVERY, "warhound_colour.png")) else mats["red"]
    for m in {mats[k].name: mats[k] for k in ("red", "bone", "black", "armour")}.values():
        battle(m)
    mats["grille"] = glow(P._surface("wh_grille", *COLOURS["black"]))
    return mats


GLOW = ((1.0, 0.22, 0.04), 1.0, 0.06)    # the heat inside the grilles: colour of its light, strength where the slats
                                         # close it in, and the reach of that test in metres of the scene


def glow(m):
    """Heat inside a grille: where the surface's ambient occlusion is deep, between and behind the slats, it gives off
    a dull orange light that rises and falls over the loop. Its scene sets the Value node `phase` (0 to 1) every
    frame; left alone the light holds its mean."""
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.only_local = True
    ao.inputs["Distance"].default_value = GLOW[2]
    ph = N.new("ShaderNodeValue")
    ph.name = "phase"
    ph.outputs[0].default_value = 0.0

    def op(kind, a, z):
        n = N.new("ShaderNodeMath")
        n.operation = kind
        for k, x in enumerate((a, z)):
            if isinstance(x, (int, float)):
                n.inputs[k].default_value = x
            else:
                L.new(x, n.inputs[k])
        return n.outputs[0]

    deep = op("POWER", op("SUBTRACT", 1.0, ao.outputs["AO"]), 3.0)
    angle = op("MULTIPLY", ph.outputs[0], 2 * math.pi)
    pulse = op("ADD", op("MULTIPLY", op("SINE", angle, 0.0), 0.15),
               op("ADD", op("MULTIPLY", op("SINE", op("ADD", op("MULTIPLY", angle, 3.0), 1.0), 0.0), 0.05), 0.8))
    b.inputs["Emission Color"].default_value = (*GLOW[0], 1)
    L.new(op("MULTIPLY", op("MULTIPLY", deep, pulse), GLOW[1]), b.inputs["Emission Strength"])
    return m


def armour(P):
    """paint.py's surface with the ornament atlas (src/warhoundlivery.py) wired in through the UV layer `plate`, as
    mech-design/src/procession/livery.py does: colour, metal, roughness and relief."""
    m = P._surface("wh_armour", (1, 1, 1), 0.5, 0.0, 0.8)
    N, L = m.node_tree.nodes, m.node_tree.links
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "plate"

    def tex(kind, data, interpolation="Linear"):
        t = N.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(LIVERY, f"warhound_{kind}.png"))
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
    bump.inputs["Distance"].default_value = json.load(open(os.path.join(LIVERY, "warhound.json")))["relief"]
    L.new(tex("height", True, "Cubic"), bump.inputs["Height"])
    L.new(next(n for n in N if n.type == "BEVEL").outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], N["Principled BSDF"].inputs["Normal"])
    return m


# war damage (battle()), in the parts' own coordinates, kit mm (1 mm = 0.24 m of the 16 m titan): candidate impacts
# per mm and the share of them that hit; radius of an impact's hole, of the bare metal blasted round it and of its
# scorch (mm, times 0.5 to 1.5 per impact); large dents (candidates per mm, share, radius in mm); scratches (stretch
# of the noise across a scratch, its scale, the band of the noise kept); flaking paint (noise scale, band where the
# paint is off to the primer, band where the primer is off too); charring (noise scale, band of the heat-browned
# paint round a charred patch, band of the char); soot (noise scale, band, darkening); the colours of primer, browned
# paint and char; dent depth in metres of the scene
HITS = (0.3, 0.5)
CRATER = (0.15, 0.45, 0.6)
DENTS = (0.2, 0.5, 1.3)
SCRATCH = (12.0, 0.5, (0.68, 0.71))
FLAKES = (0.7, (0.60, 0.62), (0.66, 0.68))
CHAR = (0.18, (0.52, 0.59), (0.575, 0.62))
SOOT = (0.15, (0.45, 0.65), 0.6)
PRIMER, BROWNED, CHARRED = (0.10, 0.085, 0.07), (0.05, 0.022, 0.012), (0.012, 0.010, 0.009)
DENT = 0.03


def battle(m):
    """Wear and war damage over paint.py's surface `m`: shell impacts (a dark hole, a ring of paint blasted to bare
    metal, a scorched halo round it, a dent), large dents, scratches through the paint along the surface, paint
    flaking off to the primer and to the metal, charred patches with heat-browned paint round them, soot, and a
    mottled fade of the paint. Bare metal joins the surface's edge wear; the rest acts on its colour, roughness, metal
    and normal."""
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    co = N.new("ShaderNodeTexCoord")
    obj = co.outputs["Object"]

    def op(kind, *xs):
        n = N.new("ShaderNodeMath")
        n.operation = kind
        for k, x in enumerate(xs):
            if isinstance(x, (int, float)):
                n.inputs[k].default_value = x
            else:
                L.new(x, n.inputs[k])
        return n.outputs[0]

    def ramp(x, lo, hi, a=0.0, z=1.0):
        n = N.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        L.new(x, n.inputs["Value"])
        for k, v in zip(("From Min", "From Max", "To Min", "To Max"), (lo, hi, a, z)):
            n.inputs[k].default_value = v
        return n.outputs["Result"]

    def noise(vec, scale, detail=2.0, rough=0.5):
        n = N.new("ShaderNodeTexNoise")
        for k, v in zip(("Scale", "Detail", "Roughness"), (scale, detail, rough)):
            n.inputs[k].default_value = v
        L.new(vec, n.inputs["Vector"])
        return n.outputs["Fac"]

    def mix(f, a, z):
        n = N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        for ident, x in (("Factor_Float", f), ("A_Color", a), ("B_Color", z)):
            sock = next(q for q in n.inputs if q.identifier == ident)
            if isinstance(x, tuple):
                sock.default_value = (*x, 1)
            else:
                L.new(x, sock)
        return next(q for q in n.outputs if q.identifier == "Result_Color")

    def shots(scale, share):
        """Points scattered through the part's volume, one per cell of `scale` per mm, a `share` of them used: the
        distance of the surface point from the nearest along the surface (the part's normal taken out, so every
        surface the shot crosses shows it), in mm over the point's size, and whether it is used."""
        vor = N.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = scale
        L.new(obj, vor.inputs["Vector"])
        rnd = N.new("ShaderNodeSeparateColor")
        L.new(vor.outputs["Color"], rnd.inputs["Color"])
        v = N.new("ShaderNodeVectorMath")
        v.operation = "SUBTRACT"
        L.new(vor.outputs["Position"], v.inputs[0])
        L.new(obj, v.inputs[1])
        along = N.new("ShaderNodeVectorMath")
        along.operation = "DOT_PRODUCT"
        L.new(v.outputs[0], along.inputs[0])
        L.new(co.outputs["Normal"], along.inputs[1])
        far = N.new("ShaderNodeVectorMath")
        far.operation = "LENGTH"
        L.new(v.outputs[0], far.inputs[0])
        across = op("SQRT", op("MAXIMUM", op("SUBTRACT", op("POWER", far.outputs["Value"], 2.0),
                                              op("POWER", along.outputs["Value"], 2.0)), 0.0))
        return op("DIVIDE", across, op("MULTIPLY_ADD", rnd.outputs["Green"], 1.0, 0.5)), op("LESS_THAN", rnd.outputs["Red"], share)

    d, keep = shots(*HITS)                             # shell impacts
    jag = op("MULTIPLY", d, op("MULTIPLY_ADD", noise(obj, 3.0, 4.0), 0.5, 0.75))   # a ragged edge
    r0, r1, r2 = CRATER
    hole = op("MULTIPLY", ramp(jag, 0.7 * r0, r0, 1.0, 0.0), keep)
    blast = op("MULTIPLY", ramp(jag, 0.6 * r1, r1, 1.0, 0.0), keep)
    burn = op("MULTIPLY", ramp(jag, 0.3 * r2, r2, 1.0, 0.0), keep)
    dent = op("MULTIPLY", ramp(d, 0.0, 0.8 * r1, 1.0, 0.0), keep)
    d2, keep2 = shots(*DENTS[:2])                      # large dents: a smooth bowl, the paint stays
    bowl = op("MULTIPLY", ramp(d2, 0.0, DENTS[2], 1.0, 0.0), keep2)
    nrm = N.new("ShaderNodeSeparateXYZ")               # scratches: noise stretched along one axis, kept where that
    L.new(co.outputs["Normal"], nrm.inputs[0])         # axis lies in the surface
    scratch = None
    for k, axis in enumerate("XYZ"):
        s = N.new("ShaderNodeVectorMath")
        s.operation = "MULTIPLY"
        L.new(obj, s.inputs[0])
        s.inputs[1].default_value = [SCRATCH[0] if j == k else 1.0 for j in range(3)]
        streak = ramp(noise(s.outputs[0], SCRATCH[1]), *SCRATCH[2])
        w = op("MULTIPLY", streak, op("POWER", op("SUBTRACT", 1.0, op("ABSOLUTE", nrm.outputs[axis])), 2.0))
        scratch = w if scratch is None else op("MAXIMUM", scratch, w)
    scratch = op("MULTIPLY", scratch, ramp(noise(obj, 0.12), 0.45, 0.65))
    fl = noise(obj, FLAKES[0], 6.0, 0.65)              # flaking paint: off to the primer, in its middle to the metal
    flake, flake_core = ramp(fl, *FLAKES[1]), ramp(fl, *FLAKES[2])
    ch = noise(obj, CHAR[0], 4.0, 0.6)                 # charring: browned paint round black char
    browned, char = ramp(ch, *CHAR[1]), ramp(ch, *CHAR[2])
    soot = ramp(noise(obj, SOOT[0], 3.0), *SOOT[1])
    fade = op("MULTIPLY_ADD", noise(obj, 0.5, 3.0), 0.35, 0.82)

    paint = next(q for q in N if q.type == "MIX")      # the surface's mix of paint and bare metal by its edge wear
    sock = lambda n, ident: next(q for q in n.inputs if q.identifier == ident)
    worn = next(l.from_socket for l in L if l.to_socket == sock(paint, "Factor_Float"))
    users = [l.to_socket for l in L if l.from_socket == worn]
    bare = op("MAXIMUM", op("MAXIMUM", worn, blast), op("MAXIMUM", scratch, flake_core))
    for q in users:                                  # colour, metal and roughness follow the bare metal
        L.new(bare, q)
    base = next(l.from_socket for l in L if l.to_socket == sock(paint, "A_Color"))
    faded = N.new("ShaderNodeVectorMath")
    faded.operation = "SCALE"
    L.new(base, faded.inputs[0])
    L.new(fade, faded.inputs["Scale"])
    L.new(mix(browned, mix(flake, faded.outputs[0], PRIMER), BROWNED), sock(paint, "A_Color"))
    colour = next(l.from_socket for l in L if l.to_socket == b.inputs["Base Color"])
    dark = N.new("ShaderNodeVectorMath")
    dark.operation = "SCALE"
    L.new(colour, dark.inputs[0])
    L.new(op("MULTIPLY", op("MULTIPLY_ADD", soot, -SOOT[2], 1.0), op("MULTIPLY_ADD", burn, -0.8, 1.0)), dark.inputs["Scale"])
    L.new(mix(hole, mix(char, dark.outputs[0], CHARRED), (0.008, 0.007, 0.006)), b.inputs["Base Color"])
    rough = next(l.from_socket for l in L if l.to_socket == b.inputs["Roughness"])
    L.new(op("MAXIMUM", rough, op("MAXIMUM", op("MULTIPLY", char, 0.92), op("MULTIPLY", flake, 0.7))), b.inputs["Roughness"])
    metal = next(l.from_socket for l in L if l.to_socket == b.inputs["Metallic"])
    L.new(op("MULTIPLY", metal, op("SUBTRACT", 1.0, char)), b.inputs["Metallic"])
    normal = next(l.from_socket for l in L if l.to_socket == b.inputs["Normal"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = DENT
    blister = op("MULTIPLY", op("MAXIMUM", browned, char), noise(obj, 4.0, 4.0))
    height = op("ADD", op("ADD", dent, op("MULTIPLY", bowl, 4.0)),
                op("MULTIPLY", op("ADD", op("MAXIMUM", scratch, flake), flake_core), 0.15))
    L.new(op("SUBTRACT", op("MULTIPLY", blister, 0.3), height), bump.inputs["Height"])
    L.new(normal, bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])


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
    return [area[root(f.index)] for f in bm.faces], [root(f.index) for f in bm.faces]


def painted(name, mats):
    """The part as supplied (kit mm, where the kit lays it), decimated, every face given its enamel or machinery."""
    import bmesh
    o = load(name)
    if KEEP < 1:
        d = o.modifiers.new("keep", "DECIMATE")
        d.ratio = KEEP
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="keep")
    for k in SLOTS:
        o.data.materials.append(mats[k])
    bm = bmesh.new()
    bm.from_mesh(o.data)
    area, root = patches(bm)
    slot = SLOTS.index(PAINT[name])
    for f, a in zip(bm.faces, area):
        f.material_index = SLOTS.index("machine") if a < PATCH else slot
    if name == "head":                               # the lenses of the eyes and the two side windows: black glass
        def in_grille(y, z):                         # even-odd rule over the outline's edges
            inside = False
            for (y0, z0), (y1, z1) in zip(GRILLE, GRILLE[1:] + GRILLE[:1]):
                if (z0 > z) != (z1 > z) and y < y0 + (z - z0) * (y1 - y0) / (z1 - z0):
                    inside = not inside
            return inside
        r, z0, z1 = EYE
        for f in bm.faces:
            c = f.calc_center_median()
            if z0 < c.z < z1 and any(math.hypot(c.x - x, c.y - y) < r for x, y in EYES):
                f.material_index = SLOTS.index("eye")
            elif abs(c.x - MID) < GRILLE_DEPTH and in_grille(c.y, c.z):
                f.material_index = SLOTS.index("grille")
        for side in (1, -1):
            seed = Vector((MID + side * (WINDOW[0] - MID), WINDOW[1], WINDOW[2]))
            glass = root[min(bm.faces, key=lambda f: (f.calc_center_median() - seed).length).index]
            for f, q in zip(bm.faces, root):
                if q == glass:
                    f.material_index = SLOTS.index("eye")
    layer = bm.faces.layers.float.new("panel")       # a tone per plate: the patch's area hashed
    for f, a in zip(bm.faces, area):
        f[layer] = 0.85 + 0.3 * ((a * 7919.0) % 1.0)
    pid = bm.faces.layers.int.new("patch")           # the patch of every face, for the charts of the ornament
    for f, r in zip(bm.faces, root):
        f[pid] = r
    bm.to_mesh(o.data)
    bm.free()
    o.data.attributes.active = None
    return o


def split(o, side):
    """The leg cut into its hip arm, thigh and shin: each face goes to the piece whose line (hip to upper knee, upper
    knee to lower knee, lower knee to ankle) its centre lies nearest; the hip wheel goes whole to the hip arm. The
    housings of the knees cover the cuts."""
    import bmesh
    g = LEGS[side]
    pts = [Vector(g["wheel"][1:]), Vector(g["knees"][0]), Vector(g["knees"][1]), Vector(g["ball"][1:])]
    c = np.empty(len(o.data.polygons) * 3, np.float32)
    o.data.polygons.foreach_get("center", c)
    yz = c.reshape(-1, 3)[:, 1:]
    dist = []
    for a, b in zip(pts, pts[1:]):
        a, b = np.array(a), np.array(b)
        t = np.clip(((yz - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
        dist.append(np.linalg.norm(yz - (a + t[:, None] * (b - a)), axis=1))
    label = np.argmin(np.stack(dist, 1), 1)
    label[np.linalg.norm(yz - np.array(pts[0]), axis=1) < 4.6] = 0
    pieces = []
    for k in range(3):
        q = o.copy()
        q.data = o.data.copy()
        q.name = q.data.name = f"leg_{side}.{k}"
        bpy.context.collection.objects.link(q)
        bm = bmesh.new()
        bm.from_mesh(q.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if label[f.index] != k], context="FACES")
        bm.to_mesh(q.data)
        bm.free()
        pieces.append(q)
    bpy.data.objects.remove(o)
    return pieces


def housings(M, mats):
    """Steel housings at the joints: hubs, collars and flanges with bolt heads, each an object that rides the part
    it is fixed to, its mesh in that part's own coordinates (kit mm). Returns {part: object}."""
    import bmesh
    groups = {}
    def drum(owner, slot, centre, axis, radius, depth, segments=32):
        bm = groups.setdefault(owner, bmesh.new())
        first = len(bm.faces)
        q = Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=depth,
                              matrix=Matrix.Translation(Vector(centre)) @ q)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[first:]:
            f.material_index = slot
    def bolted(owner, centre, axis, radius, depth, bolts, face):
        """A disc and a ring of bolt heads on its face that looks along `face` (+1 or -1 along the axis)."""
        axis = Vector(axis).normalized()
        drum(owner, 0, centre, axis, radius, depth)
        u = axis.orthogonal().normalized()
        v = axis.cross(u)
        for k in range(bolts):
            a = math.tau * k / bolts
            p = Vector(centre) + face * axis * (depth / 2 + 0.12) + (radius - 0.45) * (math.cos(a) * u + math.sin(a) * v)
            drum(owner, 1, p, axis, 0.28, 0.25, segments=6)
    hip = Vector((0, HIP[0] + WAIST[1], HIP[1] + WAIST[2]))
    for side, sign in (("left", 1), ("right", -1)):
        inner = LEGS[side]["side"] + WAIST[0]
        outer = inner + sign * 8.32                    # the outer face of the leg's wheel
        bolted("waist", (outer + sign * 0.4, hip.y, hip.z), (1, 0, 0), 4.3, 0.8, 12, sign)        # flange
        drum("waist", 0, (outer + sign * 1.2, hip.y, hip.z), (1, 0, 0), 2.6, 1.2)                # hub
        bolted("waist", (outer + sign * 1.9, hip.y, hip.z), (1, 0, 0), 2.0, 0.3, 6, sign)        # hub cap
        for k in (0.25, 0.5, 0.75):                                                              # ribs round the wheel
            drum("waist", 0, (inner + sign * 8.32 * k, hip.y, hip.z), (1, 0, 0), 4.15, 0.35)
        sh = Vector(SHOULDER[side])
        bolted("body", M["body"] @ (sh - Vector((sign * 1.6, 0, 0))), M["body"].to_3x3() @ Vector((1, 0, 0)), 3.4, 1.0, 10, sign)   # shoulder collar
        g = LEGS[side]
        for k, (y, z) in enumerate(g["knees"]):                                                  # knee hubs on both flat sides
            m = M[f"leg_{side}.{k + 1}"]
            for x, face in ((g["faces"][0] - 0.3, -1), (g["faces"][1] + 0.3, 1)):
                bolted(f"leg_{side}.{k + 1}", m @ Vector((x, y, z)), m.to_3x3() @ Vector((1, 0, 0)), 1.9, 0.6, 6, face)
        ball = M[f"leg_{side}.2"] @ Vector(g["ball"])
        rim = M["foot_" + side] @ (Vector(CUPS["foot_" + side]) + Vector((0, 0, 2.9)))
        bolted("foot_" + side, rim, (0, 0, 1), 4.0, 1.2, 10, 1)                                  # ankle collar
        bolted(f"leg_{side}.2", ball + Vector((0, 0, 3.0)), (0, 0, 1), 2.4, 1.6, 6, 1)           # its gland round the shin
    bolted("waist", (-4.3, 55.7, 45.4), (0, 0, 1), 4.6, 0.8, 14, -1)                            # waist ring
    bolted("body", M["body"] @ Vector((-4.28, 34.4, 54.22)), M["body"].to_3x3() @ Vector((0, 1, 0)), 3.7, 0.9, 10, -1)   # neck collar
    out = {}
    for owner, bm in groups.items():
        bm.transform(M[owner].inverted())            # into the part's own coordinates
        me = bpy.data.meshes.new("joints_" + owner)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("joints_" + owner, me)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(mats["steel"])
        o.data.materials.append(mats["bolt"])
        out[owner] = o
    return out


def _pack(sizes, side):
    """Shelves: the charts from the tallest down, left to right in rows; their corners, or None when they do not fit."""
    order = sorted(range(len(sizes)), key=lambda k: -sizes[k][1])
    at, x, y, row = [None] * len(sizes), 0, 0, 0
    for k in order:
        w, h = sizes[k]
        if x + w > side:
            x, y, row = 0, y + row, 0
        if w > side or y + h > side:
            return None
        at[k], x, row = (x, y), x + w, max(row, h)
    return at


def plating(parts, M):
    """The armour plates of the parts in ORNATE as flat charts in one atlas, the layout of
    mech-design/src/procession/plating.py: each plate (a flat patch of red or bone of at least CHART_AREA) drawn in
    its own plane, `up` the titan's up laid into it, in metres of the 16 m titan. M: the parts' motions in the pose
    the charts are made in, always POSE, so the layout does not change with the scene's pose. Writes the UV layer
    `plate` and gives every charted face the armour slot. Returns the arrays src/warhoundlivery.py draws from."""
    import bmesh
    charts = []
    for part, o in parts:
        if part not in ORNATE:
            continue
        m = M[part]
        R = m.to_3x3()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        pid = bm.faces.layers.int["patch"]
        groups = {}
        for f in bm.faces:
            if f.material_index in (SLOTS.index("red"), SLOTS.index("bone")):
                groups.setdefault(f[pid], []).append(f)
        for faces in groups.values():
            a = sum(f.calc_area() for f in faces) * SCALE ** 2
            if a < CHART_AREA:
                continue
            n = sum((R @ f.normal * f.calc_area() for f in faces), Vector()).normalized()
            c = sum(((m @ f.calc_center_median()) * f.calc_area() for f in faces), Vector()) * SCALE ** 3 / a   # metres
            curved = any((R @ f.normal).angle(n, 0.0) > BEND for f in faces)
            up = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((0, -1, 0))
            up = (up - up.dot(n) * n).normalized()
            right = up.cross(n)
            tri = np.array([[((m @ l.vert.co) * SCALE).dot(right), ((m @ l.vert.co) * SCALE).dot(up)] for f in faces
                            for l in f.loops[:3]], np.float64).reshape(-1, 3, 2)
            charts.append(dict(part=part, faces=[f.index for f in faces], n=n, c=c, area=a, curved=curved, tri=tri,
                               klass=PAINT[part], up=up, right=right, lo=tri.reshape(-1, 2).min(0),
                               size=np.ptp(tri.reshape(-1, 2), 0)))
        bm.free()
    lo_d, hi_d = 10.0, 2000.0
    for _ in range(24):                                # the largest density at which all charts fit
        d = (lo_d + hi_d) / 2
        fits = _pack([(int(math.ceil(ch["size"][0] * d)) + 2 * MARGIN, int(math.ceil(ch["size"][1] * d)) + 2 * MARGIN) for ch in charts], ATLAS)
        lo_d, hi_d = (d, hi_d) if fits else (lo_d, d)
    density = lo_d
    at = _pack([(int(math.ceil(ch["size"][0] * density)) + 2 * MARGIN, int(math.ceil(ch["size"][1] * density)) + 2 * MARGIN) for ch in charts], ATLAS)
    by_part = {}
    for ch, (x, y) in zip(charts, at):
        ch["at"] = (x + MARGIN, y + MARGIN)            # the chart's lowest corner; row 0 is the bottom
        by_part.setdefault(ch["part"], []).append(ch)
    for part, o in parts:
        if part not in by_part:
            continue
        me = o.data
        uv = me.uv_layers.new(name="plate")
        loops = np.zeros((len(me.loops), 2), np.float32)
        mat = np.array([p.material_index for p in me.polygons])
        for ch in by_part[part]:
            for fi, t in zip(ch["faces"], ch["tri"]):
                p = me.polygons[fi]
                q = (t - ch["lo"]) * density + ch["at"]
                for k, li in enumerate(p.loop_indices[:3]):
                    loops[li] = q[k] / ATLAS
                mat[fi] = SLOTS.index("armour")
        uv.data.foreach_set("uv", loops.ravel())
        me.polygons.foreach_set("material_index", mat)
        me.update()
    flip = np.array([1, -1, 1])                        # ornament.py's mechs face +y; the titan faces -y
    classes = ["bone", "red"]
    print(f"PLATING warhound: {len(charts)} charts ({sum(ch['curved'] for ch in charts)} curved), "
          f"{sum(ch['area'] for ch in charts):.0f} m2, {density:.0f} px per metre in {ATLAS} px")
    return dict(density=density, side=ATLAS, classes=np.array(classes),
                at=np.array([ch["at"] for ch in charts], np.int32),
                size=np.array([np.ceil(ch["size"] * density) for ch in charts], np.int32),
                lo=np.array([ch["lo"] for ch in charts]), n=np.array([np.array(ch["n"]) * flip for ch in charts]),
                c=np.array([(np.array(ch["c"]) - np.array([-4.3, 50.0, 0.0]) * SCALE) * flip for ch in charts]),
                up=np.array([np.array(ch["up"]) for ch in charts]), area=np.array([ch["area"] for ch in charts]),
                curved=np.array([ch["curved"] for ch in charts]),
                klass=np.array([classes.index(ch["klass"]) for ch in charts], np.int32),
                tri=np.concatenate([(ch["tri"] - ch["lo"]) * density + ch["at"] for ch in charts]).astype(np.float32),
                tri_chart=np.concatenate([np.full(len(ch["tri"]), k, np.int32) for k, ch in enumerate(charts)]))


def model(pose=POSE):
    """The painted Warhound in `pose`, with its housings, every part an object of its own parented to an empty
    `warhound` at its feet: metres, facing -y. Returns the empty, the objects, and place(pose), which moves the
    torso, head and guns to another pose (the legs stay as they stand)."""
    mats = materials()
    lg = legs(pose)
    M = assemble(pose, lg)
    parts = []                                       # (part, object)
    for name in M:
        if name.endswith((".1", ".2")):
            continue
        if name.endswith(".0"):
            side = name.split("_")[1].split(".")[0]
            parts += [(f"leg_{side}.{k}", q) for k, q in enumerate(split(painted("leg_" + side, mats), side))]
        else:
            parts.append((name, painted(name, mats)))
    info = plating(parts, M if pose is POSE else assemble(POSE, legs(POSE)))
    parts += list(housings(M, mats).items())
    lo = float("inf")
    for part, o in parts:
        co = np.empty(len(o.data.vertices) * 3, np.float32)
        o.data.vertices.foreach_get("co", co)
        m = np.array(M[part])
        lo = min(lo, float((co.reshape(-1, 3) @ m[2, :3] + m[2, 3]).min()))
    base = Matrix.Scale(SCALE, 4) @ Matrix.Translation(-Vector((-4.3, 50.0, lo)))
    root = bpy.data.objects.new("warhound", None)
    bpy.context.collection.objects.link(root)
    for part, o in parts:
        o.parent = root
        o.matrix_basis = base @ M[part]

    def place(p):
        M2 = assemble(p, lg)
        for part, o in parts:
            o.matrix_basis = base @ M2[part]

    bpy.context.view_layer.update()
    model.plating = info
    return root, [o for _, o in parts], place


def plating_file():
    """The charts of the armour for src/warhoundlivery.py: wip/warhound/warhound.npz."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    model()
    os.makedirs(os.path.dirname(PLATING), exist_ok=True)
    np.savez_compressed(PLATING, **model.plating)
    print("PLATING_DONE", PLATING)


def lookdev(stem="warhound-look", pose=POSE):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    root, obs, _ = model(pose)
    s = bpy.context.scene
    setup(samples=64)
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.37, 0.40, 1)
    s.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    views(obs, stem, [("side", (1, 0, 0), (0, 0, 1)), ("front", (0, -1, 0), (0, 0, 1)), ("iso", (1, -1, 0.5), (0, 0, 1)),
                      ("back", (-1, 1, 0.4), (0, 0, 1))])


def build(only=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = {n.split(".")[0]: m for n, m in assemble().items() if not n.endswith((".1", ".2"))}
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
    {"kit": lambda: kit(), "parts": lambda: parts(args[1], args[2:]), "build": lambda: build(args[1:] or None), "lookdev": lambda: lookdev(*args[1:2], **({"pose": {**POSE, **json.loads(args[2])}} if len(args) > 2 else {})),
     "plating": lambda: plating_file()}[args[0]]()
