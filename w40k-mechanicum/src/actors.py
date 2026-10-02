"""Actors of a plate scene: every moving element of the motion map
(src/motion.py) as its own mesh with bones, in front of the clean plate
(src/cleanplate.py).

Mesh. The MoGe-2 point map inside the element's SAM mask. Depth is smoothed
from the mask's interior, because edge pixels blend into the background; a
thin thing (a candle, a staff, a chain) takes one depth, the near side of
what MoGe-2 saw, so it stays where it is held. The rim curves back and a
back shell closes the mesh. UVs are plate pixels: the plate is the texture.
A wheel that spins is a flat disc on the plane fitted to its points, with
its own texture unrolled by angle and radius, so it can turn all the way.

Bones, by kind:
    priest   root, spine, chest, head; two robe bones hanging from the hips;
             per hand an upper arm, a forearm and a hand bone that keeps its
             orientation, so what the hand holds moves with the hand and
             stays upright
    carry    bound to its priest's hand bone; a staff that stands on the
             floor turns about its foot and follows the hand
    swing    one bone from the pivot
    hover    one bone
    cloth    four bones from the top edge down
    spin     one bone along the wheel's axis
    flame    two bones from the wick up; on a carried candle they hang from
             the hand bone

This module needs OpenCV, which Blender's Python lacks: it bakes meshes,
weights and bones into wip/scene3d/<name>_actors.npz, and src/rig.py builds
the Blender objects from that file.

    python3 src/actors.py <name>
"""
import os, sys, math, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motion as M

ROOT = M.ROOT
TAU = 2 * math.pi
STEP = 2                   # plate pixels per mesh vertex
REACH = 0.65               # m, how far in front of the chest a hand can hold a thing
FLAME_H = 0.04             # m, the height of a candle flame; the model paints them 5 to 25 cm tall
FLAME_PX = 8.0             # plate pixels: a flame shown smaller than this has no shape left


def smooth(e0, e1, x):
    x = np.clip((x - e0) / (e1 - e0), 0, 1)
    return x * x * (3 - 2 * x)


def seg_dist(x, y, a, b):
    """Distance in pixels from points (x, y) to the segment a-b."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    s = np.clip(((x - a[0]) * vx + (y - a[1]) * vy) / max(vx * vx + vy * vy, 1e-6), 0, 1)
    return np.hypot(x - (a[0] + s * vx), y - (a[1] + s * vy))


def hats(v, centres):
    """Piecewise-linear weights of value v over ascending `centres`: one
    array per centre, summing to 1."""
    out = []
    for i, c in enumerate(centres):
        w = np.ones_like(v, dtype=np.float32)
        if i > 0:
            w = w * np.clip((v - centres[i - 1]) / (c - centres[i - 1]), 0, 1)
        if i < len(centres) - 1:
            w = w * np.clip((centres[i + 1] - v) / (centres[i + 1] - c), 0, 1)
        out.append(w)
    return out


def world(K, size, x, y, z):
    """Plate pixel (x, y) at depth z to Blender world: x right, y forward, z up."""
    W, H = size
    X = ((np.asarray(x) + 0.5) / W - K[0, 2]) / K[0, 0] * z
    Y = ((np.asarray(y) + 0.5) / H - K[1, 2]) / K[1, 1] * z
    return np.stack([X, np.asarray(z) * np.ones_like(X), -Y], -1)


def pixel(K, size, P):
    """Blender world points (..., 3) to plate pixels (x, y)."""
    W, H = size
    return ((P[..., 0] / P[..., 1] * K[0, 0] + K[0, 2]) * W - 0.5, (-P[..., 2] / P[..., 1] * K[1, 1] + K[1, 2]) * H - 0.5)


def flame_scale(fl, z, f):
    """How much a painted flame shrinks about its wick: to FLAME_H at depth
    z (f: focal length in pixels), but not below FLAME_PX pixels, and never
    larger than painted. A flame cut off by the plate's edge keeps its size:
    its full height is not known."""
    h = max(fl["wick"][1] - fl["tip"][1], 1.0)
    return 1.0 if fl.get("edge") else min(1.0, max(FLAME_H * f / (z * h), FLAME_PX / h))


def load(name):
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    d, seg = np.load(stem + ".npz"), np.load(stem + "_seg.npz")
    depth, K = d["depth"], d["intrinsics"]
    depth = np.where(np.isfinite(depth) & (depth > 0), depth, 2 * np.nanmax(depth[np.isfinite(depth)]))   # sky: far dome
    flames = json.loads(str(seg["flames"])) if "flames" in seg.files else []
    return depth, K, seg, flames


def wheels(name):
    seg = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_seg.npz"))
    return json.loads(str(seg["wheels"])) if "wheels" in seg.files else {}


def surface(el, depth, f):
    """Front depth, rim bulge and rim radius (metres) of an element's mask."""
    m = el["mask"]
    lz = np.log(depth)
    core = cv2.erode(m.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    thin = core.sum() < 0.2 * m.sum() or el["kind"] in ("carry", "flame")
    if thin:                                             # one depth: the near side of what MoGe-2 saw
        z = np.full(m.shape, float(np.percentile(depth[m], 30)), np.float32)
    else:
        c, z = core.astype(np.float32), None
        for sg in (3, 12, 40):                           # the interior's depth, spread to the rim and beyond
            g = cv2.GaussianBlur(c, (0, 0), sg)
            zs = cv2.GaussianBlur(lz * c, (0, 0), sg) / (g + 1e-6)
            z = zs if z is None else np.where(seen, z, zs)
            seen = g > 0.05 if sg == 3 else seen | (g > 0.05)
        z = np.exp(z).astype(np.float32)
    dist = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5)
    R = max(2.0, 0.5 * float(np.percentile(dist[m], 90)))
    if el["kind"] in ("cloth", "flame"):
        R = min(R, 3.0)                                  # cloth and flames are thin
    b = np.sqrt(np.clip(1 - (1 - np.minimum(dist / R, 1)) ** 2, 0, 1))
    el.update(z=z, bulge=b, rm=(R * z / f).astype(np.float32))


