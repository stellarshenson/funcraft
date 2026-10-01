"""Pose test for the armatures: each chassis painted, rigged and posed.

Run:
    blender -b -P src/rigtest.py [-- madcat atlas battlemaster]

Writes wip/preview/rig/<chassis>-<pose>-<view>.png. Each pose moves only the
controllers - body and the two foot IK bones - exactly as the walk will.
"""

import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
import paint as P
import rig as G
import lookdev as LD
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "wip", "preview", "rig")


def poses(name):
    """(pose name, body drop, {side: (dy, dz, pitch)} foot offsets from rest)."""
    Jl, Jr = G.joints(name, "L"), G.joints(name, "R")
    # stride: left foot forward and lifted, right foot back, heel rising
    mid = (Jl["ankle"].y + Jr["ankle"].y) / 2
    return [
        ("rest", 0.0, {"L": (0, 0, 0), "R": (0, 0, 0)}),
        ("stride", 0.35, {"L": (mid + 2.0 - Jl["ankle"].y, 0.9, 0.0),
                          "R": (mid - 2.0 - Jr["ankle"].y, 0.0, 0.0)}),
        ("crouch", 0.9, {"L": (mid - Jl["ankle"].y, 0, 0), "R": (mid - Jr["ankle"].y, 0, 0)}),
    ]


def main(names):
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        cfg = R.CHASSIS[name]
        R.clear_scene()
        mech = R.load(name)
        mech.name = name
        P.paint(mech, name)
        bpy.context.view_layer.objects.active = mech
        mech.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(31))
        rig = G.build(mech, name)
        H = cfg["height"]
        LD.studio(H)
        LD.render_setup(48)
        bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 640, 800
        cd = bpy.data.cameras.new("cam")
        cd.lens = 70
        cam = bpy.data.objects.new("cam", cd)
        bpy.context.collection.objects.link(cam)
        bpy.context.scene.camera = cam

        body0 = rig.data.bones["body"].head_local.copy()
        for pose, drop, feet in poses(name):
            G.place(rig, "body", body0 - Vector((0, 0, drop)))
            for s, (dy, dz, pitch) in feet.items():
                a = G.joints(name, s)["ankle"]
                G.turn(rig, f"ik.{s}", a + Vector((0, dy, dz)), pitch)
            bpy.context.view_layer.update()
            for view, az, el in (("side", 90, 4), ("front34", 32, 7)):
                LD.look(cam, (0, 0, H * 0.5), az, el, H * 2.45)
                bpy.context.scene.render.filepath = os.path.join(OUT, f"{name}-{pose}-{view}.png")
                bpy.ops.render.render(write_still=True)
            print("RIGTEST", name, pose, flush=True)

        blend = os.path.join(ROOT, "in", "models", "rigged", f"{name}.blend")
        os.makedirs(os.path.dirname(blend), exist_ok=True)
        G.place(rig, "body", body0)
        for s in "LR":
            G.place(rig, f"ik.{s}", G.joints(name, s)["ankle"])
        bpy.ops.wm.save_as_mainfile(filepath=blend)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv or list(P.SCHEMES))
