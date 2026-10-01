"""Actors of a plate scene: every priest of the motion map (src/motion.py)
as its own mesh with a skeleton, in front of the clean plate
(src/cleanplate.py).

The mesh is the MoGe-2 point map inside the priest's SAM mask. Its depth is
smoothed from the mask's interior, because edge pixels blend into the
background; the rim curves back like the side of a body and a back shell
closes it, so a turned head has volume. UVs are plate pixels: the plate is
the texture. The skeleton has root, spine, chest and head bones up the
figure, and an upper arm and forearm to every hand that holds something or
gestures; the weights come from the mask. A carried thing is its own mesh,
bound to that forearm. Motions are bone rotations, a whole number of cycles
per loop.

This module needs OpenCV, which Blender's Python lacks: it bakes meshes,
weights and bones into wip/scene3d/<name>_actors.npz, and src/rig.py builds the
Blender objects from that file.

    python3 src/actors.py <name>
"""
import os, sys, math, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motion as M

ROOT = M.ROOT
TAU = 2 * math.pi
STEP = 2                   # plate pixels per mesh vertex


def smooth(e0, e1, x):
    x = np.clip((x - e0) / (e1 - e0), 0, 1)
    return x * x * (3 - 2 * x)


def seg_dist(x, y, a, b):
    """Distance in pixels from points (x, y) to the segment a-b."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    s = np.clip(((x - a[0]) * vx + (y - a[1]) * vy) / max(vx * vx + vy * vy, 1e-6), 0, 1)
    return np.hypot(x - (a[0] + s * vx), y - (a[1] + s * vy))


def layout(name):
    """Per priest and carried thing: mask, front and back depth; per priest
    also the joints (plate pixels and depth) and the arms."""
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    d, seg = np.load(stem + ".npz"), np.load(stem + "_seg.npz")
    depth, K = d["depth"], d["intrinsics"]
    H, W = depth.shape
    f = float(K[0, 0]) * W
    lz = np.log(depth)
    els = [dict(e) for e in M.MAPS[name] if e["kind"] != "stream"]
    by = {e["id"]: e for e in els}
    for el in els:
        m = seg[el["id"]]
        core = cv2.erode(m.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        if core.sum() < 0.2 * m.sum():                       # thin things: staffs, candles
            core = m
        c = core.astype(np.float32)
        z = None
        for sg in (3, 12, 40):                               # the interior's depth, spread to the rim and beyond
            g = cv2.GaussianBlur(c, (0, 0), sg)
            zs = cv2.GaussianBlur(lz * c, (0, 0), sg) / (g + 1e-6)
            z = zs if z is None else np.where(seen, z, zs)
            seen = g > 0.05 if sg == 3 else seen | (g > 0.05)
        z = np.exp(z).astype(np.float32)
        dist = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5)
        R = max(2.0, 0.5 * float(np.percentile(dist[m], 90)))          # rim radius, pixels
        b = np.sqrt(np.clip(1 - (1 - np.minimum(dist / R, 1)) ** 2, 0, 1))
        el.update(mask=m, z=z, bulge=b, radius=R, rm=R * z / f)
    for el in els:
        if el["kind"] != "priest":
            continue
        m = el["mask"]
        ys, xs = np.nonzero(m)
        yt, yb = int(ys.min()), int(ys.max())
        Hh = yb - yt

        def cx(y, m=m, yt=yt, yb=yb):
            y = int(np.clip(y, yt + 2, yb - 2))
            return float(np.median(np.nonzero(m[max(y - 5, 0):y + 6].any(0))[0]))

        def zc(x, y, el=el, yt=yt, yb=yb):                   # the middle of the body's thickness
            yi, xi = int(np.clip(y, yt, yb)), int(np.clip(x, 0, W - 1))
            return float(el["z"][yi, xi] + el["rm"][yi, xi])

        cut = yb >= H - 4 or el["head"] >= 1.0               # the frame or another priest hides the legs
        yn = yt + min(el["head"], 0.97) * Hh
        yf = yb + (0.3 * Hh if yb >= H - 4 else 0) + (3.0 * Hh if el["head"] >= 1.0 else 0)
        yc, yp = yn + 0.22 * (yf - yn), yn + 0.5 * (yf - yn)
        rows = np.nonzero(m[int(np.clip(yc, yt, yb))])[0]
        bw = float(rows.max() - rows.min()) if len(rows) else float(xs.max() - xs.min())
        hr = np.nonzero(m[int(yt + 0.6 * (yn - yt))])[0]
        J = dict(top=(cx(yt + 3), yt), neck=(cx(yn), yn), chest=(cx(yc), yc), pelvis=(cx(yp), yp), feet=(cx(yp), yf))
        el.update(joints={k: (x, y, zc(x, y)) for k, (x, y) in J.items()}, cut=cut, bw=bw, height=Hh,
                  head_x=float(hr.mean()), head_hw=max(float(hr.max() - hr.min()) / 2, 6.0), arms=[])
    for el in els:                                           # an arm to every hand that holds or gestures
        if el["kind"] == "carry":
            p, tag, (hx, hy), deg = by[el["parent"]], el["id"], el["hand"], el.get("lift", 0.0)
            J = p["joints"]
            side = 1.0 if hx >= J["chest"][0] else -1.0
            sh = (J["chest"][0] + side * 0.28 * p["bw"], J["neck"][1] + 0.06 * (J["feet"][1] - J["neck"][1]))
            elb = (sh[0] + 0.25 * (hx - sh[0]), max(hy, sh[1]) + 0.10 * (J["feet"][1] - J["neck"][1]))
            zb = J["chest"][2]
            yi, xi = int(np.clip(hy, 0, H - 1)), int(np.clip(hx, 0, W - 1))
            zh = float(el["z"][yi, xi] + el["rm"][yi, xi])
            p["arms"].append(dict(tag=tag, deg=deg, shoulder=(*sh, zb), elbow=(*elb, 0.5 * (zb + zh)), hand=(hx, hy, zh),
                                  sign=1.0 if hx >= elb[0] else -1.0, r=max(8.0, 0.10 * p["bw"])))
    return els, K, (W, H)


def weights(el, x, y):
    """Bone weights of a priest's vertices at plate pixels x, y."""
    J = el["joints"]
    yf, yp, yc, yn = J["feet"][1], J["pelvis"][1], J["chest"][1], J["neck"][1]
    c_root, c_spine, c_chest = (yf + yp) / 2, (yp + yc) / 2, (yc + yn) / 2
    root = np.clip((y - c_spine) / (c_root - c_spine), 0, 1)
    chest = np.clip((c_spine - y) / (c_spine - c_chest), 0, 1)
    w = dict(root=root, chest=chest, spine=1 - root - chest)
    band = 0.04 * el["height"]
    head = smooth(yn + band, yn - band, y) * smooth(1.5 * el["head_hw"], 1.1 * el["head_hw"], np.abs(x - el["head_x"]))
    w = {k: v * (1 - head) for k, v in w.items()}
    w["head"] = head
    for a in el["arms"]:
        hx, hy = a["hand"][:2]
        ex, ey = a["elbow"][:2]
        L = max(math.hypot(hx - ex, hy - ey), 1.0)
        tip = (hx + (hx - ex) / L * a["r"], hy + (hy - ey) / L * a["r"])                 # past the joint: all of the fist
        fore = smooth(1.4 * a["r"], 0.7 * a["r"], seg_dist(x, y, (ex, ey), tip))
        upper = 0.6 * smooth(1.4 * a["r"], 0.7 * a["r"], seg_dist(x, y, a["shoulder"][:2], (ex, ey))) * (1 - fore)
        w = {k: v * (1 - fore - upper) for k, v in w.items()}
        w["fore_" + a["tag"]], w["upper_" + a["tag"]] = fore, upper
    return w


