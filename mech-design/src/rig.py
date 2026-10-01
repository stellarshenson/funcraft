"""Armature for a painted BattleMech - the skeleton the walk drives. Blender 4.5.

The mesh stays whole. It is skinned to the armature through vertex groups, so
the paint and the glass on its faces move with it and nothing is cut open.

Bones, in model space (facing +Y, feet on z = 0):

    root                 placement - location and heading in the scene
      body               deform: everything above the hips
        thigh.L/R        deform: hip → knee
          shin.L/R       deform: knee → ankle, IK chain of two to ik.L/R
            foot.L/R     deform: ankle → toe, copies ik.L/R's rotation, so the
                         sole keeps whatever angle the controller has
        pole.L/R         the direction the knee points: in front for a
                         humanoid knee, behind for the Mad Cat's reverse knee
      ik.L/R             foot controller - the walk moves these

L is the -x side, R the +x side.

Joint positions are (y, z) pairs read off orthographic side renders of each
leg with a half-unit grid, and x is the measured centre of each leg's shin.
The BattleMaster is modelled mid-stride, so its two legs have their own joints;
they are read after its lower body is turned into line with the torso
(mechrig.untwist), and its hips share one point so both thighs are one length.
"""

import bpy, math
import numpy as np
from mathutils import Vector, Matrix

JOINTS = {
    "madcat": dict(
        x={"L": -1.95, "R": 1.95}, pole=-1.0, corridor=(0.9, 3.3), split=6.9,
        L=dict(hip=(-0.92, 6.62), knee=(-0.90, 3.80), ankle=(0.00, 1.00), toe=(2.20, 0.15)),
        R=dict(hip=(-0.92, 6.62), knee=(-0.90, 3.80), ankle=(0.00, 1.00), toe=(2.20, 0.15)),
    ),
    "atlas": dict(
        x={"L": -2.12, "R": 2.12}, pole=1.0, corridor=(0.45, 3.35), split=6.9,
        L=dict(hip=(-0.45, 6.90), knee=(-0.10, 4.50), ankle=(-0.94, 1.02), toe=(1.70, 0.15)),
        R=dict(hip=(-0.45, 6.90), knee=(-0.10, 4.50), ankle=(-0.94, 1.02), toe=(1.70, 0.15)),
    ),
    "battlemaster": dict(
        x={"L": -1.88, "R": 2.13}, pole=1.0, corridor=(0.8, 3.05), split=7.1,
        L=dict(hip=(-1.00, 6.40), knee=(-1.35, 4.20), ankle=(-2.75, 1.10), toe=(-0.60, 0.15)),
        R=dict(hip=(-1.00, 6.40), knee=(0.30, 4.60), ankle=(0.00, 1.10), toe=(2.20, 0.15)),
    ),
}

HIP_BAND = 0.15      # half-width of the body → leg blend at `split`, model units
ANKLE_BAND = 0.08    # margin above the ankle still counted as foot territory
KNEE_TAU = 0.06      # softness of the split between leg bones, by distance
REACH = 2.2          # a vertex further than this from every leg bone is body


def joints(name, side):
    J = JOINTS[name]
    x = J["x"][side]
    return {k: Vector((x, *J[side][k])) for k in ("hip", "knee", "ankle", "toe")}


def _roll_to_x(eb):
    """Point the bone's local X along world X, so every leg bone bends about X."""
    d = (eb.tail - eb.head).normalized()
    eb.align_roll(Vector((1, 0, 0)).cross(d))


def _seg_dist(p, a, b):
    """Distance from each row of `p` to the segment a-b."""
    a, b = np.asarray(a), np.asarray(b)
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0.0, 1.0)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _components(edges, keep):
    """Label the connected pieces of the vertices in `keep`, through mesh edges."""
    lab = np.arange(len(keep))
    e = edges[keep[edges[:, 0]] & keep[edges[:, 1]]]
    while True:
        new = lab.copy()
        m = np.minimum(lab[e[:, 0]], lab[e[:, 1]])
        np.minimum.at(new, e[:, 0], m)
        np.minimum.at(new, e[:, 1], m)
        new = new[new]
        if np.array_equal(new, lab):
            return lab
        lab = new


