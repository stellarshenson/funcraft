"""The walk of the procession's mechs, on the armature of src/rig.py: the
places of its controllers (the body and the two foot targets) as functions
of the gait phase. It takes the place of rig.walk, which banners 03 to 05
keep. Blender 4.5.

There are two walks, and the knee of a chassis decides which one it has.

The bird walk, for a knee that points back (BIRD: Mad Cat, Marauder). The
front of the foot touches the ground first and leaves it last:

    landing   the toes touch, with the foot pitched toe down, and the foot
              rolls down flat after them: this takes the shock
    stance    the foot lies flat and moves back at the speed of the ground;
              the legs give under the load, so the body is lowest over a
              standing leg
    roll-off  the heel rises while the toes still stand
    swing     the toes leave the ground, the foot hangs its front down, and
              the leg carries it high and forward to the next landing

The march, for a knee that points forward (MARCH: Atlas, BattleMaster). The
heel touches the ground first and the toes leave it last:

    landing   the heel touches on a leg that reaches forward, with the toes
              up, and the foot rolls down flat about the heel
    stance    the foot lies flat and moves back at the speed of the ground;
              the leg stays long, so the body rises over a standing leg and
              sinks between two steps
    roll-off  the heel rises a little while the toes still stand
    swing     the foot leaves the ground nearly level, comes forward, and
              its toes go up for the next landing of the heel. It never
              points its toes at the ground, which the bird's foot does

`_bird` holds its walk as the path of the toe tip and the pitch of the
foot. `_march` holds its walk as the heights of the toe tip and of the heel
and the path of the point of the sole that leads: the heel at the landing,
the toe tip at the roll-off, in the swing a point that goes from the one to
the other. The ankle, which the armature's controller is, follows from them.
A point of the sole that stands moves back in a straight line at the speed
of the ground; every curve leaves and meets the ground with that speed and
without a kink. So no speed of a foot jumps, which is what makes a walk
fluid.

The body sits lower than at rest by one fixed amount, `crouch`: as much as
the longest reach of a leg needs. From there it rises or sinks twice per
cycle and shifts over the standing foot. Nothing in its height switches
between the legs.

BIRD and MARCH give each chassis its numbers. The length of ground that one
foot stands on is `duty` times the ground's travel per gait cycle
(frame.STEP), which all mechs share.

    blender -b -P src/procession/gait.py -- <chassis>     # wip/procession/skeleton-<chassis>.json: the armature's joints through a gait cycle
    python3 src/procession/skeleton.py <chassis>          # draws them: wip/preview/procession/skeleton-<chassis>.png and .avif
"""
import bpy, os, sys, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F

R = F.mechwalk
# For both walks. duty: the share of a gait cycle that a foot stands; down, off: the shares of the cycle in which
# the foot rolls down flat after it lands and rolls off before it leaves; heel: metres from the ankle back to the
# heel's end of the sole; ahead: metres in front of the hip at which a flat foot's ankle is in mid-stance; sway:
# metres the body shifts over the standing foot; rise: metres the body is higher over
# a standing leg than between two steps (negative: lower); turn: degrees the pelvis turns the side of the leading
# leg forward (src/procession/hips.py)
# land, peel: degrees of toe-down pitch at the landing and at its largest in the swing; lift: metres the toe tip rises
BIRD = {
    "madcat": dict(duty=0.66, down=0.10, off=0.16, land=26.0, peel=50.0, lift=0.6, heel=2.49, ahead=0.3, sway=0.18, rise=-0.14, turn=5.0),
    "marauder": dict(duty=0.66, down=0.10, off=0.16, land=26.0, peel=50.0, lift=0.6, heel=2.47, ahead=0.3, sway=0.18, rise=-0.14, turn=5.0),
}
# strike: degrees of toe-up pitch when the heel lands; push: degrees of toe-down pitch when the toes leave
MARCH = {
    "atlas": dict(duty=0.62, down=0.08, off=0.14, strike=12.0, push=7.0, heel=1.50, ahead=0.0, sway=0.20, rise=0.30, turn=4.0),
    "battlemaster": dict(duty=0.62, down=0.08, off=0.14, strike=10.0, push=6.0, heel=1.48, ahead=0.0, sway=0.18, rise=0.26, turn=3.0),
}
GAIT = {**BIRD, **MARCH}
NOD = 0.015                        # radians that the body nods
STRAIGHT = 0.97                    # a leg is never longer than this share of its full length
_CROUCH = {}


