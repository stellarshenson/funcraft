"""Ornament for the armour of the three mechs, drawn plate by plate into the
atlas of src/procession/plating.py. Each plate is drawn in its own plane and
to its own outline, so the ornament lies on the mesh as if it were sculpted
there: a trim follows the plate's real edge, an emblem stands upright.

What a plate gets depends on its size, the radius of the largest circle that
fits in it:

    under R_STEEL    a seam line round it
    from R_STEEL     a band of bare steel round it, with rivets
    from R_GOLD      a raised gold trim with rivets; the field inside is engraved
    from R_DEVICE    some carry an emblem in gold relief; some have a field in two
                     colours, halved or in warning stripes, as a knight's shield has
    from R_GRAND     a cog-tooth border inside the trim, an emblem, a scroll with a motto

Emblems and engraving patterns are the relief pictures of
src/procession/motifs.py. Lettering is drawn here, so that it is spelled
right. A plate and its mirror twin on the other side of the mech get the
same ornament: every choice is made from the plate's size and place, with
the side left out.

Writes to wip/procession/livery/, for src/procession/livery.py:

    <name>_colour.png    sRGB
    <name>_surface.png   red = metal, green = roughness
    <name>_height.png    16 bit: 0.5 is the plate's surface, the whole range is RELIEF metres
    <name>.json          the enamel of each colour class, for the armour outside the atlas

    ../w40k-mechanicum/.venv-moge/bin/python src/procession/ornament.py [atlas battlemaster madcat]
"""
import os, sys, json, hashlib
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PLATING = os.path.join(ROOT, "wip", "procession", "plating")
GEN = os.path.join(ROOT, "wip", "gen")
OUT = os.path.join(ROOT, "wip", "procession", "livery")
PREVIEW = os.path.join(ROOT, "wip", "preview", "procession")
FONT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"

# enamels and metals, linear RGB
RED, BLACK, BONE = (0.20, 0.012, 0.009), (0.012, 0.012, 0.014), (0.44, 0.38, 0.27)
GOLD, STEEL = (0.95, 0.66, 0.24), (0.22, 0.225, 0.235)
# colour class of the paint scheme of src/paint.py -> enamel: one household, each mech led by another of its colours
LIVERY = {"atlas": dict(primary=RED, secondary=BLACK, bone=BONE),
          "madcat": dict(primary=BLACK, secondary=RED, accent=BONE),
          "battlemaster": dict(primary=BONE, secondary=RED),
          "marauder": dict(primary=RED, secondary=BONE, accent=BLACK)}

R_STEEL, R_GOLD, R_DEVICE, R_GRAND = 0.07, 0.18, 0.24, 0.36   # metres: see the table above
DEVICE_SHARE = 0.6                 # share of the plates between R_DEVICE and R_GRAND that carry an emblem
HALVED, STRIPED = 0.16, 0.08       # shares of the plates from R_DEVICE with a halved field, with a striped one
PARTNER = {RED: BONE, BLACK: RED, BONE: RED}   # the second colour of a halved field
STRIPE = 0.09                      # metres: width of one warning stripe
RELIEF = 0.04                      # metres that the height map spans
MARGIN = 6                         # pixels round every chart, as in plating.py
SEAM = 0.006                       # metres: the dark line round a plate
TRIM = 0.14                        # a gold trim's width as a share of the plate's radius ...
TRIM_WIDTH = (0.022, 0.060)        # ... within these limits, metres
TRIM_RISE, RIVET_RISE, EMBLEM_RISE = 0.006, 0.004, 0.016
TOOTH = 0.10                       # metres: length of one tooth of a cog-tooth border
TILE = 1.2                         # metres: side of one repeat of an engraving pattern
ENGRAVE = 0.35                     # how much an engraving darkens and lightens the enamel
ENAMEL_ROUGH = 0.50

EMBLEMS = dict(cogskull=1, laurelskull=1, wingedskull=1, cogaxe=1, chalice=2, fleur=2, hourglass=1, candle=1, seal=1)
GRAND = ["cogskull", "laurelskull", "wingedskull", "cogaxe", "chalice", "hourglass"]
DEVICES = ["fleur", "laurelskull", "candle", "cogskull", "seal", "wingedskull"]
MOTTOES = ["AVE OMNISSIAH", "DEUS IN MACHINA", "OMNISSIAH VULT", "MACHINA VULT", "PRO OMNISSIAH", "MEMORIA AETERNA",
           "SPIRITUS MACHINAE"]


def chance(c, area, salt):
    """A number in 0..1 that is the same for a plate and its mirror twin."""
    key = f"{round(abs(c[0]) * 2)}/{round(c[1] * 2)}/{round(c[2] * 2)}/{round(area * 4)}/{salt}"
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16) / 0xffffffff


