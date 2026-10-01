"""Motion maps of the plate scenes (src/scenes.py): which elements of a
plate move, and how.

A priest is cut out of the plate into its own rigged mesh (src/actors.py):
the map gives the box and points SAM 2.1 cuts its mask from
(src/segment.py), and the rotations of its bones. A thing a priest carries
is bound to that priest's forearm. A molten stream stays in the plate and
flows: its texture is carried along flow lines, written as one clean plate
per loop frame. Every motion is a whole number of cycles per loop, so
frame 80 equals frame 0.

    python3 src/motion.py map <name>      # wip/preview/motion-<name>.png: masks, skeletons, legend
    python3 src/motion.py flow <name>     # wip/scene3d/<name>_flow/p0001..p0080.png (clean plate, streams flowing)
    python3 src/motion.py proof <name>    # measured motion per element in wip/frames-<name>, head crops
"""
import os, sys, math
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = 80
CYCLE = 20                 # frames per flow cycle of a molten stream: 4 per loop
TAU = 2 * math.pi


def priest(id, who, box, pos, phase, neg=(), head=0.2, **moves):
    """A figure. head: share of the mask's height above the neck. Moves, as
    peak bone rotations in degrees: turn (head left and right), nod (head
    forward and back up), tilt (head to the shoulder), sway (lean from the
    feet); breathe: chest stretch in percent."""
    return dict(kind="priest", id=id, who=who, box=box, pos=pos, neg=neg, phase=phase, head=head, **moves)


def carry(id, who, parent, box, pos, hand, lift=0.0, neg=(), grip=None):
    """A thing `parent` holds, or a free hand: one rigid piece on the
    forearm that ends at plate pixel `hand`; the forearm swings `lift`
    degrees. grip=(box, point): the hand that holds the thing, cut with it,
    so thing and hand move as one."""
    el = dict(kind="carry", id=id, who=who, parent=parent, box=box, pos=pos, neg=neg, hand=hand, lift=lift)
    if grip:
        el["cuts"] = [dict(box=box, pos=pos, neg=neg), dict(box=grip[0], pos=[grip[1]], neg=())]
    return el


def stream(id, who, box, pos, line, speed):
    """Molten metal flowing along `line` at `speed` px per frame."""
    return dict(kind="stream", id=id, who=who, box=box, pos=pos, neg=(), line=line, speed=speed)


