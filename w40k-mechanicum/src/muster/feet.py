"""Where the post of each banner of the left walk meets the floor: the row of its foot (`foot` in POSTS of
src/muster.py). A post stands at the depth measured for its cloth; the floor is that of the crowd (muster_crowd.npz),
under the post as a plane through its 12 nearest points. Also seen from above: how far each post stands from the
railing of the walk, at the depth of its cloth and at the depth its thing has in the list.

    python3 src/muster/feet.py
"""
import os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import muster as M

T, b, B, c, posts = (np.load(M.SCENE + f"_{name}.npz") for name in ("things", "banners", "back", "crowd", "posts"))
ids = [str(v) for v in T["ids"]]
K, (H, W) = B["intrinsics"], B["depth"].shape
v = c["floor"].reshape(-1, 3)
row = lambda y, z: (-z / y * K[1, 1] + K[1, 2]) * H - 0.5                # the row of a place y deep and z above the camera
right = lambda col, y: ((col + 0.5) / W - K[0, 2]) / K[0, 0] * y        # how far right of the camera a column is at depth y
rail = T["depth"][ids.index("P1")]
cols = np.flatnonzero(np.isfinite(rail))
line = np.stack([right(cols, rail[cols]), rail[cols]], 1)               # the railing from above


def floor(x, y):
    k = np.argsort(np.hypot(v[:, 0] - x, v[:, 1] - y))[:12]
    p = np.linalg.lstsq(np.c_[v[k, 0], v[k, 1], np.ones(12)], v[k, 2], rcond=None)[0]
    return float(p[0] * x + p[1] * y + p[2])


print("banner | depth of its cloth, of its post in the list | from the railing, seen from above, at each (scene m) | row of its foot on the floor | upper edge of the railing in that column | lower end of the rod now")
for k, el in enumerate([el for el in M.ELEMENTS if el["kind"] == "banner"][:6], 1):
    at = posts[f"{el['id']}_at"]
    cloth, thing = float(np.median(b[f"v{k}"][:, 1])), float(np.nanmedian(T["depth"][ids.index("T" + el["id"][1:])]))
    lean, r = np.polyfit(at[:, 1], at[:, 0], 1), 500.0
    for _ in range(20):                                                   # the row at which the axis of the post meets the floor
        x = right(np.polyval(lean, r), cloth)
        r = row(cloth, floor(x, cloth))
    away = [float(np.hypot(line[:, 0] - right(at[:20, 0].mean(), z), line[:, 1] - z).min()) for z in (cloth, thing)]
    edge = np.flatnonzero(T["label"][:, int(round(np.polyval(lean, r)))] == ids.index("P1") + 1)
    print(f"  {el['id']} | {cloth:5.1f} {thing:5.1f} | {away[0]:4.1f} {away[1]:4.1f} | {r:6.1f} | {edge.min() if len(edge) else -1} | {at[-1, 1]:.0f}")