def layout(name):
    """Every element that gets a mesh: mask, depth, bones (plate pixels and
    depth) and what its bones do. Carried things and carried flames add
    their bones to the priest that holds them."""
    depth, K, seg, flames = load(name)
    H, W = depth.shape
    f = float(K[0, 0]) * W
    els = [dict(e) for e in M.MAPS[name] if e["kind"] not in ("stream", "smoke")]
    for fl in flames:
        if fl["mesh"]:
            els.append(dict(kind="flame", id=fl["id"], who="Flame", wick=fl["wick"], tip=fl["tip"], owner=fl["owner"],
                            edge=fl.get("edge", False)))
    by = {e["id"]: e for e in els}

    def sized(el, z):
        """Sets a flame's scale at depth z (flame_scale); returns its tip after scaling (plate pixels)."""
        wk, tp = el["wick"], el["tip"]
        el["scale"] = flame_scale(el, z, f)
        return (wk[0] + el["scale"] * (tp[0] - wk[0]), wk[1] + el["scale"] * (tp[1] - wk[1]))

    for el in els:
        el["mask"] = seg[el["id"]]
        el["bones"], el["moving"] = [], []
        surface(el, depth, f)

    def at(el, x, y):                                        # the middle of the element's thickness
        yi, xi = int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))
        return float(el["z"][yi, xi] + el["rm"][yi, xi])

    for el in els:
        m = el["mask"]
        ys, xs = np.nonzero(m)
        yt, yb = int(ys.min()), int(ys.max())

        def mid(y, m=m, yt=yt, yb=yb):
            y = int(np.clip(y, yt + 2, yb - 2)) if yb - yt > 4 else yt
            cols = np.nonzero(m[max(y - 5, 0):y + 6].any(0))[0]
            return float(np.median(cols))

        if el["kind"] == "priest":
            Hh = yb - yt
            yn = yt + min(el["head"], 0.97) * Hh
            yf = yb + (0.3 * Hh if yb >= H - 4 else 0) + (3.0 * Hh if el["head"] >= 1.0 else 0)
            yc, yp = yn + 0.22 * (yf - yn), yn + 0.5 * (yf - yn)
            rows = np.nonzero(m[int(np.clip(yc, yt, yb))])[0]
            bw = float(rows.max() - rows.min()) if len(rows) else float(xs.max() - xs.min())
            hr = np.nonzero(m[int(yt + 0.6 * (yn - yt))])[0]
            J = dict(top=(mid(yt + 3), yt), neck=(mid(yn), yn), chest=(mid(yc), yc), pelvis=(mid(yp), yp),
                     knee=(mid(yp), yp + 0.5 * (yf - yp)), feet=(mid(yp), yf))
            J = {k: (x, y, at(el, x, y)) for k, (x, y) in J.items()}
            el.update(joints=J, bw=bw, height=Hh, head_x=float(hr.mean()), head_hw=max(float(hr.max() - hr.min()) / 2, 6.0),
                      arms=[])
            el["bones"] = [("root", J["feet"], J["pelvis"], None), ("spine", J["pelvis"], J["chest"], "root"),
                           ("chest", J["chest"], J["neck"], "spine"), ("head", J["neck"], J["top"], "chest"),
                           ("robe1", J["pelvis"], J["knee"], "root"), ("robe2", J["knee"], J["feet"], "robe1")]
            el["moving"] = (["head"] if any(el.get(k) for k in ("turn", "nod", "tilt")) else []) + \
                           (["root"] if el.get("sway") else []) + (["chest"] if el.get("breathe") else []) + \
                           (["robe1", "robe2"] if el.get("robe") else [])
        elif el["kind"] == "swing":
            px, py = el["pivot"]
            c = (float(xs.mean()), float(ys.mean()))
            z = at(el, *c)
            el["bones"], el["moving"] = [("swing", (px, py, z), (*c, z), None)], ["swing"]
        elif el["kind"] == "hover":
            c = (float(xs.mean()), float(ys.mean()))
            z = at(el, *c)
            el["bones"], el["moving"] = [("hover", (c[0], c[1] + 20, z), (c[0], c[1] - 20, z), None)], ["hover"]
        elif el["kind"] == "cloth":
            rows = np.linspace(yt + 0.04 * (yb - yt), yb, 5)
            pts = [(mid(y), float(y)) for y in rows]
            pts = [(x, y, at(el, x, y)) for x, y in pts]
            el["chain"] = pts
            el["bones"] = [(f"c{i}", pts[i], pts[i + 1], f"c{i - 1}" if i else None) for i in range(4)]
            el["moving"] = [b[0] for b in el["bones"]]
        elif el["kind"] == "flame" and el["owner"] is None:
            wk, z = el["wick"], at(el, *el["wick"])
            tp = sized(el, z)
            half = ((wk[0] + tp[0]) / 2, (wk[1] + tp[1]) / 2, z)
            el["bones"] = [("fa", (*wk, z), half, None), ("fb", half, (*tp, z), "fa")]
            el["moving"] = ["fa", "fb"]
    for el in els:                                           # an arm and a hand bone to every hand that holds or gestures
        if el["kind"] != "carry":
            continue
        p, tag, (hx, hy) = by[el["parent"]], el["id"], el["hand"]
        J = p["joints"]
        el["z"] = np.clip(el["z"], J["chest"][2] - REACH, J["chest"][2])       # within an arm's reach of the chest
        side = 1.0 if hx >= J["chest"][0] else -1.0
        sh = (J["chest"][0] + side * 0.28 * p["bw"], J["neck"][1] + 0.06 * (J["feet"][1] - J["neck"][1]))
        elb = (sh[0] + 0.25 * (hx - sh[0]), max(hy, sh[1]) + 0.10 * (J["feet"][1] - J["neck"][1]))
        zb, zh = J["chest"][2], at(el, hx, hy)
        arm = dict(tag=tag, deg=el.get("lift", 0.0), shoulder=(*sh, zb), elbow=(*elb, 0.5 * (zb + zh)), hand=(hx, hy, zh),
                   sign=1.0 if hx >= elb[0] else -1.0, r=max(8.0, 0.10 * p["bw"]))
        p["arms"].append(arm)
        p["bones"] += [("upper_" + tag, arm["shoulder"], arm["elbow"], "chest"),
                       ("fore_" + tag, arm["elbow"], arm["hand"], "upper_" + tag),
                       ("hand_" + tag, arm["hand"], (hx, hy - 25, zh), "fore_" + tag, dict(upright=True))]
        if arm["deg"]:
            p["moving"].append("fore_" + tag)
        el["bind"] = "hand_" + tag
        if el.get("stands"):                                 # a staff on the floor: turns about its foot, follows the hand
            ys, xs = np.nonzero(el["mask"])
            foot = (float(np.median(xs[ys > ys.max() - 6])), float(ys.max()), zh)
            p["bones"].append(("staff_" + tag, foot, arm["hand"], None, dict(track="hand_" + tag)))
            el["bind"] = "staff_" + tag
        for fe in els:                                       # the candle's flame: its own mesh, its bones on the hand bone
            if fe["kind"] == "flame" and fe["owner"] == tag:
                fe["z"] = np.full_like(fe["z"], zh - float(fe["rm"].max()))      # at the candle's depth
                wk, tp = fe["wick"], sized(fe, zh)
                half = ((wk[0] + tp[0]) / 2, (wk[1] + tp[1]) / 2, zh)
                p["bones"] += [("fa_" + tag, (*wk, zh), half, el["bind"]), ("fb_" + tag, half, (*tp, zh), "fa_" + tag)]
                p["moving"] += ["fa_" + tag, "fb_" + tag]
                fe.update(parent=el["parent"], names=("fa_" + tag, "fb_" + tag), bind=el["bind"])
    return els, K, (W, H), flames


