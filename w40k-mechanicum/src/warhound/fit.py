"""How much of the titan the plate hides, for the saint scene's titan settings (src/scenes.py) moved left or right.

    blender -b -P src/warhound/fit.py -- '<json overrides of the titan settings>' <px>[:<depth>] ...

For each plate column px of the head's middle and depth D in metres (row as in the settings; the titan scaled by
D over the settings' depth about the camera, so its size in the picture stays), over 8 phases of the idle motion:
the head's columns on the plate, and per part the share of its vertices that lie in the picture and before the
plate's 3D scene (wip/scene3d/saint_clean.npz, with the corridor), and the share of them seen outside the corridor's
outline (src/saintcorridor.py). A vertex is hidden where the plate's depth at its pixel is less than its own depth.
"""
import ast, json, os, sys
import bpy
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import titan, saintcorridor

src = open(os.path.join(ROOT, "src", "scenes.py")).read()
node = next(n for n in ast.parse(src).body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SCENES")
ns = {}
exec(compile(ast.Module([node], []), "scenes", "exec"), ns)
argv = sys.argv[sys.argv.index("--") + 1:]
conf = {**ns["SCENES"]["saint"]["titan"], **json.loads(argv[0])}
cols = [tuple(float(x) for x in (a + ":" + str(conf["head"][2])).split(":")[:2]) for a in argv[1:]] or [tuple(conf["head"][::2])]

d = np.load(os.path.join(ROOT, "wip", "scene3d", "saint_clean.npz"))
K, depth = d["intrinsics"], d["depth"]
H, W = depth.shape
mouth = saintcorridor.outline(H, W)
bpy.ops.wm.read_factory_settings(use_empty=True)
movers = []
root = titan.build(conf, K, (W, H), movers)
obs = [o for o in root.children if o.type == "MESH"]
px0, row, D = conf["head"]


def shown(P):
    """Plate column, row, and whether each world point (x right, y depth, z up) is in the picture and not hidden."""
    c = (P[:, 0] / P[:, 1] * K[0, 0] + K[0, 2]) * W - 0.5
    r = (-P[:, 2] / P[:, 1] * K[1, 1] + K[1, 2]) * H - 0.5
    ci, ri = np.round(c).astype(int), np.round(r).astype(int)
    inside = (ci >= 0) & (ci < W) & (ri >= 0) & (ri < H)
    seen = inside.copy()
    seen[inside] = P[inside, 1] <= depth[ri[inside], ci[inside]]
    out = seen.copy()
    out[seen] = ~mouth[ri[seen], ci[seen]]
    return c, r, inside, seen, out


worst, box = {}, {}
for ph in np.arange(8) / 8:
    for f in movers:
        f(ph)
    bpy.context.view_layer.update()
    for o in obs:
        co = np.empty(len(o.data.vertices) * 3, np.float32)
        o.data.vertices.foreach_get("co", co)
        m = np.array(o.matrix_world)
        co = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        for px, D1 in cols:
            shift = np.array([(px - px0) / W / K[0, 0] * D1, 0, 0])
            c, r, inside, seen, out = shown(co * (D1 / D) + shift)
            w = worst.setdefault((px, D1, o.name), [1.0, 0.0, W, 0.0, W, 0.0, 0.0])
            w[6] = max(w[6], out.mean())
            if out.any():
                b = box.setdefault((px, D1, o.name), [W, H, 0, 0])
                b[:] = [min(b[0], c[out].min()), min(b[1], r[out].min()), max(b[2], c[out].max()), max(b[3], r[out].max())]
            w[0] = min(w[0], seen.mean())
            w[1] = max(w[1], seen.mean())
            if o.name == "head":
                w[2], w[3] = min(w[2], c.min()), max(w[3], c.max())
                if (~seen).any():
                    w[4], w[5] = min(w[4], c[~seen].min()), max(w[5], c[~seen].max())
for px, D1 in cols:
    h = worst[(px, D1, "head")]
    print(f"FIT px {px:.0f} depth {D1:.2f}: head columns {h[2]:.0f}..{h[3]:.0f}, shown {100 * h[0]:.1f}..{100 * h[1]:.1f} %"
          + (f", hidden at columns {h[4]:.0f}..{h[5]:.0f}" if h[5] else ""))
    for o in obs:
        lo, hi = worst[(px, D1, o.name)][:2]
        if o.name != "head" and hi > 0.005:
            print(f"FIT     {o.name}: shown {100 * lo:.1f}..{100 * hi:.1f} %, outside the outline up to {100 * worst[(px, D1, o.name)][6]:.1f} %"
                  + (" at columns {0:.0f}..{2:.0f}, rows {1:.0f}..{3:.0f}".format(*box[(px, D1, o.name)]) if (px, D1, o.name) in box else ""))