def skin_weights(name, co, edges):
    """Per-vertex weights for body, thigh, shin and foot on each side.

    Which vertices are leg at all:

      - A separate piece of the mesh that never reaches the feet and rises a
        unit past the hips is body, whole - the Atlas's torso shell, whose
        groin hangs into the leg corridor. So is a piece that sits entirely
        at hip height or above - the Atlas's hip connectors.
      - A separate piece that stays below the body line and inside the leg
        corridor is leg, whole - the Atlas's legs, which rise past the hip
        pivot and would be cut there by a height rule.
      - In a single shell holding everything (the Mad Cat, the BattleMaster),
        a vertex is leg below the body line `split`, inside the corridor in x
        and within REACH of the bones - or anywhere at all below the ankle,
        where splayed toes and heels reach past both limits. `split` is the
        underside of the torso, not the hip pivot: thigh armour rises above
        the pivot and must turn with the thigh.

    Which leg: the nearer one, decided per connected piece below the body
    line, because the inner edge of one BattleMaster foot is nearer the other
    leg's bones than its own.

    Which bone inside a leg: the nearest of thigh, shin and foot, blended
    softly where two are nearly equal - that is, only at a joint. Distance to
    the foot is penalised above the ankle, so the bottom of the Mad Cat's calf
    stays with the shin; distance to the thigh is penalised below the knee, so
    a knee plate hanging in front of the shin stays with the shin.
    """
    J = JOINTS[name]
    x_in, x_out = J["corridor"]
    split = J["split"]
    ax, z = np.abs(co[:, 0]), co[:, 2]
    hip_z = min(joints(name, s)["hip"].z for s in "LR")
    ankle_z = max(joints(name, s)["ankle"].z for s in "LR")

    d = {}
    for s in "LR":
        P = {k: np.array(v) for k, v in joints(name, s).items()}
        heel = P["ankle"] + (P["ankle"] - P["toe"]) * 0.8
        heel[2] = P["toe"][2]
        d[s] = dict(
            thigh=_seg_dist(co, P["hip"], P["knee"]) + np.maximum(0.0, P["knee"][2] - z),
            shin=_seg_dist(co, P["knee"], P["ankle"]),
            foot=np.minimum(_seg_dist(co, P["ankle"], P["toe"]), _seg_dist(co, P["ankle"], heel))
                 + 2.0 * np.maximum(0.0, z - P["ankle"][2]),
        )
        d[s]["min"] = np.minimum(np.minimum(d[s]["thigh"], d[s]["shin"]), d[s]["foot"])

    # which leg, per connected piece below the body line
    near_L = d["L"]["min"] <= d["R"]["min"]
    low = z < split - HIP_BAND
    lab = _components(edges, low)
    share = np.bincount(lab[low], weights=near_L[low], minlength=len(co))
    size = np.bincount(lab[low], minlength=len(co))
    frac = share[lab] / np.maximum(size[lab], 1)
    near_L = np.where(low & (frac > 0.6), True, np.where(low & (frac < 0.4), False, near_L))

    # whole separate pieces
    piece = _components(edges, np.ones(len(co), bool))
    zmin = np.full(len(co), np.inf); np.minimum.at(zmin, piece, z)
    zmax = np.full(len(co), -np.inf); np.maximum.at(zmax, piece, z)
    stray = ((ax <= x_in) | (ax >= x_out)) & (z > ankle_z)
    out = np.zeros(len(co)); np.maximum.at(out, piece, stray.astype(float))
    zmin, zmax, out = zmin[piece], zmax[piece], out[piece]
    body_piece = (zmin > hip_z - 0.3) | ((zmax > hip_z + 1.0) & (zmin > ankle_z))
    leg_piece = ~body_piece & (zmax < split + 0.8) & (out == 0)
    pL = np.bincount(piece, weights=near_L, minlength=len(co))
    pN = np.bincount(piece, minlength=len(co))
    near_L = np.where(leg_piece, (pL / np.maximum(pN, 1))[piece] >= 0.5, near_L)

    W = {"body": np.ones(len(co))}
    for s in "LR":
        side = near_L if s == "L" else ~near_L
        reach = ((ax > x_in) & (ax < x_out) & (d[s]["min"] < REACH)) | (z < ankle_z + ANKLE_BAND)
        leg = _smooth((split + HIP_BAND - z) / (2 * HIP_BAND)) * reach
        leg = np.where(leg_piece, 1.0, np.where(body_piece, 0.0, leg)) * side
        e = {b: np.exp(-np.minimum((d[s][b] - d[s]["min"]) / KNEE_TAU, 50.0))
             for b in ("thigh", "shin", "foot")}
        tot = e["thigh"] + e["shin"] + e["foot"]
        for b in ("thigh", "shin", "foot"):
            W[f"{b}.{s}"] = leg * e[b] / tot
        W["body"] -= leg
    return W