MAPS = {
    "foundry": [
        priest("1", "Priest, front left", (55, 446, 220, 766), [(135, 620), (130, 500)], 0.00, turn=10, sway=0.8, breathe=1.2),
        priest("2", "Priest by the crucible", (236, 450, 346, 711), [(290, 590), (292, 490)], 0.30, nod=12, breathe=1.2),
        priest("3", "Priest in the smoke", (925, 440, 984, 578), [(955, 520)], 0.55, turn=12, sway=0.6),
        priest("4", "Priest at the channel, far", (1063, 445, 1134, 613), [(1100, 540)], 0.75, nod=10, tilt=3),
        priest("5", "Priest at the channel, near", (1271, 445, 1375, 684), [(1325, 580), (1322, 480)], 0.15, turn=10, sway=0.8),
        priest("6", "Priest, front right", (1710, 442, 1858, 739), [(1785, 620), (1782, 490)], 0.45, nod=10, turn=8, breathe=1.2),
        stream("7", "Molten pour from the crucible", (535, 269, 627, 492), [(575, 320), (580, 420)],
               [(575, 272), (578, 380), (590, 490)], 4.0),
        stream("8", "Molten spill over the lip", (600, 470, 800, 640), [(680, 520), (730, 580)],
               [(640, 488), (700, 540), (760, 615)], 3.0),
        stream("9", "Molten channel", (640, 570, 1720, 768), [(760, 640), (1000, 680), (1250, 720), (1450, 752)],
               [(680, 610), (1000, 670), (1300, 725), (1720, 778)], 2.5),
    ],
    "choir": [
        priest("1", "Priest, front left", (58, 201, 370, 765), [(215, 480), (215, 265)], 0.00, head=0.26, turn=8, sway=0.8, breathe=1.2),
        carry("1a", "Lamp staff of 1", "1", (70, 40, 170, 765), [(122, 160), (122, 620)], hand=(102, 430),
              grip=((78, 405, 128, 455), (102, 430))),
        carry("1b", "Candle of 1", "1", (300, 285, 378, 440), [(338, 350)], hand=(340, 442), lift=1.5,
              grip=((316, 415, 366, 470), (340, 442))),
        priest("2", "Priest, second row left", (349, 245, 568, 763), [(450, 470), (462, 300)], 0.20, nod=8, turn=10),
        carry("2a", "Candle of 2", "2", (528, 318, 578, 432), [(552, 370)], hand=(549, 430), lift=1.5,
              grip=((530, 410, 568, 450), (549, 430))),
        priest("3", "Priest, front centre left", (550, 142, 992, 764), [(790, 480), (770, 260)], 0.40,
               neg=[(652, 420)], head=0.3, turn=10, tilt=4, sway=0.8),
        carry("3a", "Banner staff of 3", "3", (562, 0, 722, 765), [(645, 90), (655, 520)], hand=(646, 440),
              grip=((610, 404, 682, 482), (646, 440))),
        carry("3b", "Candle of 3", "3", (900, 258, 992, 462), [(950, 330)], hand=(952, 475), lift=1.5,
              grip=((915, 430, 990, 520), (952, 475))),
        priest("4", "Priest, second row centre", (945, 258, 1159, 764), [(1060, 470), (1058, 330)], 0.60, nod=10, breathe=1.2),
        carry("4a", "Candle of 4", "4", (1118, 304, 1167, 422), [(1143, 350)], hand=(1143, 430), lift=1.5,
              grip=((1122, 404, 1164, 454), (1143, 430))),
        priest("5", "Priest, third row", (1172, 256, 1307, 757), [(1235, 450)], 0.80, turn=12, sway=0.6),
        priest("6", "Priest, front centre", (1258, 140, 1700, 763), [(1450, 520), (1475, 270), (1647, 560)], 0.10,
               head=0.3, turn=10, breathe=1.2),
        carry("6h", "Right hand of 6", "6", (1356, 458, 1462, 540), [(1405, 500)], hand=(1405, 500), lift=3),
        carry("6a", "Candle of 6", "6", (1598, 262, 1702, 440), [(1645, 340)], hand=(1645, 462), lift=1.5,
              grip=((1610, 430, 1680, 495), (1645, 462))),
        priest("7", "Priest, second row right", (1695, 194, 1933, 766), [(1810, 470), (1830, 280)], 0.50, nod=10, sway=0.6),
        carry("7a", "Candle of 7", "7", (1903, 268, 1967, 382), [(1938, 320)], hand=(1942, 396), lift=1.5,
              grip=((1922, 370, 1962, 420), (1942, 396))),
        priest("8", "Priest, front right", (1910, 108, 2421, 763), [(2180, 560), (2185, 250)], 0.70,
               head=0.3, turn=8, tilt=4, breathe=1.2),
        carry("8h", "Right hand of 8", "8", (2030, 480, 2140, 565), [(2085, 522)], hand=(2085, 522), lift=3),
        priest("9", "Priest at the right edge", (2294, 209, 2432, 766), [(2395, 330)], 0.30, turn=10, sway=0.6),
        priest("10", "Hood behind candle 3b", (860, 285, 932, 362), [(895, 322)], 0.90, head=1.0, nod=10),
        priest("11", "Hood behind candle 6a", (1535, 255, 1612, 362), [(1572, 300)], 0.25, head=1.0, nod=8, turn=8),
    ],
}


def masks(name):
    seg = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_seg.npz"))
    return {el["id"]: seg[el["id"]] for el in MAPS[name]}