def flame_weights(wick, tip, x, y, names, rest):
    """Vertices from the wick up follow the two flame bones; below it, `rest`."""
    h = np.clip((wick[1] - y) / max(wick[1] - tip[1], 1.0), -1, 1.5)
    on = smooth(-0.05, 0.15, h)                              # nothing below the wick moves
    up = smooth(0.35, 0.65, h)
    w = {names[0]: on * (1 - up), names[1]: on * up}
    if rest:
        w[rest] = 1 - on
    return w


def weights(el, x, y):
    """Bone weights of an element's vertices at plate pixels x, y."""
    if el["kind"] == "priest":
        J = el["joints"]
        yf, yp, yc, yn = J["feet"][1], J["pelvis"][1], J["chest"][1], J["neck"][1]
        chest, spine, r1, r2 = hats(y, [(yc + yn) / 2, (yp + yc) / 2, yp + 0.3 * (yf - yp), yp + 0.8 * (yf - yp)])
        w = dict(chest=chest, spine=spine, robe1=r1, robe2=r2)
        band = 0.04 * el["height"]
        head = smooth(yn + band, yn - band, y) * smooth(1.5 * el["head_hw"], 1.1 * el["head_hw"], np.abs(x - el["head_x"]))
        w = {k: v * (1 - head) for k, v in w.items()}
        w["head"] = head
        for a in el["arms"]:
            hx, hy = a["hand"][:2]
            ex, ey = a["elbow"][:2]
            L = max(math.hypot(hx - ex, hy - ey), 1.0)
            tip = (hx + (hx - ex) / L * a["r"], hy + (hy - ey) / L * a["r"])
            fore = smooth(1.4 * a["r"], 0.7 * a["r"], seg_dist(x, y, (ex, ey), tip))
            upper = 0.6 * smooth(1.4 * a["r"], 0.7 * a["r"], seg_dist(x, y, a["shoulder"][:2], (ex, ey))) * (1 - fore)
            w = {k: v * (1 - fore - upper) for k, v in w.items()}
            w["fore_" + a["tag"]], w["upper_" + a["tag"]] = fore, upper
        return w
    if el["kind"] == "cloth":
        ys = [p[1] for p in el["chain"]]
        return dict(zip(("c0", "c1", "c2", "c3"), hats(y, [(ys[i] + ys[i + 1]) / 2 for i in range(4)])))
    if el["kind"] == "flame":
        return flame_weights(el["wick"], el["tip"], x, y, el.get("names", ("fa", "fb")), el.get("bind"))
    if el["kind"] == "carry":
        return {el["bind"]: np.ones_like(x, dtype=np.float32)}
    return {el["bones"][0][0]: np.ones_like(x, dtype=np.float32)}


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