def build(mesh, name):
    """Add the armature, skin `mesh` to it, and return the rig object."""
    J = JOINTS[name]
    arm = bpy.data.armatures.new(f"{name}_rig")
    rig = bpy.data.objects.new(f"{name}_rig", arm)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones

    root = eb.new("root")
    root.head, root.tail = (0, 0, 0), (0, 1.5, 0)
    hip = (joints(name, "L")["hip"] + joints(name, "R")["hip"]) / 2
    body = eb.new("body")
    body.head, body.tail = (0, hip.y, hip.z), (0, hip.y, hip.z + 1.5)
    body.parent = root

    for s in "LR":
        P = joints(name, s)
        th = eb.new(f"thigh.{s}")
        th.head, th.tail, th.parent = P["hip"], P["knee"], body
        sh = eb.new(f"shin.{s}")
        sh.head, sh.tail, sh.parent, sh.use_connect = P["knee"], P["ankle"], th, True
        ft = eb.new(f"foot.{s}")
        ft.head, ft.tail, ft.parent, ft.use_connect = P["ankle"], P["toe"], sh, True
        ik = eb.new(f"ik.{s}")
        ik.head, ik.tail, ik.parent, ik.use_deform = P["ankle"], P["toe"], root, False
        pole = eb.new(f"pole.{s}")
        pole.head = P["knee"] + Vector((0, J["pole"] * 4.0, 0))
        pole.tail = pole.head + Vector((0, 0, 0.6))
        pole.parent, pole.use_deform = body, False
        for b in (th, sh, ft, ik):
            _roll_to_x(b)
    bpy.ops.object.mode_set(mode="POSE")

    pb = rig.pose.bones
    for s in "LR":
        c = pb[f"shin.{s}"].constraints.new("IK")
        c.target, c.subtarget = rig, f"ik.{s}"
        c.pole_target, c.pole_subtarget = rig, f"pole.{s}"
        c.chain_count = 2
        c.pole_angle = _fit_pole(rig, s)
        r = pb[f"foot.{s}"].constraints.new("COPY_ROTATION")
        r.target, r.subtarget = rig, f"ik.{s}"
    bpy.ops.object.mode_set(mode="OBJECT")

    # skin
    co = np.empty(len(mesh.data.vertices) * 3)
    mesh.data.vertices.foreach_get("co", co)
    ed = np.empty(len(mesh.data.edges) * 2, dtype=np.int64)
    mesh.data.edges.foreach_get("vertices", ed)
    W = skin_weights(name, co.reshape(-1, 3), ed.reshape(-1, 2))
    for g, w in W.items():
        vg = mesh.vertex_groups.new(name=g)
        q = np.round(w, 2)
        for val in np.unique(q[q > 0.005]):
            vg.add(np.nonzero(q == val)[0].tolist(), float(val), "REPLACE")
    mesh.parent = rig
    mod = mesh.modifiers.new("rig", "ARMATURE")
    mod.object = rig

    for s in "LR":
        err = (rig.matrix_world @ pb[f"shin.{s}"].tail - rig.matrix_world @ joints(name, s)["ankle"]).length
        knee = (pb[f"thigh.{s}"].tail - joints(name, s)["knee"]).length
        print(f"RIG {name} {s}: pole {math.degrees(pb[f'shin.{s}'].constraints[0].pole_angle):.1f} deg, "
              f"ankle error {err:.4f}, knee error {knee:.4f}")
    return rig