def motif(name, seed):
    return np.asarray(Image.open(os.path.join(GEN, f"motif_{name}_{seed}.png")).convert("L"), np.float32) / 255


def emblem(name, seed):
    """An emblem picture as (cover, shade), cut square round its outline.
    Dark places inside the outline stay part of the emblem."""
    lum = motif(name, seed)
    solid = (cv2.GaussianBlur(lum, (0, 0), 1.5) > 0.10).astype(np.uint8)
    cv2.floodFill(solid, None, (0, 0), 2)                         # the background, from a corner
    n, lab, stats, _ = cv2.connectedComponentsWithStats((solid != 2).astype(np.uint8))
    inside = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    ys, xs = np.nonzero(inside)
    cy, cx, half = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2, max(np.ptp(ys), np.ptp(xs)) // 2 + 4
    pad = max(half - min(cy, cx), half - (lum.shape[0] - cy), half - (lum.shape[1] - cx), 0) + 1
    cover = np.pad(cv2.GaussianBlur(inside.astype(np.float32), (0, 0), 1.0), pad)
    cut = np.s_[cy + pad - half:cy + pad + half, cx + pad - half:cx + pad + half]
    return cover[cut], np.pad(lum, pad)[cut]


def tile(name, seed, density):
    """An engraving pattern at the atlas's scale, 0..1 with 0.5 the surface,
    laid beside its mirror images so that it repeats without a seam."""
    side = int(round(TILE * density))
    e = motif(name, seed)
    ys, xs = np.nonzero(e > 0.1)                       # the picture has a black border: cut it off
    e = e[ys.min() + 8:ys.max() - 7, xs.min() + 8:xs.max() - 7]
    e = e - cv2.GaussianBlur(e, (0, 0), 24)            # the pattern alone, without the picture's light and dark areas
    e = cv2.resize(e, (side, side), interpolation=cv2.INTER_AREA)
    e = np.clip(0.5 + e / (4 * e.std()), 0, 1)
    return np.block([[e, e[:, ::-1]], [e[::-1], e[::-1, ::-1]]])


def lettering(text, width, height):
    """`text` in Roman capitals, as large as fits in width x height pixels."""
    f = ImageFont.truetype(FONT, 96)
    box = f.getbbox(text)
    im = Image.new("L", (box[2] - box[0], box[3] - box[1]))
    ImageDraw.Draw(im).text((-box[0], -box[1]), text, font=f, fill=255)
    k = min(width / im.width, height / im.height)
    size = (max(int(im.width * k), 1), max(int(im.height * k), 1))
    return cv2.resize(np.asarray(im, np.float32) / 255, size, interpolation=cv2.INTER_AREA)


class Layers:
    """What is drawn on one plate: colour, metal, roughness, and height in
    metres above the plate's surface."""

    def __init__(self, shape, colour):
        self.col = np.empty((*shape, 3), np.float32)
        self.col[:] = colour
        self.met = np.zeros(shape, np.float32)
        self.rou = np.full(shape, ENAMEL_ROUGH, np.float32)
        self.hei = np.zeros(shape, np.float32)

    def put(self, a, colour, metal, rough, rise=0.0, at=np.s_[:, :]):
        """Lay a material with cover `a` (0..1), raised by `rise`."""
        self.col[at] += a[..., None] * (np.asarray(colour, np.float32) - self.col[at])
        self.met[at] += a * (metal - self.met[at])
        self.rou[at] += a * (rough - self.rou[at])
        self.hei[at] += a * rise

    def window(self, x0, y0, w, h):
        """The part of a w x h rectangle at (x0, y0) that lies on the plate:
        its slice here and its slice in the rectangle, or None."""
        H, W = self.met.shape
        xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
        if xa >= xb or ya >= yb:
            return None
        return np.s_[ya:yb, xa:xb], np.s_[ya - y0:yb - y0, xa - x0:xb - x0]