def flow_setup(plate, streams):
    """Per stream: soft mask, flow vectors (px per frame) along its line,
    a per-pixel phase offset, and the plate with stream colours spread
    outward so an upstream look-up never fetches the surroundings."""
    H, W = plate.shape[:2]
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(7)
    for el in streams:
        m = el["mask"].astype(np.float32)
        best, fx, fy = np.full((H, W), np.inf, np.float32), np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
        for (x0, y0), (x1, y1) in zip(el["line"][:-1], el["line"][1:]):
            vx, vy = x1 - x0, y1 - y0
            L = math.hypot(vx, vy)
            s = np.clip(((X - x0) * vx + (Y - y0) * vy) / (L * L), 0, 1)
            d = np.hypot(X - (x0 + s * vx), Y - (y0 + s * vy))
            near = d < best
            best[near], fx[near], fy[near] = d[near], vx / L, vy / L
        g = cv2.GaussianBlur(m, (0, 0), 12) + 1e-6
        fx = cv2.GaussianBlur(fx * m, (0, 0), 12) / g
        fy = cv2.GaussianBlur(fy * m, (0, 0), 12) / g
        n = np.hypot(fx, fy) + 1e-6
        el["F"] = (fx / n * el["speed"], fy / n * el["speed"])
        noise = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 20)
        el["offset"] = (noise - noise.min()) / (noise.max() - noise.min() + 1e-6)
        el["ws"] = cv2.GaussianBlur(cv2.dilate(el["mask"].astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 2)
        fill, done = np.zeros_like(plate), m > 0
        for sg in (6, 20, 60):
            wb = cv2.GaussianBlur(m, (0, 0), sg)
            spread = cv2.GaussianBlur(plate * m[..., None], (0, 0), sg) / (wb[..., None] + 1e-6)
            new = ~done & (wb > 1e-3)
            fill[new], done = spread[new], done | new
        el["src"] = np.where(m[..., None] > 0, plate, fill)


def flow_frame(plate, streams, k):
    """The plate at loop frame k. Each stream is two copies of its texture,
    each carried downstream for CYCLE frames and then reset, half a cycle
    apart, cross-faded so a copy is invisible when it resets."""
    H, W = plate.shape[:2]
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    f32 = lambda a: a.astype(np.float32)
    out = plate.copy()
    for el in streams:
        fx, fy = el["F"]
        col = np.zeros_like(plate)
        for i in (0.0, 0.5):
            p = (k / CYCLE + el["offset"] + i) % 1.0
            tau = (p - 0.5) * CYCLE
            wgt = (1 - np.abs(2 * p - 1))[..., None]
            col += wgt * cv2.remap(el["src"], f32(X - fx * tau), f32(Y - fy * tau), cv2.INTER_CUBIC,
                                   borderMode=cv2.BORDER_REFLECT)
        out = out * (1 - el["ws"][..., None]) + col * el["ws"][..., None]
    return np.clip(out, 0, 255)


def write_flow(name):
    mk = masks(name)
    streams = [dict(el, mask=mk[el["id"]]) for el in MAPS[name] if el["kind"] == "stream"]
    assert streams, f"{name} has no stream"
    plate = cv2.imread(os.path.join(ROOT, "wip", "scene3d", name + "_clean.png"), cv2.IMREAD_COLOR).astype(np.float32)
    flow_setup(plate, streams)
    seq = os.path.join(ROOT, "wip", "scene3d", f"{name}_flow")
    os.makedirs(seq, exist_ok=True)
    for k in range(FRAMES):
        cv2.imwrite(os.path.join(seq, f"p{k + 1:04d}.png"), flow_frame(plate, streams, k).astype(np.uint8),
                    [cv2.IMWRITE_PNG_COMPRESSION, 1])
    print("FLOW_DONE", seq)


COLOURS = [(255, 229, 0), (3, 255, 118), (0, 214, 255), (249, 0, 213), (255, 121, 41), (0, 145, 255),
           (118, 230, 0), (129, 64, 255), (218, 255, 100), (252, 128, 234), (255, 255, 255), (80, 180, 255)]


def describe(el):
    """The element's motion in plain words."""
    if el["kind"] == "stream":
        return f"texture flows along the arrows at {el['speed']:g} px per frame ({el['speed'] * 20:g} px/s)"
    if el["kind"] == "carry":
        s = f"one rigid piece on the forearm of priest {el['parent']}"
        return s + (f", which swings \u00b1{el['lift']:g}\u00b0 to raise and lower it" if el["lift"] else "")
    parts = []
    if el.get("turn"):
        parts.append(f"head turn \u00b1{el['turn']:g}\u00b0")
    if el.get("nod"):
        parts.append(f"head nod {el['nod']:g}\u00b0")
    if el.get("tilt"):
        parts.append(f"head tilt \u00b1{el['tilt']:g}\u00b0")
    if el.get("sway"):
        parts.append(f"body lean \u00b1{el['sway']:g}\u00b0")
    if el.get("breathe"):
        parts.append(f"chest breathes {el['breathe']:g} %")
    return ", ".join(parts) + f"; phase {el['phase']:.2f}"


def arrow(img, a, b, c, both=True):
    """Arrow from a to b with a 14 px head; `both`: heads at both ends."""
    a, b = tuple(int(v) for v in a), tuple(int(v) for v in b)
    tip = 14 / max(math.dist(a, b), 1)
    for u, v in ((a, b), (b, a)) if both else ((a, b),):
        cv2.arrowedLine(img, u, v, (0, 0, 0), 7, cv2.LINE_AA, tipLength=tip)
        cv2.arrowedLine(img, u, v, c, 3, cv2.LINE_AA, tipLength=tip)


def draw_map(name):
    """Each moving element filled in its own colour and outlined, numbered;
    every priest's skeleton in white (joints as dots, the bones that rotate
    ringed in the priest's colour); flow arrows on streams; and a legend."""
    from PIL import Image, ImageDraw, ImageFont
    import actors as A
    plate = cv2.imread(os.path.join(ROOT, "wip", "scene3d", name + ".png"), cv2.IMREAD_COLOR).astype(np.float32)
    H, W = plate.shape[:2]
    els, mk = MAPS[name], masks(name)
    rig = {e["id"]: e for e in A.layout(name)[0]}
    img = plate * 0.55
    colour, n = {}, 0
    for el in els:
        if el["kind"] == "carry":
            colour[el["id"]] = colour[el["parent"]]
        else:
            colour[el["id"]], n = COLOURS[n % len(COLOURS)], n + 1
    yy, xx = np.mgrid[0:H, 0:W]
    for el in els:
        m = mk[el["id"]].astype(np.float32)[..., None]
        if el["kind"] == "carry":                          # hatched: held by the priest of that colour
            m = m * (((xx + yy) // 6) % 2 == 0)[..., None]
        img = img * (1 - 0.45 * m) + np.array(colour[el["id"]], np.float32)[::-1] * 0.45 * m
    img = img.astype(np.uint8)
    for el in els:
        cs, _ = cv2.findContours(mk[el["id"]].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(img, cs, -1, colour[el["id"]][::-1], 2, cv2.LINE_AA)
    tags = []
    pt = lambda j: (int(np.clip(j[0], 0, W - 1)), int(np.clip(j[1], 0, H - 1)))
    for el in els:
        c = colour[el["id"]][::-1]
        ys, xs = np.nonzero(mk[el["id"]])
        if el["kind"] == "priest":
            r = rig[el["id"]]
            J = r["joints"]
            chain = [J["feet"], J["pelvis"], J["chest"], J["neck"], J["top"]]
            bones = list(zip(chain[:-1], chain[1:])) + [s for a in r["arms"] for s in
                                                        ((a["shoulder"], a["elbow"]), (a["elbow"], a["hand"]))]
            for a, b in bones:
                cv2.line(img, pt(a), pt(b), (0, 0, 0), 6, cv2.LINE_AA)
                cv2.line(img, pt(a), pt(b), (255, 255, 255), 2, cv2.LINE_AA)
            moving = [J["neck"]] * bool(el.get("turn") or el.get("nod") or el.get("tilt")) + \
                     [J["feet"]] * bool(el.get("sway")) + [J["chest"]] * bool(el.get("breathe")) + \
                     [a["elbow"] for a in r["arms"] if a["deg"]]
            for a, b in bones:
                for j in (a, b):
                    cv2.circle(img, pt(j), 5, (0, 0, 0), -1, cv2.LINE_AA)
                    cv2.circle(img, pt(j), 3, (255, 255, 255), -1, cv2.LINE_AA)
            for j in moving:
                cv2.circle(img, pt(j), 11, (0, 0, 0), 5, cv2.LINE_AA)
                cv2.circle(img, pt(j), 11, c, 3, cv2.LINE_AA)
            tags.append((el["id"], (J["top"][0], ys.min() - 30), c))
        elif el["kind"] == "carry":
            tags.append((el["id"], (xs.max() + 28, ys.min() + 18), c))
        else:
            for a, b in zip(el["line"][:-1], el["line"][1:]):
                arrow(img, a, b, c, both=False)
            (x0, y0), (x1, y1) = el["line"][:2]
            tags.append((el["id"], (x0 + 0.5 * (x1 - x0) + 34, y0 + 0.5 * (y1 - y0) - 30), c))
    for tid, (x, y), c in tags:
        x, y = int(np.clip(x, 24, W - 24)), int(np.clip(y, 24, H - 24))
        cv2.circle(img, (x, y), 21, (0, 0, 0), -1, cv2.LINE_AA)
        cv2.circle(img, (x, y), 21, c, 3, cv2.LINE_AA)
        fs = 0.75 if len(tid) < 2 else 0.6
        (tw, th), _ = cv2.getTextSize(tid, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
        cv2.putText(img, tid, (x - tw // 2, y + th // 2), cv2.FONT_HERSHEY_SIMPLEX, fs, c, 2, cv2.LINE_AA)
    rows = (len(els) + 1) // 2
    pane = Image.new("RGB", (W, 70 + 38 * rows), (16, 16, 16))
    d = ImageDraw.Draw(pane)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 22)
    fr = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 19)
    d.text((20, 14), f"{name}: moving elements. White lines: bones; ringed joints rotate. Angles are peak bone "
           "rotations; one cycle per 4 s loop. Hatched: carried, bound to the forearm of the priest of that colour.",
           font=fr, fill=(220, 220, 220))
    for i, el in enumerate(els):
        x, y = 20 + (i // rows) * (W // 2), 56 + (i % rows) * 38
        c = colour[el["id"]]
        d.rectangle((x, y + 4, x + 22, y + 26), fill=c)
        d.text((x + 34, y + 2), el["id"], font=fb, fill=c)
        d.text((x + 82, y + 2), el["who"], font=fb, fill=(235, 235, 235))
        d.text((x + 400, y + 4), describe(el), font=fr, fill=(200, 200, 200))
    top = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    out = Image.new("RGB", (W, H + pane.height))
    out.paste(top, (0, 0))
    out.paste(pane, (0, H))
    path = os.path.join(ROOT, "wip", "preview", f"motion-{name}.png")
    out.save(path)
    print("wrote", path)


def proof(name):
    """Measured motion in the rendered frames wip/frames-<name>: optical
    flow (Farneback) from frame 0 to every frame, averaged over a priest's
    head or a carried thing, less the flow of a ring around the element
    (the camera's drift). Reported in GIF pixels: the largest excursion, and
    r, the share of the motion's timing that the commanded bone rotations
    explain. A stream: the mean flow from each frame to the next along its
    line. Also writes the head crops at four loop phases,
    wip/preview/rig-<name>-heads.png."""
    import actors as A
    d = os.path.join(ROOT, "wip", f"frames-{name}")
    full = [cv2.imread(os.path.join(d, f"f{k:03d}.png")) for k in range(FRAMES)]
    h, w = full[0].shape[:2]
    g = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in full]
    flows = [cv2.calcOpticalFlowFarneback(g[0], g[k], None, 0.5, 4, 21, 5, 7, 1.5, 0) for k in range(FRAMES)]
    els = A.layout(name)[0]
    by = {e["id"]: e for e in els}
    small = lambda m: cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
    t = np.arange(FRAMES) / FRAMES
    gif = 1140 / w
    body = lambda e: {"sway": np.sin(TAU * (t + e["phase"])), "breathe": 0.5 * (1 - np.cos(TAU * (t + e["phase"] + 0.1)))}
    print(f"{'id':>4}  {'element':28s} {'part':8s} {'excursion':>10s}  {'r':>5s}  commanded")
    crops = []
    for el in els:
        if el["kind"] == "priest":
            sel = el["mask"] & (np.arange(el["mask"].shape[0])[:, None] < el["joints"]["neck"][1])
            ph = t + el["phase"]
            curves = {"turn": np.sin(TAU * (ph + 0.15)), "nod": 0.5 * (1 - np.cos(TAU * (ph + 0.25))),
                      "tilt": np.sin(TAU * (ph + 0.4)), "sway": np.sin(TAU * ph)}
            cmd = {k: v for k, v in {**curves, **body(el)}.items() if el.get(k)}
            part = "head"
        else:
            sel = el["mask"]
            pa = by[el["parent"]]
            cmd = {"lift": np.sin(TAU * (t + pa["phase"] + 0.2))} if el["lift"] else {}
            cmd.update({"parent " + k: v for k, v in body(pa).items() if pa.get(k)})
            part = "all"
        ms = cv2.erode(small(sel).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        if ms.sum() < 6:
            ms = small(sel)
        sm = small(el["mask"]).astype(np.uint8)
        rg = (cv2.dilate(sm, np.ones((41, 41), np.uint8)) > 0) & ~(cv2.dilate(sm, np.ones((17, 17), np.uint8)) > 0)
        v = np.array([f[ms].mean(0) - f[rg].mean(0) for f in flows])
        v = v - v.mean(0)
        exc = float(np.hypot(v[:, 0], v[:, 1]).max() * 2 * gif)
        A_ = np.stack(list(cmd.values()) + [np.ones(FRAMES)], 1) if cmd else None
        r = float("nan")
        if cmd:                                              # share of the motion explained by the commanded curves
            fit = A_ @ np.linalg.lstsq(A_, v, rcond=None)[0]
            r = float(np.sqrt(max(0.0, 1 - ((v - fit) ** 2).sum() / max((v ** 2).sum(), 1e-9))))
        print(f"{el['id']:>4}  {el['who']:28s} {part:8s} {exc:7.2f} px  {r:5.2f}  "
              + (", ".join(cmd) or "none of its own"))
        if el["kind"] == "priest":
            ys, xs = np.nonzero(small(sel))
            cx, cy, s = int(xs.mean()), int(ys.mean()), int(max(xs.max() - xs.min(), ys.max() - ys.min()) * 0.75 + 12)
            x0, y0 = int(np.clip(cx - s, 0, w - 2 * s)), int(np.clip(cy - s, 0, h - 2 * s))
            row = [cv2.resize(full[k][y0:y0 + 2 * s, x0:x0 + 2 * s], (220, 220), interpolation=cv2.INTER_CUBIC)
                   for k in (0, 20, 40, 60)]
            row = np.concatenate(row, 1)
            cv2.putText(row, f"{el['id']}  frames 0 20 40 60", (6, 20), 0, 0.55, (0, 255, 255), 2)
            crops.append(row)
    mk = masks(name)
    for el in MAPS[name]:
        if el["kind"] != "stream":
            continue
        ms = cv2.erode(small(mk[el["id"]]).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        (x0, y0), (x1, y1) = el["line"][0], el["line"][-1]
        ux, uy = (x1 - x0) / math.hypot(x1 - x0, y1 - y0), (y1 - y0) / math.hypot(x1 - x0, y1 - y0)
        along = [float((f[..., 0][ms] * ux + f[..., 1][ms] * uy).mean()) for f in
                 (cv2.calcOpticalFlowFarneback(g[k], g[k + 1], None, 0.5, 4, 15, 5, 5, 1.1, 0) for k in range(0, FRAMES - 1, 4))]
        print(f"{el['id']:>4}  {el['who']:28s} {'stream':8s} {np.mean(along) * gif:5.2f} px per frame downstream; "
              f"commanded {el['speed'] * 1140 / 2432:.2f}")
    cols = 2 if len(crops) > 6 else 1
    crops += [np.zeros_like(crops[0])] * (-len(crops) % cols)
    sheet = np.concatenate([np.concatenate(crops[i::cols], 0) for i in range(cols)], 1)
    path = os.path.join(ROOT, "wip", "preview", f"rig-{name}-heads.png")
    cv2.imwrite(path, sheet)
    print("wrote", path)


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    {"map": draw_map, "flow": write_flow, "proof": proof}[cmd](name)