def _fit_pole(rig, s):
    """The pole angle that leaves the rest pose where it is.

    Blender's pole angle depends on each bone's roll, so instead of deriving
    it, try angles and keep the one that puts the knee back on its rest spot.
    """
    pb = rig.pose.bones
    c = pb[f"shin.{s}"].constraints[-1]
    rest = rig.data.bones[f"thigh.{s}"].tail_local.copy()

    def err(a):
        c.pole_angle = a
        bpy.context.view_layer.update()
        return (pb[f"thigh.{s}"].tail - rest).length

    best = min((math.radians(a) for a in range(-180, 180, 5)), key=err)
    for step in (1.0, 0.2, 0.05):
        best = min((best + math.radians(k * step) for k in range(-5, 6)), key=err)
    err(best)
    return best


def place(rig, bone, head):
    """Move a controller bone so its head sits at `head`, in armature space."""
    pb = rig.pose.bones[bone]
    m = pb.bone.matrix_local.copy()
    m.translation = head
    pb.matrix = m


def turn(rig, bone, head, pitch):
    """Place a controller and tilt it about X by `pitch` radians."""
    pb = rig.pose.bones[bone]
    m = Matrix.Rotation(pitch, 4, "X") @ pb.bone.matrix_local.to_3x3().to_4x4()
    m.translation = head
    pb.matrix = m


# ------------------------------------------------------------------- walk ---
def walk(rig, name, phase, stride, duty=0.6, lift=0.8, toe=0.14, sway=0.12, nod=0.015, bob=0.12):
    """Pose one frame of the walk from the controllers alone.

    Every quantity is a function of `phase` in [0, 1), so phase 1.0 poses
    exactly like phase 0.0 and the loop closes.

    A planted foot slides backward in a straight line at `stride` per cycle -
    the speed the floor moves under the mech - so it stays locked to the
    floor. A swinging foot eases forward, lifts on an arch, and pitches toe
    down as it leaves and toe up before it lands, never dipping below the
    floor. The hips sit as low as the more stretched leg needs, which gives
    the body its bob, and shift a little over the planted foot.
    """
    sweep = stride * duty
    hip = (joints(name, "L")["hip"] + joints(name, "R")["hip"]) / 2
    feet, drop = {}, 0.0
    for s, off in (("L", 0.0), ("R", 0.5)):
        P = joints(name, s)
        L = (P["knee"] - P["hip"]).length + (P["ankle"] - P["knee"]).length
        toe_len = (P["toe"] - P["ankle"]).length
        p = (phase + off) % 1.0
        if p < duty:
            t = p / duty
            dy, dz, pitch = sweep * (0.5 - t), 0.0, 0.0
        else:
            t = (p - duty) / (1.0 - duty)
            dy = sweep * (0.5 - 0.5 * math.cos(math.pi * t) - 0.5)
            pitch = -toe * math.sin(2 * math.pi * t)
            dz = max(lift * math.sin(math.pi * t),
                     toe_len * max(0.0, -math.sin(pitch)),
                     0.8 * toe_len * max(0.0, math.sin(pitch)))
        y = hip.y + 0.3 + dy
        reach = math.sqrt(max((0.95 * L) ** 2 - (y - P["hip"].y) ** 2, 0.0))
        drop = max(drop, (P["hip"].z - (P["ankle"].z + dz)) - reach)
        feet[s] = (Vector((P["ankle"].x, y, P["ankle"].z + dz)), pitch)

    # left mid-stance falls at phase 0.3, right at 0.8; double support at 0.05
    # and 0.55, where the body also sits lowest
    drop += bob * 0.5 * (1 + math.cos(4 * math.pi * (phase - 0.05)))
    body0 = rig.data.bones["body"].head_local
    shift = sway * math.cos(2 * math.pi * (phase - 0.3))  # + moves towards the left foot
    turn(rig, "body", body0 + Vector((-shift, 0, -drop)), nod * math.sin(4 * math.pi * phase))
    for s, (head, pitch) in feet.items():
        turn(rig, f"ik.{s}", head, pitch)
    bpy.context.view_layer.update()