def rivets(L, region, spacing, r, colour):
    """Domed rivets of radius r pixels along the outline of `region`, evenly spaced."""
    R = int(np.ceil(r)) + 2
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    rho = np.hypot(yy, xx)
    a = np.clip(r - rho + 0.5, 0, 1)
    dome = np.sqrt(np.clip(1 - (rho / r) ** 2, 0, 1))
    shadow = np.clip(r + 2.0 - rho, 0, 1) * (1 - a)
    shaded = np.asarray(colour, np.float32) * (0.5 + 0.65 * dome[..., None])
    for c in cv2.findContours(region.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)[0]:
        p = c[:, 0, :]
        seg = np.hypot(*(np.roll(p, -1, 0) - p).T.astype(np.float32))
        n = int(round(seg.sum() / spacing))
        if n < 3:
            continue
        for x, y in p[np.minimum(np.searchsorted(np.cumsum(seg), (np.arange(n) + 0.5) * seg.sum() / n), len(p) - 1)]:
            win = L.window(x - R, y - R, 2 * R + 1, 2 * R + 1)
            if win:
                at, sub = win
                L.col[at] *= 1 - 0.5 * shadow[sub][..., None]
                L.put(a[sub], shaded[sub], 1.0, 0.30, RIVET_RISE * dome[sub], at)


def along(mask, density):
    """For every pixel, where its nearest point of the plate's outline lies
    along that outline, in metres, and the length of that outline."""
    s, per, zero = np.zeros(mask.shape, np.float32), np.ones(mask.shape, np.float32), np.ones(mask.shape, np.uint8)
    for c in cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)[0]:
        p = c[:, 0, :]
        seg = np.hypot(*(np.roll(p, -1, 0) - p).T.astype(np.float32))
        s[p[:, 1], p[:, 0]] = (np.cumsum(seg) - seg) / density
        per[p[:, 1], p[:, 0]] = max(seg.sum() / density, 1e-3)
        zero[p[:, 1], p[:, 0]] = 0
    lab = cv2.distanceTransformWithLabels(zero, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)[1]
    on = zero == 0
    lut_s, lut_p = np.zeros(lab.max() + 1, np.float32), np.ones(lab.max() + 1, np.float32)
    lut_s[lab[on]], lut_p[lab[on]] = s[on], per[on]
    return lut_s[lab], lut_p[lab]


def stamp(L, em, cx, cy, r, clip):
    """An emblem in gold relief, radius r pixels, centred on (cx, cy)."""
    side = max(int(round(2 * r)), 4)
    win = L.window(int(round(cx - side / 2)), int(round(cy - side / 2)), side, side)
    if win:
        at, sub = win
        a = cv2.resize(em[0], (side, side), interpolation=cv2.INTER_AREA)[sub] * clip[at]
        s = cv2.resize(em[1], (side, side), interpolation=cv2.INTER_AREA)[sub]
        L.put(a, np.asarray(GOLD, np.float32) * (0.16 + s[..., None]), 1.0, 0.34 - 0.12 * s, 0.003 + EMBLEM_RISE * s, at)