def world(K, size, x, y, z):
    """Plate pixel (x, y) at depth z to Blender world: x right, y forward, z up."""
    W, H = size
    X = ((np.asarray(x) + 0.5) / W - K[0, 2]) / K[0, 0] * z
    Y = ((np.asarray(y) + 0.5) / H - K[1, 2]) / K[1, 1] * z
    return np.stack([X, np.asarray(z) * np.ones_like(X), -Y], -1)


def grid(el, K, size):
    """Vertices, UVs and quads of an element: a front sheet on the smoothed
    depth with the rim curved back, and a back shell meeting it at the rim.
    Returns also each vertex's plate pixel, for the weights."""
    W, H = size
    m = cv2.dilate(el["mask"].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    ys, xs = np.nonzero(m)
    x0, y0 = xs.min() // STEP * STEP, ys.min() // STEP * STEP
    gx, gy = np.arange(x0, min(xs.max() + STEP, W - 1) + 1, STEP), np.arange(y0, min(ys.max() + STEP, H - 1) + 1, STEP)
    inside = m[np.ix_(gy, gx)]
    pad = np.pad(inside, 1)
    rim = inside & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    b = np.where(rim, 0.0, el["bulge"][np.ix_(gy, gx)])
    z, rm = el["z"][np.ix_(gy, gx)], el["rm"][np.ix_(gy, gx)]
    px, py = np.meshgrid(gx.astype(np.float32), gy.astype(np.float32))
    n = int(inside.sum())
    idx = np.full(inside.shape, -1)
    idx[inside] = np.arange(n)
    front = world(K, size, px[inside], py[inside], (z + rm * (1 - b))[inside])
    back = world(K, size, px[inside], py[inside], (z + rm * (1 + b))[inside])
    a, bb, c, e = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    ok = (a >= 0) & (bb >= 0) & (c >= 0) & (e >= 0)
    q = np.stack([a, e, c, bb], -1)[ok]                      # counter-clockwise seen from the camera
    uv = np.stack([(px[inside] + 0.5) / W, 1 - (py[inside] + 0.5) / H], -1)
    return (np.concatenate([front, back]), np.concatenate([uv, uv]), np.concatenate([q, q[:, ::-1] + n]),
            np.concatenate([px[inside]] * 2), np.concatenate([py[inside]] * 2))


def bake(name):
    """Meshes, weights and bones of every actor, in world coordinates."""
    els, K, size = layout(name)
    out, meta = {}, []
    for el in els:
        V, uv, q, px, py = grid(el, K, size)
        k = el["id"]
        out[k + "/V"], out[k + "/uv"], out[k + "/q"] = V.astype(np.float32), uv.astype(np.float32), q.astype(np.int32)
        if el["kind"] == "carry":
            meta.append(dict(id=k, kind="carry", parent=el["parent"], bone="fore_" + k))
            continue
        for bone, w in weights(el, px, py).items():
            out[f"{k}/w/{bone}"] = w.astype(np.float16)
        P = {j: world(K, size, *v).tolist() for j, v in el["joints"].items()}
        bones = [("root", P["feet"], P["pelvis"], None), ("spine", P["pelvis"], P["chest"], "root"),
                 ("chest", P["chest"], P["neck"], "spine"), ("head", P["neck"], P["top"], "chest")]
        arms = []
        for a in el["arms"]:
            s, e, h = (world(K, size, *a[j]).tolist() for j in ("shoulder", "elbow", "hand"))
            bones += [("upper_" + a["tag"], s, e, "chest"), ("fore_" + a["tag"], e, h, "upper_" + a["tag"])]
            arms.append(dict(tag=a["tag"], sign=a["sign"], deg=a["deg"]))
        meta.append(dict(id=k, kind="priest", bones=bones, arms=arms, phase=el["phase"],
                         **{m: el.get(m, 0) for m in ("turn", "nod", "tilt", "sway", "breathe")}))
    path = os.path.join(ROOT, "wip", "scene3d", name + "_actors.npz")
    np.savez_compressed(path, meta=json.dumps(meta), **out)
    print("ACTORS_BAKED", path, sum(len(out[m["id"] + "/V"]) for m in meta), "vertices")


if __name__ == "__main__":
    bake(sys.argv[1])