def _cubic(t, y0, m0, y1, m1):
    """The cubic through y0 at t = 0 and y1 at t = 1 with the slopes m0 and m1 there."""
    return (2 * t ** 3 - 3 * t ** 2 + 1) * y0 + (t ** 3 - 2 * t ** 2 + t) * m0 + (-2 * t ** 3 + 3 * t ** 2) * y1 + (t ** 3 - t ** 2) * m1


def _pitch(G, p):
    """Degrees of toe-down pitch of a bird's foot at the phase `p` of its own cycle (0: its toes land)."""
    duty, land, peel = G["duty"], G["land"], G["peel"]
    leave = 0.7 * peel                                     # the pitch when the toes leave
    top = duty + 0.4 * (1.0 - duty)                        # where the pitch is largest
    fall, climb = -1.5 * land / G["down"], 1.5 * leave / G["off"]     # slopes, per unit of p
    knots = [(0.0, land, fall), (G["down"], 0.0, 0.0), (duty - G["off"], 0.0, 0.0), (duty, leave, climb), (top, peel, 0.0), (1.0, land, fall)]
    for (p0, y0, m0), (p1, y1, m1) in zip(knots, knots[1:]):
        if p <= p1:
            return _cubic((p - p0) / (p1 - p0), y0, m0 * (p1 - p0), y1, m1 * (p1 - p0))
    return land


def _ankle(P, toe_y, toe_z, b):
    """The ankle of a foot whose toe tip is `toe_y` forward of the mid-stance
    ankle and `toe_z` above its standing height, pitched toe down by `b`
    radians: forward, up, and the controller's pitch."""
    v = P["toe"] - P["ankle"]
    long, flat = math.hypot(v.y, v.z), math.atan2(-v.z, v.y)        # the foot from ankle to toe tip: length, angle below level
    return toe_y - long * math.cos(flat + b), toe_z + long * (math.sin(flat + b) - math.sin(flat)), -b


def _bird(G, P, p, stride):
    duty = G["duty"]
    toe = (P["toe"] - P["ankle"]).y                        # the toe tip of a flat foot, forward of its ankle
    if p < duty:                                           # the toe tip stands
        y, z = toe + stride * (duty / 2 - p), 0.0
    else:
        t = (p - duty) / (1.0 - duty)
        m = -stride * (1.0 - duty)                         # the ground's speed, per unit of t
        y = toe + _cubic(t, -stride * duty / 2, m, stride * duty / 2, m)
        z = G["lift"] * math.sin(math.pi * t) ** 2
    return _ankle(P, y, z, math.radians(_pitch(G, p)))


def _march(G, P, p, stride):
    duty, down, off = G["duty"], G["down"], G["off"]
    toe = (P["toe"] - P["ankle"]).y
    sole = G["heel"] + toe                                 # from the heel's end to the toe tip
    up, back = sole * math.sin(math.radians(G["strike"])), sole * math.sin(math.radians(G["push"]))    # the toe tip's height at the landing, the heel's at the roll-off
    drop, climb = up / down, back / off                    # how fast the toe tip comes down after the landing and the heel rises before the toes leave, per unit of p
    if p < duty:
        lead = 1.0 if p < down else 0.0                    # the point of the sole that stands: 1 the heel, 0 the toe tip; a flat foot stands on both
        y = toe - lead * sole + stride * (duty / 2 - p)
        t_z = _cubic(p / down, up, -drop * down, 0.0, 0.0) if p < down else 0.0
        h_z = _cubic((p - duty + off) / off, 0.0, 0.0, back, climb * off) if p > duty - off else 0.0
    else:
        t = (p - duty) / (1.0 - duty)
        lead = t * t * (3.0 - 2.0 * t)
        m = -stride * (1.0 - duty)                         # the ground's speed, per unit of t
        y = _cubic(t, toe - stride * duty / 2, m, toe - sole + stride * duty / 2, m)
        t_z = _cubic(t, 0.0, 0.0, up, -drop * (1.0 - duty))
        h_z = _cubic(t, back, climb * (1.0 - duty), 0.0, 0.0)
    b = math.asin((h_z - t_z) / sole)
    return _ankle(P, y + lead * sole * math.cos(b), t_z, b)