def scroll(L, text, cx, cy, hw, hh, clip):
    """A bone scroll with forked ends and black lettering, half-size hw x hh pixels."""
    pts = np.array([(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw - 0.9 * hh, cy), (cx + hw, cy + hh),
                    (cx - hw, cy + hh), (cx - hw + 0.9 * hh, cy)])
    a = np.zeros(L.met.shape, np.uint8)
    cv2.fillPoly(a, [np.round(pts * 16).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=4)
    a = a.astype(np.float32) / 255 * clip
    rim = a - cv2.erode(a, np.ones((3, 3), np.uint8))
    L.put(a, np.asarray(BONE) * 1.25, 0.0, 0.62, 0.003)
    L.col *= 1 - 0.7 * rim[..., None]
    t = lettering(text, 2 * (hw - 1.4 * hh), 1.15 * hh)
    win = L.window(int(round(cx - t.shape[1] / 2)), int(round(cy - t.shape[0] / 2)), t.shape[1], t.shape[0])
    if win:
        at, sub = win
        L.put(t[sub] * a[at], BLACK, 0.0, 0.5, -0.0012, at)


def plate(mask, density, enamel, c, n, area, curved, tiles, emblems):
    """Draw one plate. `mask` is its outline in pixels; returns its Layers."""
    px = 1.0 / density
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5) / density       # metres from the plate's edge
    rin = float(dist.max())
    tone = 0.90 + 0.18 * chance(c, area, "tone")
    L = Layers(mask.shape, np.asarray(enamel) * tone)
    if curved:                                         # its outline is partly a cut, not an edge: engraving only
        rin = min(rin, R_STEEL - 1e-6) if rin < R_GOLD else rin

    def band(a, b):
        return np.clip((dist - a) / px + 0.5, 0, 1) * np.clip((b - dist) / px + 0.5, 0, 1)

    def beyond(a):
        return np.clip((dist - a) / px + 0.5, 0, 1)

    field = SEAM
    black = np.full(mask.shape, float(tuple(enamel) == BLACK), np.float32)    # where the field is black enamel
    plain = 1.0                                        # 0 on a striped field: it takes no engraving and no emblem
    if rin >= R_DEVICE and not curved:
        yy, xx = np.mgrid[:mask.shape[0], :mask.shape[1]].astype(np.float32)
        kind = chance(c, area, "field")
        if kind < HALVED:                              # per pale: the right half in the second colour
            a = np.clip(xx - np.nonzero(mask)[1].mean() + 0.5, 0, 1)
            L.put(a, np.asarray(PARTNER[tuple(enamel)]) * tone, 0.0, ENAMEL_ROUGH)
            black += a * ((PARTNER[tuple(enamel)] == BLACK) - black)
        elif kind < HALVED + STRIPED:                  # warning stripes, black and bone, rising to the right
            ph = (xx + yy) / (STRIPE * density * 2 ** 0.5)
            a = np.clip(np.abs(ph % 2 - 1) * STRIPE * density - STRIPE * density / 2 + 0.5, 0, 1)
            L.put(a, np.asarray(BONE) * tone, 0.0, ENAMEL_ROUGH)
            L.put(1 - a, np.asarray(BLACK), 0.0, ENAMEL_ROUGH)
            plain = 0.0
    if rin >= R_GOLD:
        w = 0.0 if curved else float(np.clip(TRIM * rin, *TRIM_WIDTH))
        field = SEAM + w + 0.008
        grand = rin >= R_GRAND and not curved
        if grand:                                      # the cog-tooth border: two enamels in turn along the outline
            s, per = along(mask, density)
            teeth = np.maximum(2 * np.round(per / (2 * TOOTH)), 2)
            ph = s / per * teeth
            edge = np.minimum(ph % 1, 1 - ph % 1) * per / teeth * density
            odd = np.where(np.floor(ph) % 2 > 0, np.clip(edge + 0.5, 0, 1), 1 - np.clip(edge + 0.5, 0, 1))
            wc = min(0.06, 0.12 * rin)
            a = band(field, field + wc)
            one, two = [k for k in (BLACK, BONE, RED) if k != tuple(enamel)][:2]
            L.put(a * (1 - odd), one, 0.0, 0.45)
            L.put(a * odd, two, 0.0, 0.5, 0.0015)
            L.put(band(field + wc, field + wc + 0.008), GOLD, 1.0, 0.3, 0.002)
            field += wc + 0.014
        # the engraved field: tone on tone on red and bone, gold inlay on black
        T = tiles["filigree" if tuple(enamel) == BLACK or chance(c, area, "tile") > 0.6 else "damask"]
        oy, ox = int(chance(c, area, "oy") * T.shape[0]), int(chance(c, area, "ox") * T.shape[1])
        e = T[(np.arange(mask.shape[0]) + oy) % T.shape[0]][:, (np.arange(mask.shape[1]) + ox) % T.shape[1]]
        a = beyond(field + 0.004) * plain
        L.col *= 1 + (a * (1 - black) * 2 * ENGRAVE * (e - 0.5))[..., None]
        L.rou += a * (1 - black) * 0.25 * (0.5 - e)
        L.hei += a * (1 - black) * 0.004 * (e - 0.5)
        L.put(a * black * np.clip((e - 0.70) / 0.10, 0, 1), np.asarray(GOLD) * 0.9, 1.0, 0.32, 0.001)
        if not curved:                                 # the trim: gold, raised, darker towards its edges
            t = (dist - SEAM) / w
            prof = np.clip(np.minimum(t, 1 - t) * 4, 0, 1)
            prof = prof * prof * (3 - 2 * prof)
            L.put(band(SEAM, SEAM + w), np.asarray(GOLD)[None, None] * (0.5 + 0.5 * prof[..., None]), 1.0, 0.30, TRIM_RISE * prof)
            L.col *= 1 - 0.55 * band(SEAM + w, SEAM + w + 0.005)[..., None]
            rivets(L, dist >= SEAM + w / 2, max(0.10, 2.2 * w) * density, max(0.26 * w * density, 1.6), GOLD)
        device = grand or (rin >= R_DEVICE and not curved and chance(c, area, "device") < DEVICE_SHARE)
        if device and plain:                                     # an emblem where the plate is widest, as near its middle as that allows
            ys, xs = np.nonzero(dist >= 0.94 * dist.max())
            my, mx = np.nonzero(mask)
            k = np.argmin((ys - my.mean()) ** 2 + (xs - mx.mean()) ** 2)
            cy, cx = ys[k], xs[k]
            r = (0.68 if grand else 0.80) * (rin - field) * density
            central = abs(c[0]) < 0.6 and n[1] > 0.3
            pick = GRAND if grand else DEVICES
            em = emblems["cogskull" if central else pick[int(chance(c, area, "emblem") * len(pick)) % len(pick)]]
            stamp(L, em, cx, cy, r, beyond(field))
            if grand:
                scroll(L, MOTTOES[int(chance(c, area, "motto") * len(MOTTOES)) % len(MOTTOES)], cx, cy + 0.88 * r,
                       0.82 * r, 0.13 * r, beyond(field))
    elif rin >= R_STEEL:
        w = float(np.clip(0.18 * rin, 0.012, 0.03))
        L.put(band(SEAM, SEAM + w), STEEL, 1.0, 0.36, 0.0015)
        rivets(L, dist >= SEAM + w / 2, 0.09 * density, max(0.3 * w * density, 1.6), STEEL)
    if not curved:
        a = 1 - beyond(SEAM)
        L.col *= 1 - 0.6 * a[..., None]
        L.hei -= 0.002 * a
    return L


def srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def draw(name):
    d = np.load(os.path.join(PLATING, f"{name}.npz"))
    density, S, M = float(d["density"]), int(d["side"]), MARGIN
    enamels = [LIVERY[name][str(k)] for k in d["classes"]]
    tiles = {t: tile(t, 1, density) for t in ("damask", "filigree")}
    emblems = {e: emblem(e, seed) for e, seed in EMBLEMS.items()}
    colour = np.zeros((S, S, 3), np.float32)
    metal, rough, height = (np.zeros((S, S), np.float32) for _ in range(3))
    order = np.argsort(d["tri_chart"], kind="stable")
    tri, tc = d["tri"][order].astype(np.float64), d["tri_chart"][order]
    count = len(d["area"])
    start, end = np.searchsorted(tc, np.arange(count)), np.searchsorted(tc, np.arange(count), "right")
    for k in range(count):
        (w, h), (ax, ay) = d["size"][k], d["at"][k]
        t = tri[start[k]:end[k]].copy()                # atlas pixels, row 0 at the bottom -> this chart's picture
        t[..., 0] = t[..., 0] - ax + M - 0.5
        t[..., 1] = (ay + h) - t[..., 1] + M - 0.5
        mask = np.zeros((h + 2 * M, w + 2 * M), np.uint8)
        cv2.fillPoly(mask, list(np.round(t * 16).astype(np.int32)), 255, shift=4)
        if not mask.any():
            continue
        L = plate(mask, density, enamels[d["klass"][k]], d["c"][k], d["n"][k], float(d["area"][k]), bool(d["curved"][k]),
                  tiles, emblems)
        # the margin takes the nearest pixel of the plate, so that no neighbour's colour is read at the edge
        lab = cv2.distanceTransformWithLabels(255 - mask, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)[1]
        on = mask > 0
        lut = np.zeros(lab.max() + 1, np.int64)
        lut[lab[on]] = np.flatnonzero(on)
        src = lut[lab]
        at = np.s_[S - ay - h - M:S - ay + M, ax - M:ax + w + M]
        colour[at] = L.col.reshape(-1, 3)[src]
        metal[at], rough[at], height[at] = L.met.ravel()[src], L.rou.ravel()[src], L.hei.ravel()[src]
    os.makedirs(OUT, exist_ok=True)
    rgb = (srgb(colour) * 255 + 0.5).astype(np.uint8)
    cv2.imwrite(os.path.join(OUT, f"{name}_colour.png"), rgb[..., ::-1], [cv2.IMWRITE_PNG_COMPRESSION, 1])
    surface = np.stack([np.zeros_like(metal), rough, metal], -1)                    # cv2 writes blue, green, red
    cv2.imwrite(os.path.join(OUT, f"{name}_surface.png"), (np.clip(surface, 0, 1) * 255 + 0.5).astype(np.uint8),
                [cv2.IMWRITE_PNG_COMPRESSION, 1])
    cv2.imwrite(os.path.join(OUT, f"{name}_height.png"), (np.clip(0.5 + height / RELIEF, 0, 1) * 65535 + 0.5).astype(np.uint16),
                [cv2.IMWRITE_PNG_COMPRESSION, 1])
    json.dump(dict(enamel=LIVERY[name], relief=RELIEF), open(os.path.join(OUT, f"{name}.json"), "w"))
    os.makedirs(PREVIEW, exist_ok=True)
    cv2.imwrite(os.path.join(PREVIEW, f"ornament-{name}.jpg"), cv2.resize(rgb[..., ::-1], (2048, 2048), interpolation=cv2.INTER_AREA))
    print(f"ORNAMENT {name}: {count} plates at {density:.0f} px per metre")


if __name__ == "__main__":
    for name in sys.argv[1:] or list(LIVERY):
        draw(name)
