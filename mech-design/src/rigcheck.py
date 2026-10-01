"""Measure skin tearing: in each test pose, find mesh edges stretched far past
their rest length. A clean rig stretches only inside the short joint blends.

Run:
    blender -b -P src/rigcheck.py [-- madcat atlas battlemaster]
"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
import rig as G
import rigtest as T
from mathutils import Vector


def check(name):
    R.clear_scene()
    mech = R.load(name)
    rig = G.build(mech, name)
    n = len(mech.data.vertices)
    rest = np.empty(n * 3); mech.data.vertices.foreach_get("co", rest); rest = rest.reshape(-1, 3)
    ed = np.empty(len(mech.data.edges) * 2, dtype=np.int64)
    mech.data.edges.foreach_get("vertices", ed); ed = ed.reshape(-1, 2)
    l0 = np.linalg.norm(rest[ed[:, 0]] - rest[ed[:, 1]], axis=1)
    body0 = rig.data.bones["body"].head_local.copy()
    for pose, drop, feet in T.poses(name)[1:]:
        G.place(rig, "body", body0 - Vector((0, 0, drop)))
        for s, (dy, dz, pitch) in feet.items():
            G.turn(rig, f"ik.{s}", G.joints(name, s)["ankle"] + Vector((0, dy, dz)), pitch)
        bpy.context.view_layer.update()
        ev = mech.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        pos = np.empty(n * 3); ev.vertices.foreach_get("co", pos); pos = pos.reshape(-1, 3)
        l1 = np.linalg.norm(pos[ed[:, 0]] - pos[ed[:, 1]], axis=1)
        torn = (l1 > 3 * l0) & (l1 - l0 > 0.3)
        print(f"CHECK {name} {pose}: {torn.sum()} of {len(ed)} edges stretched >3x and >0.3 units")
        if torn.any():
            mid = (rest[ed[torn, 0]] + rest[ed[torn, 1]]) / 2
            for q in np.unique(np.round(mid, 0), axis=0)[:12]:
                print("   near rest point", q)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for nm in argv or ["madcat", "atlas", "battlemaster"]:
        check(nm)