def foot(name, side, p, stride):
    """Where the ankle of one leg is at the phase `p` of its own cycle (0: the
    foot lands): metres forward of its mid-stance place, metres above its
    height on a flat standing foot, and the foot's pitch in radians (toe
    down is negative)."""
    P = R.joints(name, side)
    return _bird(BIRD[name], P, p, stride) if name in BIRD else _march(MARCH[name], P, p, stride)


def _rise(name, phase):
    G = GAIT[name]
    return G["rise"] * 0.5 * (1.0 - math.cos(4 * math.pi * (phase - (G["duty"] - 0.5) / 2)))   # none between two steps


def _need(name, phase, stride):
    """How much lower than at rest the hips must sit at `phase` for both legs to reach their feet."""
    need = -1e9
    for side, off in (("L", 0.0), ("R", 0.5)):
        P = R.joints(name, side)
        full = (P["knee"] - P["hip"]).length + (P["ankle"] - P["knee"]).length
        y, z, _ = foot(name, side, (phase + off) % 1.0, stride)
        reach = math.sqrt(max((STRAIGHT * full) ** 2 - (GAIT[name]["ahead"] + y) ** 2, 0.0))
        need = max(need, P["hip"].z - (P["ankle"].z + z) - reach)
    return need


def crouch(name, stride):
    """The fixed amount by which the body sits lower than at rest."""
    if (name, stride) not in _CROUCH:
        _CROUCH[name, stride] = max(0.0, max(_need(name, k / 400, stride) + _rise(name, k / 400) for k in range(400)))
    return _CROUCH[name, stride]


def walk(rig, name, phase, stride):
    """Pose the controllers of `rig` for the gait phase `phase` (0..1; the
    left foot lands at 0). `stride`: the ground's travel per gait cycle."""
    G = GAIT[name]
    hip = (R.joints(name, "L")["hip"] + R.joints(name, "R")["hip"]) / 2
    for side, off in (("L", 0.0), ("R", 0.5)):
        P = R.joints(name, side)
        y, z, pitch = foot(name, side, (phase + off) % 1.0, stride)
        R.turn(rig, f"ik.{side}", Vector((P["ankle"].x, hip.y + G["ahead"] + y, P["ankle"].z + z)), pitch)
    shift = G["sway"] * math.cos(2 * math.pi * (phase - G["duty"] / 2))        # + moves towards the left foot
    drop = crouch(name, stride) - _rise(name, phase)
    R.turn(rig, "body", rig.data.bones["body"].head_local + Vector((-shift, 0, -drop)), NOD * math.sin(4 * math.pi * phase))
    bpy.context.view_layer.update()


if __name__ == "__main__":
    # the armature alone: the ends of its leg bones and the body at every frame of a gait cycle, for src/procession/skeleton.py
    import json
    argv = sys.argv[sys.argv.index("--") + 1:]
    name = argv[0]
    F.HIP_ROCK = float(argv[1]) if len(argv) > 1 else 4.5
    F.mechrig.clear_scene()
    mesh = F.load(name)
    rig = R.build(mesh, name)
    if F.HIP_ROCK:
        import hips
        hips.split(mesh, rig, name)
    track = []
    for i in range(F.GAIT_FRAMES):
        walk(rig, name, i / F.GAIT_FRAMES, F.STEP)
        if F.HIP_ROCK:
            hips.rock(rig, name, i / F.GAIT_FRAMES, F.HIP_ROCK, GAIT[name]["turn"])
            bpy.context.view_layer.update()
        row = {f"{bone}.{side}": [list(rig.pose.bones[f"{bone}.{side}"].head), list(rig.pose.bones[f"{bone}.{side}"].tail)]
               for side in "LR" for bone in ("thigh", "shin", "foot")}
        for side in "LR":                                  # the sole: its heel's end and its front end, which stand on z = 0 at rest
            P, pb = R.joints(name, side), rig.pose.bones[f"foot.{side}"]
            M = pb.matrix @ pb.bone.matrix_local.inverted()
            row[f"sole.{side}"] = [list(M @ Vector((P["ankle"].x, y, 0.0))) for y in (P["ankle"].y - GAIT[name]["heel"], P["toe"].y)]
        row["body"] = list(rig.pose.bones["body"].head)
        track.append(row)
    json.dump(dict(name=name, crouch=crouch(name, F.STEP), frames=track), open(os.path.join(F.WIP, f"skeleton-{name}.json"), "w"))
    print(f"SKELETON {name}: crouch {crouch(name, F.STEP):.2f} m")