def wheel_fit(el, mask, depth, K, size):
    """Where a wheel is: hub, axis and radius (world, metres). A mask of
    8000 px or more has enough MoGe-2 points: the axis is the normal of the
    plane fitted to them. A smaller wheel seen at an angle is an ellipse:
    the ratio of its axes is the cosine of the tilt and its long axis lies
    across the view, which gives the axis up to a mirror image; the fitted
    plane picks between the two. A small wheel that is round in the image,
    or cut by the plate's edge, faces the camera. rim "inner": the largest circle about the hub
    that the mask fills (a fan inside its frame); "outer": the circle round
    the whole mask (a cog with its teeth)."""
    H, W = mask.shape
    ys, xs = np.nonzero(cv2.erode(mask.astype(np.uint8), np.ones((5, 5), np.uint8)))
    P = world(K, size, xs, ys, depth[ys, xs])
    c0 = np.median(P, 0)
    hx, hy = el["pos"][0]
    ray = world(K, size, hx, hy, 1.0)
    v = ray / np.linalg.norm(ray)
    _, _, vt = np.linalg.svd(P[::max(1, len(P) // 4000)] - c0, full_matrices=False)
    fitted = vt[2] if vt[2] @ v < 0 else -vt[2]              # towards the camera
    ysm, xsm = np.nonzero(mask)
    whole = xsm.min() > 1 and ysm.min() > 1 and xsm.max() < W - 2 and ysm.max() < H - 2
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    (_, _), (d1, d2), ang = cv2.fitEllipse(max(cs, key=len))
    if mask.sum() >= 8000:                                   # enough points for the plane
        n = fitted
    elif whole and min(d1, d2) < 0.85 * max(d1, d2):         # a small wheel seen at an angle
        a = math.radians(ang) + (math.pi / 2 if d2 > d1 else 0)      # direction of the long axis in the image
        tilt = math.acos(min(d1, d2) / max(d1, d2))
        u1 = np.array([math.cos(a), 0.0, -math.sin(a)])              # image x is world x, image y is world -z
        u1 = u1 - (u1 @ v) * v
        u1 = u1 / np.linalg.norm(u1)
        u2 = np.cross(v, u1)
        cands = [np.cross(u1, math.cos(tilt) * u2 + sgn * math.sin(tilt) * v) for sgn in (1, -1)]
        cands = [c if c @ v < 0 else -c for c in cands]
        n = max(cands, key=lambda c: c @ fitted)
    else:                                                    # a small wheel, round in the image or cut by the edge
        n = -v
    hub = ray * (c0 @ n) / (ray @ n)                         # the hub pixel's ray meets the plane
    e1 = np.cross(n, [0.0, 0.0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0.0, 0.0])
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    ysa, xsa = np.nonzero(mask)
    Pa = world(K, size, xsa, ysa, 1.0)
    Pa = Pa * ((c0 @ n) / (Pa @ n))[:, None]                 # every mask pixel on the plane
    R = float(np.percentile(np.linalg.norm(Pa - hub, axis=1), 99))
    if el.get("rim") == "inner":
        th = np.linspace(0, TAU, 360, endpoint=False)
        ring = np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2
        for r in np.linspace(R, 0.2 * R, 60):
            qx, qy = pixel(K, size, hub + r * ring)
            ok = (qx >= 0) & (qx < W - 1) & (qy >= 0) & (qy < H - 1)
            if ok.all() and mask[qy.astype(int), qx.astype(int)].mean() >= 0.97:
                R = float(r)
                break
    return dict(hub=hub.tolist(), n=n.tolist(), e1=e1.tolist(), e2=e2.tolist(), R=R)


def wheel_disc(fit, K, size):
    """The plate pixels a wheel's disc covers."""
    W, H = size
    th = np.linspace(0, TAU, 360, endpoint=False)
    Q = np.array(fit["hub"]) + fit["R"] * (np.cos(th)[:, None] * np.array(fit["e1"]) + np.sin(th)[:, None] * np.array(fit["e2"]))
    qx, qy = pixel(K, size, Q)
    return cv2.fillPoly(np.zeros((H, W), np.uint8), [np.round(np.stack([qx, qy], 1)).astype(np.int32)], 1) > 0


def wheel(name, el, K, size, fit, rings=48, spokes=240):
    """A spinning wheel: a flat disc, and its texture unrolled by angle (u)
    and radius (v) with the mask as its alpha. Where the wheel is outside
    the plate, the texture is its own mirror image about the edge of what
    is seen. Returns vertices, uvs, quads and the texture's path."""
    W, H = size
    m = el["mask"]
    hub, e1, e2, R = np.array(fit["hub"]), np.array(fit["e1"]), np.array(fit["e2"]), fit["R"]
    th = np.linspace(0, TAU, 720, endpoint=False)
    rr = (np.arange(256) + 0.5) / 256 * R
    Q = hub + rr[:, None, None] * (np.cos(th)[None, :, None] * e1 + np.sin(th)[None, :, None] * e2)
    qx, qy = (v.astype(np.float32) for v in pixel(K, size, Q))
    plate = cv2.imread(os.path.join(ROOT, "wip", "scene3d", name + ".png"), cv2.IMREAD_COLOR)
    ok = (qx >= 0) & (qx <= W - 1) & (qy >= 0) & (qy <= H - 1)
    tex = cv2.remap(plate, qx, qy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    alpha = cv2.remap(m.astype(np.uint8) * 255, qx, qy, cv2.INTER_LINEAR)
    tex = np.dstack([tex, alpha])
    for r in range(256):                                     # outside the plate: the mirror image of what is seen
        good = np.nonzero(ok[r])[0]
        if len(good) in (0, 720):
            continue
        bad = np.nonzero(~ok[r])[0]
        near = good[np.abs(((bad[:, None] - good[None, :] + 360) % 720) - 360).argmin(1)]
        src = (2 * near - bad) % 720
        tex[r, bad] = tex[r, np.where(ok[r][src], src, near)]
    path = os.path.join(ROOT, "wip", "scene3d", f"{name}_wheel_{el['id']}.png")
    cv2.imwrite(path, tex[::-1])
    a = np.linspace(0, TAU, spokes + 1)
    rad = np.linspace(0, R, rings + 1)
    V = hub + rad[:, None, None] * (np.cos(a)[None, :, None] * e1 + np.sin(a)[None, :, None] * e2)
    uv = np.stack(np.broadcast_arrays((a / TAU)[None, :], (rad / R)[:, None]), -1)
    idx = np.arange((rings + 1) * (spokes + 1)).reshape(rings + 1, spokes + 1)
    q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
    return V.reshape(-1, 3), uv.reshape(-1, 2), q, path


def source(el, flames, depth, f):
    """Plate pixel and depth of a fixed smoke source: the tip of the flame
    nearest `at` within 60 px, at the size the flame is shown (flame_scale),
    or `at` itself (a censer). f: the focal length in pixels."""
    x, y = el["at"]
    near = min(flames, key=lambda f: math.hypot(f["wick"][0] - x, f["wick"][1] - y), default=None)
    if near and math.hypot(near["wick"][0] - x, near["wick"][1] - y) < 60:
        (wx, wy), (tx, ty) = near["wick"], near["tip"]
        yy, xx = int(min(wy + 6, depth.shape[0] - 1)), int(wx)
        z = float(np.percentile(depth[max(yy - 3, 0):yy + 4, max(xx - 3, 0):xx + 4], 30))
        s = flame_scale(near, z, f) if near["mesh"] else 1.0
        return (wx + s * (tx - wx), wy + s * (ty - wy)), z
    return (x, y), float(np.percentile(depth[y - 4:y + 5, x - 4:x + 5], 30))


def flame_texture(name, els):
    """wip/scene3d/<name>_flames.png: the plate with an alpha that keeps
    flame only. A flame is light, not a thing with an edge: its alpha is
    how bright a pixel is (0 at half brightness, 1 at 0.8), inside the
    flame's own sheet and above its wick. The glow the model painted round
    the flame falls below that brightness and stays out."""
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    bgr = cv2.imread(stem + ".png").astype(np.float32) / 255
    body = smooth(0.50, 0.80, (bgr[..., 2] + bgr[..., 1]) / 2)             # red and green: the white core and the orange mantle
    alpha = np.zeros(body.shape, np.float32)
    for el in els:
        if el["kind"] == "flame":
            near = cv2.erode(el["mask"].astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
            a = body * cv2.GaussianBlur(near.astype(np.float32), (0, 0), 1.2)   # close to the flame: not the candle's lit rim
            a[int(el["wick"][1]) + 2:] = 0
            alpha = np.maximum(alpha, a)
    cv2.imwrite(stem + "_flames.png", np.dstack([bgr, alpha]).__mul__(255).astype(np.uint8))
    return stem + "_flames.png"


def bake(name):
    """Meshes, weights, bones and motions of every actor, in world coordinates."""
    els, K, size, flames = layout(name)
    depth, fits = load(name)[0], wheels(name)
    W3 = lambda p: world(K, size, *p).tolist()
    lit = flame_texture(name, els) if any(el["kind"] == "flame" for el in els) else None
    out, meta = {}, []
    for el in els:
        k = el["id"]
        item = dict(id=k, kind=el["kind"], phase=el.get("phase", 0.0))
        if el["kind"] == "spin":
            fit = fits[k]
            V, uv, q, path = wheel(name, el, K, size, fit)
            hub, n = np.array(fit["hub"]), np.array(fit["n"])
            item.update(texture=path, bones=[("spin", hub.tolist(), (hub + 0.1 * n).tolist(), None, {})],
                        turns=el.get("turns", 1), rock=el.get("rock", 0.0))
            out[k + "/w/spin"] = np.ones(len(V), np.float16)
        else:
            V, uv, q, px, py = grid(el, K, size)
            if el["kind"] == "flame":                            # to a candle flame's size, about the wick
                yi, xi = int(el["wick"][1]), int(el["wick"][0])
                w0 = world(K, size, *el["wick"], float(el["z"][yi, xi] + el["rm"][yi, xi]))
                V = w0 + el["scale"] * (V - w0)
            for bone, w in weights(el, px, py).items():
                out[f"{k}/w/{bone}"] = w.astype(np.float16)
            item["bones"] = [(b[0], W3(b[1]), W3(b[2]), b[3], b[4] if len(b) > 4 else {}) for b in el["bones"]]
        out[k + "/V"], out[k + "/uv"], out[k + "/q"] = V.astype(np.float32), uv.astype(np.float32), q.astype(np.int32)
        if el["kind"] == "priest":
            item.update(arms=[dict(tag=a["tag"], sign=a["sign"], deg=a["deg"]) for a in el["arms"]],
                        **{m: el.get(m, 0) for m in ("turn", "nod", "tilt", "sway", "breathe", "robe")})
        elif el["kind"] == "carry":
            item.update(parent=el["parent"])
        elif el["kind"] == "flame":
            item.update(owner=el["owner"], texture=lit)
            if "parent" in el:                                   # on a carried candle: its bones are the priest's
                item.update(parent=el["parent"], names=el["names"])
        elif el["kind"] in ("swing", "cloth"):
            item["deg"] = el["deg"]
        elif el["kind"] == "hover":
            item["rise"] = el["px"] * el["bones"][0][1][2] / (float(K[0, 0]) * size[0])     # plate pixels to metres
        meta.append(item)
    sources = []                                             # smoke: from a carried candle's flame, or a fixed point
    for el in M.MAPS[name]:
        if el["kind"] == "smoke":
            if el.get("of"):
                sources.append(dict(id=el["id"], of=el["of"]))
            else:
                (x, y), z = source(el, flames, depth, float(K[0, 0]) * size[0])
                sources.append(dict(id=el["id"], world=world(K, size, x, y, z).tolist()))
    path = os.path.join(ROOT, "wip", "scene3d", name + "_actors.npz")
    np.savez_compressed(path, meta=json.dumps(meta), sources=json.dumps(sources), **out)
    print("ACTORS_BAKED", path, len(meta), "meshes,", sum(len(out[m["id"] + "/V"]) for m in meta), "vertices")


if __name__ == "__main__":
    bake(sys.argv[1])
